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
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from url_builder import montarURL, passo_validity_time
from sampler import DecodedRaster, decode_geotiff_bytes, sample_at_latlon, sample_profile_line

import hashlib
import io
import os
import tempfile
import threading
from collections import OrderedDict
from pathlib import Path

VERSION = "0.6.0"
STARTED = time.time()
DEFAULT_PORT = 8765
DEFAULT_PARALLEL = 16  # bumped 8 -> 16 (era saturando CPTEC pouco)

# ─── Instrumentacao de paralelismo (verificavel) ───
# in_flight_workers: quantos workers estao em fetch+decode AGORA
# max_observed: pico historico observado
_inflight_lock = threading.Lock()
_inflight = {"current": 0, "max_observed": 0, "total_started": 0}

def _flight_enter(label: str):
    with _inflight_lock:
        _inflight["current"] += 1
        _inflight["total_started"] += 1
        if _inflight["current"] > _inflight["max_observed"]:
            _inflight["max_observed"] = _inflight["current"]
        cur = _inflight["current"]
        peak = _inflight["max_observed"]
    print(f"[par] +1 ({label}) → in_flight={cur} peak={peak}", flush=True)

def _flight_exit(label: str, elapsed_s: float):
    with _inflight_lock:
        _inflight["current"] -= 1
        cur = _inflight["current"]
    print(f"[par] -1 ({label}, {elapsed_s*1000:.0f}ms) → in_flight={cur}", flush=True)

def _flight_reset_peak():
    with _inflight_lock:
        _inflight["max_observed"] = _inflight["current"]

# ───────────────────────── Cache persistente em disco ─────────────────────────
# Armazena os TIFs baixados em ~/.gisele/tiff-cache/<sha256>.bin
# Quando o cache excede CACHE_MAX_BYTES, faz eviction LRU baseado em atime.

CACHE_DIR = Path(os.environ.get("GISELE_CACHE_DIR",
                                 os.path.expanduser("~/.gisele/tiff-cache")))
CACHE_MAX_BYTES = int(os.environ.get("GISELE_CACHE_MAX_BYTES", str(10 * 1024 ** 3)))  # 10 GB default
_cache_lock = threading.Lock()
_cache_stats = {"hits": 0, "misses": 0, "writes": 0, "evictions": 0}

def _cache_path(url: str) -> Path:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{h}.bin"

def _cache_get(url: str) -> Optional[bytes]:
    p = _cache_path(url)
    if not p.exists():
        with _cache_lock:
            _cache_stats["misses"] += 1
        return None
    try:
        data = p.read_bytes()
        # Atualiza atime para LRU (touch)
        try: os.utime(p, None)
        except OSError: pass
        with _cache_lock:
            _cache_stats["hits"] += 1
        return data
    except OSError:
        return None

def _cache_put(url: str, data: bytes) -> None:
    if not data:
        return
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = _cache_path(url)
    # Atomic write: tmp + rename. Evita arquivo parcial se processo morrer.
    fd, tmp_path = tempfile.mkstemp(dir=str(CACHE_DIR), suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp_path, p)  # atomic em POSIX e Windows (Python 3.3+)
        with _cache_lock:
            _cache_stats["writes"] += 1
    except OSError as e:
        try: os.unlink(tmp_path)
        except OSError: pass
        print(f"[cache] write err: {e}", flush=True)
    # Eviction LRU se passou do limite
    _maybe_evict()

def _maybe_evict() -> None:
    """Se cache total > CACHE_MAX_BYTES, remove arquivos mais antigos por atime."""
    try:
        entries = []
        total = 0
        for p in CACHE_DIR.glob("*.bin"):
            try:
                st = p.stat()
                entries.append((st.st_atime, st.st_size, p))
                total += st.st_size
            except OSError:
                continue
        if total <= CACHE_MAX_BYTES:
            return
        # Ordena por atime crescente (mais antigo primeiro)
        entries.sort(key=lambda e: e[0])
        target = int(CACHE_MAX_BYTES * 0.8)  # libera ate 80% do cap (evita oscilacao)
        with _cache_lock:
            for atime, size, p in entries:
                if total <= target:
                    break
                try:
                    p.unlink()
                    total -= size
                    _cache_stats["evictions"] += 1
                except OSError:
                    continue
    except OSError:
        pass

def _cache_total_bytes() -> int:
    try:
        return sum(p.stat().st_size for p in CACHE_DIR.glob("*.bin"))
    except OSError:
        return 0

# ───────────────────────── In-memory decoded cache (#1) ─────────────────────────
# Cache LRU de DecodedRaster (numpy array + bbox + nodata) na RAM, por URL hash.
# Speedup: segunda amostragem do mesmo TIF pula fetch+decode → ~0.1ms.

DECODED_CACHE_MAX = int(os.environ.get("GISELE_DECODED_CACHE_MAX", "256"))
_decoded_cache: OrderedDict = OrderedDict()    # url_hash -> DecodedRaster
_decoded_cache_lock = threading.Lock()
_decoded_stats = {"hits": 0, "misses": 0, "writes": 0, "evictions": 0}

def _url_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()

def _decoded_get(url: str):
    k = _url_key(url)
    with _decoded_cache_lock:
        if k in _decoded_cache:
            _decoded_cache.move_to_end(k)
            _decoded_stats["hits"] += 1
            return _decoded_cache[k]
        _decoded_stats["misses"] += 1
    return None

def _decoded_put(url: str, decoded):
    k = _url_key(url)
    with _decoded_cache_lock:
        _decoded_cache[k] = decoded
        _decoded_cache.move_to_end(k)
        _decoded_stats["writes"] += 1
        while len(_decoded_cache) > DECODED_CACHE_MAX:
            _decoded_cache.popitem(last=False)
            _decoded_stats["evictions"] += 1

def _decoded_memory_mb() -> float:
    """Estimativa do uso de RAM (assumindo Float32)."""
    total = 0
    with _decoded_cache_lock:
        for d in _decoded_cache.values():
            try: total += d.width * d.height * 4
            except AttributeError: continue
    return round(total / (1024 ** 2), 1)

# ───────────────────────── PNG render endpoint (#4) ─────────────────────────
# matplotlib (Agg backend) para paletas + Pillow para encode PNG.
# Cache de PNGs em RAM por (url, paleta, vmin, vmax, undef).

# Lazy import: so importa quando primeiro usado (matplotlib e pesado)
_mpl_loaded = False
_cm_module = None

def _ensure_mpl():
    global _mpl_loaded, _cm_module
    if _mpl_loaded:
        return
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import cm
    _cm_module = cm
    _mpl_loaded = True

# Mapeamento paleta -> nome do colormap matplotlib (case-insensitive lookup)
_PALETA_TO_CMAP = {
    "viridis": "viridis", "plasma": "plasma", "inferno": "inferno",
    "magma": "magma", "cividis": "cividis", "jet": "jet", "turbo": "turbo",
    "grayscale": "gray", "gray": "gray", "cinza": "gray",
    "rdbu": "RdBu_r", "rdylbu": "RdYlBu_r", "spectral": "Spectral_r",
    "brbg": "BrBG_r", "seismic": "seismic", "coolwarm": "coolwarm",
    "terrain": "terrain", "ocean": "ocean",
}

PNG_CACHE_MAX = int(os.environ.get("GISELE_PNG_CACHE_MAX", "512"))
_png_cache: OrderedDict = OrderedDict()
_png_cache_lock = threading.Lock()
_png_stats = {"hits": 0, "misses": 0, "writes": 0}

def _png_total_bytes() -> int:
    with _png_cache_lock:
        return sum(len(v) for v in _png_cache.values())

def _render_png_from_decoded(decoded, paleta: str,
                              vmin: Optional[float] = None,
                              vmax: Optional[float] = None,
                              undef_extras: Optional[list] = None) -> bytes:
    """Aplica paleta + retorna PNG RGBA. NoData = alpha 0 (transparente)."""
    _ensure_mpl()
    data = decoded.data
    if data.ndim != 2:
        raise ValueError(f"esperado raster 2D, got shape={data.shape}")
    # Auto min/max via percentil 5-95 quando nao especificado
    if vmin is None or vmax is None:
        nd = decoded.nodata
        valid = np.isfinite(data)
        if nd is not None:
            valid &= (data != nd)
        if undef_extras:
            for u in undef_extras: valid &= (data != u)
        if valid.any():
            vd = data[valid]
            if vmin is None: vmin = float(np.percentile(vd, 5))
            if vmax is None: vmax = float(np.percentile(vd, 95))
        else:
            vmin, vmax = 0.0, 1.0
    if vmax <= vmin:
        vmax = vmin + 1e-6
    # Mascara
    mask = ~np.isfinite(data)
    if decoded.nodata is not None: mask |= (data == decoded.nodata)
    if undef_extras:
        for u in undef_extras: mask |= (data == u)
    # Normaliza para [0,1]
    norm = np.clip((data - vmin) / (vmax - vmin), 0.0, 1.0)
    # Paleta
    cmap_name = _PALETA_TO_CMAP.get((paleta or "viridis").lower(), "viridis")
    cmap = _cm_module.get_cmap(cmap_name)
    rgba = (cmap(norm) * 255).astype(np.uint8)  # shape (H, W, 4)
    rgba[mask, 3] = 0  # NoData transparente
    # Encode PNG (Pillow)
    from PIL import Image as PIL_Image
    img = PIL_Image.fromarray(rgba, "RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False, compress_level=3)
    return buf.getvalue()


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
    parallel_limit: int = Field(DEFAULT_PARALLEL, ge=1, le=32,
                                description="Quantas fetches concorrentes")
    passoMin: Optional[int] = Field(None, ge=1,
                                    description="Primeiro passo em HORAS (opcional). Padrao: 1*freq.")
    passoMax: Optional[int] = Field(None, ge=1,
                                    description="Ultimo passo em HORAS (opcional). Padrao: horizonte completo.")


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


class PolygonSample(BaseModel):
    idx: int
    passo_h: int
    time_utc: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    sum: Optional[float] = None
    count: int = 0


class TimeSeriesPolygonRequest(BaseModel):
    """Estatisticas zonais (min/max/media/soma) de poligono(s) ao longo do tempo."""
    modelo: ModelConfig
    variavel: VariavelConfig
    dataRodada: str = Field(..., description="YYYYMMDDHH")
    geometries: list[dict] = Field(...,
        description="Geometrias GeoJSON (Polygon/MultiPolygon), coordenadas [lon,lat]")
    nodata_extras: Optional[list[float]] = None
    parallel_limit: int = Field(DEFAULT_PARALLEL, ge=1, le=32,
                                description="Quantas fetches concorrentes")
    passoMin: Optional[int] = Field(None, ge=1,
                                    description="Primeiro passo em HORAS (opcional).")
    passoMax: Optional[int] = Field(None, ge=1,
                                    description="Ultimo passo em HORAS (opcional).")


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
    parallel_limit: int = DEFAULT_PARALLEL


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
    # 1) Cache hit em disco?
    cached = _cache_get(url)
    if cached is not None:
        return (True, cached, None)
    # 2) Fetch da rede
    try:
        r = await client.get(url, timeout=30.0)
        if r.status_code != 200:
            return (False, None, f"HTTP {r.status_code}")
        content = r.content
        # 3) Persiste pra disk cache (fire-and-forget — nao bloqueia se erro)
        try: _cache_put(url, content)
        except Exception as e: print(f"[cache] put err: {e}", flush=True)
        return (True, content, None)
    except Exception as e:
        return (False, None, str(e))


async def _fetch_and_sample(
    client: httpx.AsyncClient,
    url: str,
    lat: float,
    lon: float,
    nodata_extras: Optional[list[float]],
) -> tuple[Optional[float], Optional[str]]:
    """Baixa o TIF e amostra no ponto. Retorna (value|None, error_msg|None).
    Pre-checa decoded cache em RAM: se hit, pula fetch+decode totalmente.
    """
    # 1) In-memory decoded cache? pula tudo
    cached_decoded = _decoded_get(url)
    if cached_decoded is not None:
        try:
            v = sample_at_latlon(cached_decoded, lat, lon, nodata_extras)
            return (v, None)
        except Exception as e:
            print(f"[decoded-cache] sample err (fallback to refetch): {e}", flush=True)
    # 2) Cache miss: fetch + decode + cache
    ok, content, err = await _fetch_one(client, url)
    if not ok or content is None:
        return (None, err)
    try:
        decoded = decode_geotiff_bytes(content)
        _decoded_put(url, decoded)
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


async def _fetch_decoded(
    client: httpx.AsyncClient, url: str,
) -> tuple[Optional["DecodedRaster"], Optional[str]]:
    """Baixa o TIF e retorna o DecodedRaster (decodificado), reusando os caches.
    Pre-checa o decoded cache em RAM (pula fetch+decode em hit). Diferente de
    _fetch_and_sample, devolve o raster inteiro para reducoes zonais."""
    cached = _decoded_get(url)
    if cached is not None:
        return (cached, None)
    ok, content, err = await _fetch_one(client, url)
    if not ok or content is None:
        return (None, err)
    try:
        decoded = decode_geotiff_bytes(content)
        _decoded_put(url, decoded)
        return (decoded, None)
    except Exception as e:
        return (None, f"decode_err: {e}")


def _zonal_mask(width: int, height: int, bbox: dict, geometries: list) -> "np.ndarray":
    """Rasteriza geometrias GeoJSON em uma mascara booleana (H,W) na grade do raster.
    Convencao top-down identica ao sampler: centro do pixel
      lat = maxY - (j+0.5)*dLat ; lon = minX + (i+0.5)*dLon.
    Buracos (aneis internos do Polygon) sao subtraidos; multiplos poligonos/partes
    sao unidos. Usa matplotlib.path (mesma dependencia ja carregada p/ paletas)."""
    import numpy as np
    _ensure_mpl()
    from matplotlib.path import Path as _MplPath
    W = int(width); H = int(height)
    minX = float(bbox["minX"]); minY = float(bbox["minY"])
    maxX = float(bbox["maxX"]); maxY = float(bbox["maxY"])
    d_lon = (maxX - minX) / W
    d_lat = (maxY - minY) / H
    lon_c = minX + (np.arange(W) + 0.5) * d_lon          # (W,)
    lat_c = maxY - (np.arange(H) + 0.5) * d_lat          # (H,) top-down
    LON, LAT = np.meshgrid(lon_c, lat_c)                 # (H,W)
    pts = np.column_stack([LON.ravel(), LAT.ravel()])    # (H*W, 2) -> [lon,lat]
    mask = np.zeros(H * W, dtype=bool)

    def _parts(geom):
        if not isinstance(geom, dict):
            return []
        t = geom.get("type"); c = geom.get("coordinates")
        if not c:
            return []
        if t == "Polygon":
            return [c]                                   # uma parte: [outer, hole...]
        if t == "MultiPolygon":
            return list(c)                               # varias partes
        return []

    for geom in (geometries or []):
        for part in _parts(geom):
            if not part or not part[0]:
                continue
            try:
                outer = _MplPath(np.asarray(part[0], dtype=float)[:, :2])
            except Exception:
                continue
            inside = outer.contains_points(pts)
            for hole in part[1:]:
                if not hole:
                    continue
                try:
                    inside &= ~_MplPath(np.asarray(hole, dtype=float)[:, :2]).contains_points(pts)
                except Exception:
                    pass
            mask |= inside
    return mask.reshape(H, W)


def _zonal_stats(decoded: "DecodedRaster", mask: "np.ndarray",
                 nodata_extras: Optional[list[float]]) -> Optional[dict]:
    """Reduz as celulas dentro da mascara (min/max/media/soma/contagem), excluindo
    NoData com a mesma regra de is_masked (nao-finito, == nodata, == extras)."""
    import numpy as np
    arr = decoded.data                                   # (H,W) float32
    if getattr(arr, "shape", None) != mask.shape:
        return None                                      # grade incompativel
    sel = mask & np.isfinite(arr)
    nd = getattr(decoded, "nodata", None)
    if nd is not None:
        sel &= (arr != nd)
    if nodata_extras:
        for e in nodata_extras:
            try:
                sel &= (arr != float(e))
            except (TypeError, ValueError):
                pass
    vals = arr[sel]
    n = int(vals.size)
    if n == 0:
        return {"min": None, "max": None, "mean": None, "sum": None, "count": 0}
    return {
        "min": float(np.min(vals)),
        "max": float(np.max(vals)),
        "mean": float(np.mean(vals)),
        "sum": float(np.sum(vals)),
        "count": n,
    }


# ───────────────────────── Endpoints ─────────────────────────

@app.get("/health")
def health():
    cache_total = _cache_total_bytes()
    return {
        "service": "gisele-python-helper",
        "version": VERSION,
        "uptime_seconds": round(time.time() - STARTED, 2),
        "ready": True,
        "cache": {
            "dir": str(CACHE_DIR),
            "size_bytes": cache_total,
            "size_mb": round(cache_total / (1024 ** 2), 1),
            "max_bytes": CACHE_MAX_BYTES,
            "hits": _cache_stats["hits"],
            "misses": _cache_stats["misses"],
            "writes": _cache_stats["writes"],
            "evictions": _cache_stats["evictions"],
            "hit_rate": round(_cache_stats["hits"] / max(1, _cache_stats["hits"] + _cache_stats["misses"]), 3),
        },
        "default_parallel": DEFAULT_PARALLEL,
        "parallelism": {
            "in_flight_now": _inflight["current"],
            "peak_observed": _inflight["max_observed"],
            "total_workers_started": _inflight["total_started"],
        },
        "prefetch": {
            "queued": _prefetch_stats["queued"],
            "completed": _prefetch_stats["completed"],
            "failed": _prefetch_stats["failed"],
            "in_progress": _prefetch_stats["in_progress"],
        },
        "decoded_cache": {
            "entries": len(_decoded_cache),
            "max": DECODED_CACHE_MAX,
            "memory_mb": _decoded_memory_mb(),
            "hits": _decoded_stats["hits"],
            "misses": _decoded_stats["misses"],
            "hit_rate": round(_decoded_stats["hits"] / max(1, _decoded_stats["hits"] + _decoded_stats["misses"]), 3),
            "evictions": _decoded_stats["evictions"],
        },
        "png_cache": {
            "entries": len(_png_cache),
            "max": PNG_CACHE_MAX,
            "size_kb": round(_png_total_bytes() / 1024, 1),
            "hits": _png_stats["hits"],
            "misses": _png_stats["misses"],
            "hit_rate": round(_png_stats["hits"] / max(1, _png_stats["hits"] + _png_stats["misses"]), 3),
        },
    }
@app.post("/cache/clear")
def cache_clear():
    """Limpa o cache em disco — util para liberar espaco ou reiniciar do zero."""
    removed = 0
    try:
        for p in CACHE_DIR.glob("*.bin"):
            try: p.unlink(); removed += 1
            except OSError: pass
        with _cache_lock:
            for k in _cache_stats: _cache_stats[k] = 0
    except OSError as e:
        raise HTTPException(500, f"cache clear err: {e}")
    return {"removed": removed, "ok": True}


@app.post("/v1/timeseries/point")
async def timeseries_point(req: TimeSeriesPointRequest):
    """Extracao temporal de um ponto.
    Fetch paralelo via asyncio.gather + Semaphore + httpx.AsyncClient compartilhado
    (connection pooling). Aceita range passoMin/passoMax em horas.
    """
    t0 = time.time()
    m = req.modelo.model_dump()
    v = req.variavel.model_dump()
    freq = max(1, int(v.get("frequencia") or 1))

    steps = _resolve_steps(freq, v.get("horizonte"), m.get("maxPassos", 24))
    if not steps:
        raise HTTPException(400, f"frequencia/horizonte invalidos (freq={freq}, hor={v.get('horizonte')})")

    # Filtra steps pelo intervalo (passoMin/passoMax em horas)
    if req.passoMin is not None:
        steps = [s for s in steps if s >= req.passoMin]
    if req.passoMax is not None:
        steps = [s for s in steps if s <= req.passoMax]
    if not steps:
        raise HTTPException(400,
            f"intervalo de=({req.passoMin}h) ate=({req.passoMax}h) nao cobre nenhum passo (freq={freq}h)")

    # Constroi URLs
    urls = []
    for passo_h in steps:
        url = montarURL(
            modelo_cfg=m, variavel_cfg=v,
            dataRodada=req.dataRodada, passo_h=passo_h, freq=freq, use_tif=True,
        )
        urls.append((passo_h, url))

    # Fetch + sample em paralelo (semaforo + client unico compartilhado)
    sem = asyncio.Semaphore(req.parallel_limit)
    samples: list[TimeSeriesSample] = []
    fetched = 0
    failed = 0

    # Connection pool unico — reuso de TCP/TLS entre workers
    # Limits aumentado: ate parallel_limit conexoes simultaneas
    limits = httpx.Limits(
        max_keepalive_connections=req.parallel_limit,
        max_connections=req.parallel_limit + 4,
    )
    async with httpx.AsyncClient(follow_redirects=True, limits=limits,
                                   http2=True,
                                   timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        async def worker(idx: int, passo_h: int, url: str):
            nonlocal fetched, failed
            async with sem:
                _flight_enter(f"t={passo_h}h")
                w_t0 = time.time()
                v_val, err = await _fetch_and_sample(client, url, req.lat, req.lon, req.nodata_extras)
                _flight_exit(f"t={passo_h}h", time.time() - w_t0)
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

        _flight_reset_peak()  # reset para medir esse request especifico
        await asyncio.gather(*(worker(i + 1, ph, u) for i, (ph, u) in enumerate(urls)))
    samples.sort(key=lambda s: s.idx)
    peak_observed = _inflight["max_observed"]
    print(f"[par] timeseries_point: {len(urls)} fetches, peak_concurrent={peak_observed}, "
          f"elapsed={time.time() - t0:.2f}s", flush=True)

    run_dt = datetime(
        int(req.dataRodada[0:4]), int(req.dataRodada[4:6]),
        int(req.dataRodada[6:8]), int(req.dataRodada[8:10]),
        tzinfo=timezone.utc,
    )
    resp_obj = {
        "samples": samples,
        "layer_name": f"{m.get('nome') or 'modelo'} · {v.get('label') or v.get('id') or 'variavel'}",
        "lat": req.lat, "lon": req.lon,
        "run_date_utc": run_dt.isoformat(),
        "elapsed_seconds": round(time.time() - t0, 3),
        "fetched": fetched, "failed": failed,
        "max_concurrent_observed": peak_observed,
        "parallel_limit_used": req.parallel_limit,
    }
    return resp_obj


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


@app.post("/v1/timeseries/polygon")
async def timeseries_polygon(req: TimeSeriesPolygonRequest):
    """Estatisticas zonais (min/max/media/soma) de poligono(s) ao longo do tempo.

    Espelha /v1/timeseries/point: fetch paralelo (asyncio.gather + Semaphore +
    httpx.AsyncClient compartilhado). A mascara de celulas do poligono e rasterizada
    UMA vez por grade (reusada em todos os passos) e as reducoes sao numpy vetorizado —
    bem mais eficiente que o caminho ponto-a-ponto do cliente para poligonos grandes.
    """
    t0 = time.time()
    if not req.geometries:
        raise HTTPException(400, "geometries vazio")
    m = req.modelo.model_dump()
    v = req.variavel.model_dump()
    freq = max(1, int(v.get("frequencia") or 1))

    steps = _resolve_steps(freq, v.get("horizonte"), m.get("maxPassos", 24))
    if not steps:
        raise HTTPException(400, f"frequencia/horizonte invalidos (freq={freq}, hor={v.get('horizonte')})")

    if req.passoMin is not None:
        steps = [s for s in steps if s >= req.passoMin]
    if req.passoMax is not None:
        steps = [s for s in steps if s <= req.passoMax]
    if not steps:
        raise HTTPException(400,
            f"intervalo de=({req.passoMin}h) ate=({req.passoMax}h) nao cobre nenhum passo (freq={freq}h)")

    urls = []
    for passo_h in steps:
        url = montarURL(
            modelo_cfg=m, variavel_cfg=v,
            dataRodada=req.dataRodada, passo_h=passo_h, freq=freq, use_tif=True,
        )
        urls.append((passo_h, url))

    sem = asyncio.Semaphore(req.parallel_limit)
    samples: list[PolygonSample] = []
    fetched = 0
    failed = 0
    _mask_cache: dict = {}
    _mask_lock = asyncio.Lock()
    _EMPTY = {"min": None, "max": None, "mean": None, "sum": None, "count": 0}

    async def _get_mask(decoded):
        b = decoded.bbox
        key = f"{decoded.width}x{decoded.height}|{b['minX']},{b['minY']},{b['maxX']},{b['maxY']}"
        # Calcula a mascara uma unica vez por grade (serializado p/ evitar recomputo).
        async with _mask_lock:
            mk = _mask_cache.get(key)
            if mk is None:
                mk = await asyncio.to_thread(_zonal_mask, decoded.width, decoded.height, b, req.geometries)
                _mask_cache[key] = mk
            return mk

    limits = httpx.Limits(
        max_keepalive_connections=req.parallel_limit,
        max_connections=req.parallel_limit + 4,
    )
    async with httpx.AsyncClient(follow_redirects=True, limits=limits,
                                   http2=True,
                                   timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        async def worker(idx: int, passo_h: int, url: str):
            nonlocal fetched, failed
            stats = None
            err = None
            async with sem:
                _flight_enter(f"poly t={passo_h}h")
                w_t0 = time.time()
                decoded, err = await _fetch_decoded(client, url)
                if decoded is not None:
                    try:
                        mk = await _get_mask(decoded)
                        stats = await asyncio.to_thread(_zonal_stats, decoded, mk, req.nodata_extras)
                    except Exception as e:
                        err = f"zonal_err: {e}"
                _flight_exit(f"poly t={passo_h}h", time.time() - w_t0)
            if err or stats is None:
                failed += 1
                stats = _EMPTY
            else:
                fetched += 1
            valid = passo_validity_time(req.dataRodada, passo_h)
            samples.append(PolygonSample(
                idx=idx, passo_h=passo_h,
                time_utc=valid.replace(tzinfo=timezone.utc).isoformat(),
                min=stats["min"], max=stats["max"], mean=stats["mean"],
                sum=stats["sum"], count=stats["count"],
            ))

        _flight_reset_peak()
        await asyncio.gather(*(worker(i + 1, ph, u) for i, (ph, u) in enumerate(urls)))
    samples.sort(key=lambda s: s.idx)
    peak_observed = _inflight["max_observed"]
    print(f"[par] timeseries_polygon: {len(urls)} fetches, peak_concurrent={peak_observed}, "
          f"elapsed={time.time() - t0:.2f}s", flush=True)

    run_dt = datetime(
        int(req.dataRodada[0:4]), int(req.dataRodada[4:6]),
        int(req.dataRodada[6:8]), int(req.dataRodada[8:10]),
        tzinfo=timezone.utc,
    )
    return {
        "samples": samples,
        "layer_name": f"{m.get('nome') or 'modelo'} · {v.get('label') or v.get('id') or 'variavel'}",
        "run_date_utc": run_dt.isoformat(),
        "elapsed_seconds": round(time.time() - t0, 3),
        "fetched": fetched, "failed": failed,
        "max_concurrent_observed": peak_observed,
        "parallel_limit_used": req.parallel_limit,
        "polygon_count": len(req.geometries),
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


# ───────────────────────── Tile proxy + prefetch (cache para animacao) ─────────────────────────

# Cliente httpx compartilhado para proxy de tiles — reaproveita conexao HTTP/2
_tile_client: Optional[httpx.AsyncClient] = None
_tile_client_lock = asyncio.Lock()
_prefetch_stats = {"queued": 0, "completed": 0, "failed": 0, "in_progress": 0}

async def _get_tile_client() -> httpx.AsyncClient:
    """Lazy init de httpx.AsyncClient compartilhado entre os endpoints de tile."""
    global _tile_client
    if _tile_client is None or _tile_client.is_closed:
        async with _tile_client_lock:
            if _tile_client is None or _tile_client.is_closed:
                _tile_client = httpx.AsyncClient(
                    follow_redirects=True,
                    http2=True,
                    limits=httpx.Limits(max_keepalive_connections=32, max_connections=32),
                    timeout=httpx.Timeout(30.0, connect=10.0),
                )
    return _tile_client

@app.get("/v1/tile/fetch")
async def tile_fetch(url: str):
    """Proxy de TIF/PNG com cache em disco.

    Browser chama: fetch('http://127.0.0.1:8765/v1/tile/fetch?url=' + encodeURIComponent(url))
      - Cache hit  ~5-10ms (read do disco + send via loopback)
      - Cache miss ~ tempo do FTP + ~10ms overhead (salva no cache)

    Vantagens para animacao:
      - Segundo passe pela mesma rodada e instantaneo
      - Resolve CORS (helper esta em 127.0.0.1, allow_origins=*)
      - Reduz pressao no FTP do CPTEC (1 fetch por arquivo por host)
    """
    # 1) Cache hit?
    cached = _cache_get(url)
    if cached is not None:
        # Heuristica de Content-Type pela extensao
        ext = url.lower().rsplit('.', 1)[-1] if '.' in url else ''
        mime = {
            'tif': 'image/tiff', 'tiff': 'image/tiff',
            'png': 'image/png', 'gif': 'image/gif', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
        }.get(ext, 'application/octet-stream')
        return Response(content=cached, media_type=mime,
                       headers={"X-Gisele-Cache": "HIT", "Cache-Control": "public, max-age=86400"})
    # 2) Fetch do FTP
    client = await _get_tile_client()
    try:
        r = await client.get(url)
    except Exception as e:
        raise HTTPException(502, f"upstream err: {e}")
    if r.status_code != 200:
        raise HTTPException(r.status_code, f"upstream HTTP {r.status_code}")
    content = r.content
    # 3) Persist
    try: _cache_put(url, content)
    except Exception as e: print(f"[cache] tile put err: {e}", flush=True)
    return Response(
        content=content,
        media_type=r.headers.get("content-type") or "application/octet-stream",
        headers={"X-Gisele-Cache": "MISS", "Cache-Control": "public, max-age=86400"}
    )

class TilePrefetchRequest(BaseModel):
    urls: list[str] = Field(..., description="Lista de URLs para baixar em background")
    concurrency: int = Field(8, ge=1, le=32, description="Cap de fetches paralelos")

@app.post("/v1/tile/prefetch")
async def tile_prefetch(req: TilePrefetchRequest):
    """Fire-and-forget: enfileira fetches em background, retorna imediatamente.

    Util para warm-up antes de uma animacao:
      - Frontend manda lista de URLs dos passos da rodada
      - Helper baixa em paralelo e popula cache
      - Quando a animacao chega a cada passo, ja esta em cache (hit instantaneo)

    Pula URLs ja em cache (nao baixa de novo).
    """
    # Filtra ja em cache
    to_fetch = [u for u in req.urls if not _cache_path(u).exists()]
    skipped = len(req.urls) - len(to_fetch)
    if not to_fetch:
        return {"queued": 0, "skipped_already_cached": skipped, "ok": True}

    asyncio.create_task(_do_prefetch(to_fetch, req.concurrency))
    return {
        "queued": len(to_fetch),
        "skipped_already_cached": skipped,
        "concurrency": req.concurrency,
        "ok": True,
        "note": "Fire-and-forget — use GET /health para acompanhar stats.prefetch"
    }

async def _do_prefetch(urls: list[str], concurrency: int):
    """Worker pool de prefetch."""
    sem = asyncio.Semaphore(concurrency)
    _prefetch_stats["queued"] += len(urls)
    client = await _get_tile_client()

    async def worker(url: str):
        async with sem:
            _prefetch_stats["in_progress"] += 1
            try:
                # Skip se ja existe no cache (race-condition window)
                if _cache_path(url).exists():
                    _prefetch_stats["completed"] += 1
                    return
                _flight_enter(f"prefetch")
                t0 = time.time()
                try:
                    r = await client.get(url)
                    if r.status_code == 200:
                        _cache_put(url, r.content)
                        _prefetch_stats["completed"] += 1
                    else:
                        _prefetch_stats["failed"] += 1
                except Exception:
                    _prefetch_stats["failed"] += 1
                finally:
                    _flight_exit("prefetch", time.time() - t0)
            finally:
                _prefetch_stats["in_progress"] -= 1

    await asyncio.gather(*(worker(u) for u in urls), return_exceptions=True)
    print(f"[prefetch] done: {_prefetch_stats['completed']}/{len(urls)+_prefetch_stats['queued']-len(urls)} "
          f"failed={_prefetch_stats['failed']}", flush=True)

@app.get("/v1/tile/cache/check")
async def tile_cache_check(url: str):
    """Confere rapido se uma URL ja esta em cache (sem baixar)."""
    return {"cached": _cache_path(url).exists()}

class TileCacheCheckBatchRequest(BaseModel):
    urls: list[str]

@app.post("/v1/tile/cache/check_batch")
async def tile_cache_check_batch(req: TileCacheCheckBatchRequest):
    """Batch check — confere lista de URLs de uma vez."""
    cached = [u for u in req.urls if _cache_path(u).exists()]
    return {
        "total": len(req.urls),
        "cached": len(cached),
        "missing": len(req.urls) - len(cached),
        "cached_urls": cached
    }


# ───────────────────────── PNG render endpoint (#4) ─────────────────────────

@app.get("/v1/render/png")
async def render_png(
    url: str,
    paleta: str = "viridis",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    undef: Optional[str] = None,
):
    """Aplica paleta server-side e retorna PNG RGBA.

    Pipeline:
      1. PNG cache hit? -> retorna bytes do cache (~0.1ms)
      2. Decoded cache hit? -> aplica paleta + encode + cache PNG
      3. Disk cache hit? -> decode + decoded cache + paleta + PNG cache
      4. Miss completo? -> fetch FTP + tudo acima

    Vantagens vs TIF cru:
      - Tamanho 10-20x menor (200KB vs 4MB)
      - Browser decoda PNG nativamente em hardware (~3ms vs ~30ms TIF parse)
      - Pixels NoData = alpha 0 (transparente) corretamente
    """
    # Cache key inclui params da paleta
    key_str = f"{url}|{(paleta or '').lower()}|{vmin}|{vmax}|{undef or ''}"
    key = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
    with _png_cache_lock:
        cached_png = _png_cache.get(key)
        if cached_png is not None:
            _png_cache.move_to_end(key)
            _png_stats["hits"] += 1
            return Response(cached_png, media_type="image/png",
                           headers={"X-Gisele-PNG-Cache": "HIT",
                                    "Cache-Control": "public, max-age=86400"})
        _png_stats["misses"] += 1
    # Decoded cache hit? aplica paleta direto
    decoded = _decoded_get(url)
    if decoded is None:
        # Tem TIF cru em disco? decode
        cached_bytes = _cache_get(url)
        if cached_bytes is None:
            # Fetch do FTP via client compartilhado
            client = await _get_tile_client()
            try:
                r = await client.get(url)
            except Exception as e:
                raise HTTPException(502, f"upstream err: {e}")
            if r.status_code != 200:
                raise HTTPException(r.status_code, f"upstream HTTP {r.status_code}")
            cached_bytes = r.content
            try: _cache_put(url, cached_bytes)
            except Exception as e: print(f"[cache] put err: {e}", flush=True)
        try:
            decoded = decode_geotiff_bytes(cached_bytes)
            _decoded_put(url, decoded)
        except Exception as e:
            raise HTTPException(500, f"decode err: {e}")
    # Parse undef extras (CSV string)
    undef_extras = None
    if undef:
        try:
            undef_extras = [float(x.strip()) for x in undef.split(",") if x.strip()]
        except ValueError:
            undef_extras = None
    # Render PNG
    try:
        png_bytes = _render_png_from_decoded(decoded, paleta, vmin, vmax, undef_extras)
    except Exception as e:
        raise HTTPException(500, f"render err: {e}")
    # Cache em RAM
    with _png_cache_lock:
        _png_cache[key] = png_bytes
        _png_cache.move_to_end(key)
        _png_stats["writes"] += 1
        while len(_png_cache) > PNG_CACHE_MAX:
            _png_cache.popitem(last=False)
    return Response(png_bytes, media_type="image/png",
                   headers={"X-Gisele-PNG-Cache": "MISS",
                            "Cache-Control": "public, max-age=86400"})


# ───────────────────────── Diagnostico de paralelismo ─────────────────────────

class ParallelTestRequest(BaseModel):
    n_tasks: int = Field(20, ge=1, le=200,
                          description="Quantas tarefas sinteticas disparar em paralelo")
    sleep_ms: int = Field(500, ge=10, le=10000,
                          description="Quanto tempo cada tarefa dorme (simula fetch)")
    concurrency: int = Field(16, ge=1, le=64,
                              description="Cap de concorrencia (Semaphore)")

@app.post("/v1/diagnostics/parallel")
async def diagnostics_parallel(req: ParallelTestRequest):
    """Teste sintetico de paralelismo — dispara N tarefas que dormem por
    sleep_ms cada, limitadas a concurrency simultaneas.

    Se VERDADEIRAMENTE paralelo: tempo total = ceil(N/concurrency) * sleep_ms
    Se sequencial: tempo total = N * sleep_ms

    Exemplo: 20 tarefas x 500ms com concurrency=16 deve levar ~1000ms
    (16 tarefas no primeiro batch + 4 no segundo). Se levar 10000ms,
    nao esta paralelo.
    """
    _flight_reset_peak()
    t0 = time.time()
    sem = asyncio.Semaphore(req.concurrency)
    timeline = []  # (start_offset_ms, end_offset_ms, task_id)

    async def task(i: int):
        async with sem:
            _flight_enter(f"task#{i}")
            start = time.time()
            await asyncio.sleep(req.sleep_ms / 1000.0)
            elapsed = time.time() - start
            _flight_exit(f"task#{i}", elapsed)
            timeline.append({
                "task_id": i,
                "start_ms": round((start - t0) * 1000, 1),
                "end_ms": round((start + elapsed - t0) * 1000, 1),
                "duration_ms": round(elapsed * 1000, 1),
            })

    await asyncio.gather(*(task(i) for i in range(req.n_tasks)))
    total_ms = (time.time() - t0) * 1000
    expected_sequential_ms = req.n_tasks * req.sleep_ms
    expected_parallel_ms = ((req.n_tasks + req.concurrency - 1) // req.concurrency) * req.sleep_ms
    peak = _inflight["max_observed"]
    speedup = expected_sequential_ms / total_ms if total_ms > 0 else 0
    return {
        "n_tasks": req.n_tasks,
        "sleep_ms_each": req.sleep_ms,
        "concurrency_cap": req.concurrency,
        "max_concurrent_observed": peak,
        "is_parallel": peak >= 2,
        "total_elapsed_ms": round(total_ms, 1),
        "expected_if_sequential_ms": expected_sequential_ms,
        "expected_if_parallel_ms": expected_parallel_ms,
        "speedup_over_sequential": round(speedup, 2),
        "interpretation": (
            f"PARALELO confirmado (peak={peak} > 1, speedup={speedup:.1f}x)"
            if peak >= 2 and speedup > 1.5
            else "SEQUENCIAL/quase (peak baixo, speedup ~1x)"
        ),
        "timeline_sample": sorted(timeline, key=lambda x: x["start_ms"])[:10],
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
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
