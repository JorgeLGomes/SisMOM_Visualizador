"""
gisele-python-helper — servidor local que acelera as operacoes pesadas do GISELE.

Roda como subprocess do Electron. Acessivel em http://localhost:8765 (porta configuravel).

Endpoints:
  GET  /health                          — status
  POST /v1/timeseries/point             — extracao temporal num ponto (fetch paralelo + sample)
  POST /v1/timeseries/point/geojson     — idem, saida GeoJSON FeatureCollection
  POST /v1/calc/temporal                — calculadora temporal: sum/mean/max/min(t_i..t_j) ou expressao
  POST /v1/profile/line                 — perfil ao longo de polilinha sobre 1 TIF

Filosofia:
  - Frontend e' a fonte da verdade. Envia model_config + variavel_config em cada request.
  - Backend NAO armazena estado (cache de TIFs em RAM apenas, opcional).
  - Compatibilidade com frontend: mesma convencao top-down, mesmo formato de bbox.
"""
import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from url_builder import montarURL, passo_validity_time
from sampler import DecodedRaster, decode_geotiff_bytes, sample_at_latlon, sample_profile_line

VERSION = "0.1.0"
STARTED = time.time()
DEFAULT_PORT = 8765

app = FastAPI(
    title="gisele-python-helper",
    version=VERSION,
    description="Aceleracao local em Python para operacoes pesadas do GISELE.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ───────────────────────── Schemas ─────────────────────────

class ModelConfig(BaseModel):
    """Config minima de modelo que o frontend manda."""
    nome: Optional[str] = None
    url_path: str = ""
    file_name: str = ""
    url_path_tif: Optional[str] = None
    file_name_tif: Optional[str] = None
    same_url_for_tif: bool = False
    same_name_for_tif: bool = False
    extensao: str = ".png"
    extensao_tif: str = ".tif"
    escopo1: Optional[str] = ""
    escopo2: Optional[str] = ""
    maxPassos: int = 24


class VariavelConfig(BaseModel):
    id: Optional[str] = None
    label: Optional[str] = None
    prefixo: str = ""
    frequencia: int = 1
    horizonte: Optional[int] = None
    unidade: Optional[str] = ""


class TimeSeriesPointRequest(BaseModel):
    modelo: ModelConfig
    variavel: VariavelConfig
    dataRodada: str = Field(..., description="YYYYMMDDHH")
    lat: float
    lon: float
    nodata_extras: Optional[list[float]] = None
    parallel_limit: int = Field(8, ge=1, le=32,
                                description="Quantas fetches concorrentes")


class TimeSeriesSample(BaseModel):
    idx: int
    passo_h: int
    time_utc: Optional[str] = None
    value: Optional[float] = None


class TimeSeriesPointResponse(BaseModel):
    samples: list[TimeSeriesSample]
    layer_name: str
    lat: float
    lon: float
    run_date_utc: str
    elapsed_seconds: float
    fetched: int
    failed: int


class ProfileLineRequest(BaseModel):
    tif_url: str = Field(..., description="URL absoluta do TIF a amostrar")
    coords: list[tuple[float, float]] = Field(..., description="Polilinha [(lat,lon), ...]")
    n_samples: int = 200
    nodata_extras: Optional[list[float]] = None


class TemporalCalcRequest(BaseModel):
    modelo: ModelConfig
    variavel: VariavelConfig
    dataRodada: str
    indices: list[int] = Field(..., description="Indices de passo a fetchar (t1..tN -> [1,...,N])")
    reduction: str = Field("sum", description="sum | mean | max | min | count")
    bbox_filter: Optional[dict] = Field(None,
        description="Opcional: {minX,minY,maxX,maxY} para recortar (so retorna stats no bbox)")
    nodata_extras: Optional[list[float]] = None
    parallel_limit: int = 8


class TemporalCalcResponse(BaseModel):
    width: int
    height: int
    bbox: dict
    nodata_sentinel: float
    min: float
    max: float
    elapsed_seconds: float
    fetched: int
    failed: int
    # Resultado serializado como PNG base64 (paleta aplicada no FRONTEND para byte-identidade)
    # ou nuvem de pontos JSON sumarizada
    data_b64: str = Field(..., description="Float32 raw bytes base64-encoded (little-endian)")


# ───────────────────────── Helpers ─────────────────────────

async def _fetch_one(client: httpx.AsyncClient, url: str) -> tuple[bool, Optional[bytes], Optional[str]]:
    try:
        r = await client.get(url, timeout=30.0)
        if r.status_code != 200:
            return (False, None, f"HTTP {r.status_code}")
        return (True, r.content, None)
    except Exception as e:
        return (False, None, str(e))


async def _fetch_and_sample(
    client: httpx.AsyncClient,
    url: str,
    lat: float,
    lon: float,
    nodata_extras: Optional[list[float]],
) -> tuple[Optional[float], Optional[str]]:
    """Baixa o TIF e amostra no ponto. Retorna (value|None, error_msg|None)."""
    ok, content, err = await _fetch_one(client, url)
    if not ok or content is None:
        return (None, err)
    try:
        decoded = decode_geotiff_bytes(content)
        v = sample_at_latlon(decoded, lat, lon, nodata_extras)
        return (v, None)
    except Exception as e:
        return (None, f"decode_err: {e}")


def _resolve_steps(freq: int, horizonte: Optional[int], max_passos: int) -> list[int]:
    """Retorna lista de passos_h validos (= idx * freq, idx=1..fileMax)."""
    if freq <= 0:
        return []
    horizon = max(freq, horizonte or max_passos or 24)
    file_max = horizon // freq
    return [i * freq for i in range(1, file_max + 1)]


# ───────────────────────── Endpoints ─────────────────────────

@app.get("/health")
def health():
    return {
        "service": "gisele-python-helper",
        "version": VERSION,
        "uptime_seconds": round(time.time() - STARTED, 2),
        "ready": True,
    }


@app.post("/v1/timeseries/point", response_model=TimeSeriesPointResponse)
async def timeseries_point(req: TimeSeriesPointRequest):
    """Extracao temporal de um ponto, com fetch paralelo de N TIFs."""
    t0 = time.time()
    m = req.modelo.model_dump()
    v = req.variavel.model_dump()
    freq = max(1, int(v.get("frequencia") or 1))

    steps = _resolve_steps(freq, v.get("horizonte"), m.get("maxPassos", 24))
    if not steps:
        raise HTTPException(400, f"frequencia/horizonte invalidos (freq={freq}, hor={v.get('horizonte')})")

    # Constroi URLs
    urls = []
    for passo_h in steps:
        url = montarURL(
            modelo_cfg=m, variavel_cfg=v,
            dataRodada=req.dataRodada, passo_h=passo_h, freq=freq, use_tif=True,
        )
        urls.append((passo_h, url))

    # Fetch + sample em paralelo (com semaforo)
    sem = asyncio.Semaphore(req.parallel_limit)
    samples: list[TimeSeriesSample] = []
    fetched = 0
    failed = 0

    async def worker(idx: int, passo_h: int, url: str):
        nonlocal fetched, failed
        async with sem:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                v_val, err = await _fetch_and_sample(client, url, req.lat, req.lon, req.nodata_extras)
        if err:
            failed += 1
        else:
            fetched += 1
        valid = passo_validity_time(req.dataRodada, passo_h)
        samples.append(TimeSeriesSample(
            idx=idx, passo_h=passo_h,
            time_utc=valid.replace(tzinfo=timezone.utc).isoformat(),
            value=v_val,
        ))

    await asyncio.gather(*(worker(i + 1, ph, u) for i, (ph, u) in enumerate(urls)))
    samples.sort(key=lambda s: s.idx)

    run_dt = datetime(
        int(req.dataRodada[0:4]), int(req.dataRodada[4:6]),
        int(req.dataRodada[6:8]), int(req.dataRodada[8:10]),
        tzinfo=timezone.utc,
    )
    return TimeSeriesPointResponse(
        samples=samples,
        layer_name=f"{m.get('nome') or 'modelo'} · {v.get('label') or v.get('id') or 'variavel'}",
        lat=req.lat, lon=req.lon,
        run_date_utc=run_dt.isoformat(),
        elapsed_seconds=round(time.time() - t0, 3),
        fetched=fetched, failed=failed,
    )


@app.post("/v1/timeseries/point/geojson")
async def timeseries_point_geojson(req: TimeSeriesPointRequest):
    """Idem ao /v1/timeseries/point, mas serializa como FeatureCollection GeoJSON."""
    ts = await timeseries_point(req)
    features = []
    for s in ts.samples:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(req.lon, 6), round(req.lat, 6)]},
            "properties": {
                "idx": s.idx,
                "passo_h": s.passo_h,
                "time_utc": s.time_utc,
                "value": s.value,
            },
        })
    return {
        "type": "FeatureCollection",
        "metadata": {
            "generator": "gisele-python-helper",
            "kind": "time-series",
            "layer": ts.layer_name,
            "lat": req.lat, "lon": req.lon,
            "runDate": ts.run_date_utc,
            "exportedAt": datetime.now(timezone.utc).isoformat(),
            "fetched": ts.fetched, "failed": ts.failed,
            "elapsed_seconds": ts.elapsed_seconds,
        },
        "features": features,
    }


@app.post("/v1/calc/temporal", response_model=TemporalCalcResponse)
async def calc_temporal(req: TemporalCalcRequest):
    """Calculadora temporal: reduz N rasters via sum/mean/max/min/count."""
    import base64
    t0 = time.time()
    m = req.modelo.model_dump()
    v = req.variavel.model_dump()
    freq = max(1, int(v.get("frequencia") or 1))

    if req.reduction not in {"sum", "mean", "max", "min", "count"}:
        raise HTTPException(400, f"reduction invalido: {req.reduction}")
    if not req.indices:
        raise HTTPException(400, "indices vazio")

    sem = asyncio.Semaphore(req.parallel_limit)
    rasters: list[Optional[DecodedRaster]] = [None] * len(req.indices)

    async def worker(slot: int, idx: int):
        passo_h = idx * freq
        url = montarURL(modelo_cfg=m, variavel_cfg=v,
                        dataRodada=req.dataRodada, passo_h=passo_h,
                        freq=freq, use_tif=True)
        async with sem:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                ok, content, _ = await _fetch_one(client, url)
        if ok and content:
            try:
                rasters[slot] = decode_geotiff_bytes(content)
            except Exception:
                rasters[slot] = None

    await asyncio.gather(*(worker(i, idx) for i, idx in enumerate(req.indices)))
    valid = [r for r in rasters if r is not None]
    if not valid:
        raise HTTPException(502, "nenhum TIF baixado com sucesso")
    fetched = len(valid)
    failed = len(rasters) - fetched

    # Empilha + reducao com mascara NoData
    ref = valid[0]
    H, W = ref.height, ref.width
    stack = np.full((len(valid), H, W), np.nan, dtype=np.float32)
    for i, r in enumerate(valid):
        if r.height != H or r.width != W:
            raise HTTPException(500, "rasters com dimensoes diferentes")
        d = r.data.astype(np.float32, copy=False)
        mask = ~np.isfinite(d)
        if r.nodata is not None:
            mask |= (d == r.nodata)
        if req.nodata_extras:
            for nd in req.nodata_extras:
                mask |= (d == nd)
        d = np.where(mask, np.nan, d)
        stack[i] = d

    if req.reduction == "sum":
        out = np.nansum(stack, axis=0)
        mask_all_nan = np.all(np.isnan(stack), axis=0)
        out[mask_all_nan] = np.nan
    elif req.reduction == "mean":
        out = np.nanmean(stack, axis=0)
    elif req.reduction == "max":
        out = np.nanmax(stack, axis=0)
    elif req.reduction == "min":
        out = np.nanmin(stack, axis=0)
    else:  # count
        out = np.sum(~np.isnan(stack), axis=0).astype(np.float32)

    ND = -9999.0
    out = np.where(np.isnan(out), ND, out).astype(np.float32, copy=False)
    valid_pixels = out[out != ND]
    mn = float(valid_pixels.min()) if valid_pixels.size else 0.0
    mx = float(valid_pixels.max()) if valid_pixels.size else 1.0

    data_b64 = base64.b64encode(out.tobytes()).decode("ascii")

    return TemporalCalcResponse(
        width=W, height=H, bbox=ref.bbox,
        nodata_sentinel=ND, min=mn, max=mx,
        elapsed_seconds=round(time.time() - t0, 3),
        fetched=fetched, failed=failed,
        data_b64=data_b64,
    )


@app.post("/v1/profile/line")
async def profile_line(req: ProfileLineRequest):
    """Perfil ao longo de polilinha sobre 1 TIF (fetch + decode + sample N pontos)."""
    t0 = time.time()
    async with httpx.AsyncClient(follow_redirects=True) as client:
        ok, content, err = await _fetch_one(client, req.tif_url)
    if not ok or content is None:
        raise HTTPException(502, f"falha ao baixar TIF: {err}")
    try:
        decoded = decode_geotiff_bytes(content)
    except Exception as e:
        raise HTTPException(500, f"falha no decode: {e}")
    samples = sample_profile_line(decoded, req.coords, req.n_samples, req.nodata_extras)
    return {
        "samples": samples,
        "elapsed_seconds": round(time.time() - t0, 3),
        "tif": {
            "width": decoded.width, "height": decoded.height,
            "bbox": decoded.bbox, "nodata": decoded.nodata,
        },
    }


# ───────────────────────── Entrypoint ─────────────────────────

def main():
    parser = argparse.ArgumentParser(description="gisele-python-helper")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    print(json.dumps({
        "msg": "gisele-python-helper starting",
        "version": VERSION,
        "host": args.host,
        "port": args.port,
    }), flush=True)

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
