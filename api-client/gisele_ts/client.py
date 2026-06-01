"""
client.py — Cliente HTTP do GISELE Python helper.

Envolve o endpoint POST /v1/timeseries/point com uma interface limpa e
um objeto TimeSeries que oferece dataframe/csv/json/dict.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict, field
from typing import Optional, Union, Sequence
from datetime import datetime

try:
    import requests
except ImportError as e:
    raise ImportError(
        "gisele_ts requer 'requests'. Instale com: pip install requests"
    ) from e


# ───────────────────────── Estruturas ─────────────────────────

@dataclass
class TimeSeriesSample:
    """Uma amostra (passo) da serie temporal."""
    idx: int
    passo_h: int                       # horas de previsao (ex.: 24, 48, ...)
    time_utc: Optional[str] = None     # ISO 8601, validade UTC
    value: Optional[float] = None      # valor amostrado; None se NoData


@dataclass
class TimeSeries:
    """
    Resultado de extracao de serie temporal num ponto.

    samples: lista ordenada por passo_h
    layer_name: nome legivel (modelo + variavel)
    lat/lon: coordenadas
    run_date_utc: ISO da rodada
    elapsed_seconds: tempo do server-side
    fetched/failed: contadores
    """
    samples: list[TimeSeriesSample]
    layer_name: str
    lat: float
    lon: float
    run_date_utc: str
    elapsed_seconds: float = 0.0
    fetched: int = 0
    failed: int = 0
    extra: dict = field(default_factory=dict)

    # ─── Conversoes ───
    def to_dict(self) -> dict:
        return {
            "samples": [asdict(s) for s in self.samples],
            "layer_name": self.layer_name,
            "lat": self.lat, "lon": self.lon,
            "run_date_utc": self.run_date_utc,
            "elapsed_seconds": self.elapsed_seconds,
            "fetched": self.fetched, "failed": self.failed,
            **self.extra,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_csv(self, path: str) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["idx", "passo_h", "time_utc", "lat", "lon", "value"])
            for s in self.samples:
                w.writerow([s.idx, s.passo_h, s.time_utc or "", self.lat, self.lon,
                            "" if s.value is None else s.value])

    def dataframe(self):
        """Retorna pandas.DataFrame (requer pandas instalado)."""
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError("dataframe() requer pandas: pip install pandas") from e
        rows = []
        for s in self.samples:
            rows.append({
                "idx": s.idx, "passo_h": s.passo_h,
                "time_utc": s.time_utc, "value": s.value,
            })
        df = pd.DataFrame(rows)
        if not df.empty and "time_utc" in df.columns:
            df["time_utc"] = pd.to_datetime(df["time_utc"], errors="coerce", utc=True)
        df.attrs["layer_name"] = self.layer_name
        df.attrs["lat"] = self.lat
        df.attrs["lon"] = self.lon
        return df

    # ─── Conveniencias ───
    def __len__(self) -> int:
        return len(self.samples)

    def __iter__(self):
        return iter(self.samples)

    def values(self) -> list[Optional[float]]:
        """Lista de valores (None para NoData)."""
        return [s.value for s in self.samples]

    def valid_count(self) -> int:
        """Numero de amostras com valor != None e finito."""
        from math import isfinite
        return sum(1 for s in self.samples
                   if s.value is not None and isfinite(s.value))


# ───────────────────────── Cliente ─────────────────────────

class GiseleClient:
    """
    Cliente HTTP do GISELE Python helper.

    Por padrao aponta para o helper local (subprocesso do Electron),
    porta 8765 (porta default do helper). Mude com base_url:

        # Local Electron-spawned
        GiseleClient()

        # Standalone (rodando: python server.py --port 8000)
        GiseleClient(base_url="http://127.0.0.1:8000")

        # Remoto
        GiseleClient(base_url="https://gisele.cptec.inpe.br/helper")
    """

    DEFAULT_BASE_URL = "http://127.0.0.1:8765"
    DEFAULT_TIMEOUT = 120.0   # series podem demorar (~48 fetches)

    def __init__(self, base_url: Optional[str] = None,
                 timeout: Optional[float] = None,
                 session: Optional["requests.Session"] = None):
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self.session = session or requests.Session()

    # ─── Health check ───
    def health(self) -> dict:
        """GET /health — verifica se o helper esta ativo."""
        r = self.session.get(f"{self.base_url}/health", timeout=5.0)
        r.raise_for_status()
        return r.json()

    # ─── Time series (endpoint principal) ───
    def timeseries(self, *,
                   modelo: dict, variavel: dict,
                   data_rodada: str,
                   lat: float, lon: float,
                   passo_min: Optional[int] = None,
                   passo_max: Optional[int] = None,
                   nodata_extras: Optional[Sequence[float]] = None,
                   parallel_limit: int = 16) -> TimeSeries:
        """
        Extrai a serie temporal de um modelo+variavel num ponto (lat, lon).

        Args:
            modelo: dict com a config do modelo (use MODELS["Eta_5km"] etc.,
                ou monte: {"nome": "...", "url_path": "...", "file_name": "...",
                "extensao_tif": ".tif", "maxPassos": 120, ...}).
            variavel: dict com a config da variavel:
                {"id": "PREC", "label": "Precipitacao", "prefixo": "PREC",
                 "frequencia": 1, "horizonte": 120, "unidade": "mm/h"}
            data_rodada: rodada do modelo no formato "YYYYMMDDHH" UTC.
            lat, lon: coordenadas do ponto (graus).
            passo_min, passo_max: filtro opcional em HORAS de previsao.
            nodata_extras: valores adicionais a tratar como NoData.
            parallel_limit: maximo de fetches concorrentes (1..32).

        Returns:
            TimeSeries com .samples (lista de TimeSeriesSample).

        Raises:
            requests.HTTPError: se o helper retornar 4xx/5xx.
            requests.ConnectionError: se nao alcancar o helper.
        """
        payload = {
            "modelo": modelo, "variavel": variavel,
            "dataRodada": data_rodada,
            "lat": float(lat), "lon": float(lon),
            "parallel_limit": int(parallel_limit),
        }
        if passo_min is not None:
            payload["passoMin"] = int(passo_min)
        if passo_max is not None:
            payload["passoMax"] = int(passo_max)
        if nodata_extras:
            payload["nodata_extras"] = list(nodata_extras)

        r = self.session.post(f"{self.base_url}/v1/timeseries/point",
                              json=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        samples = [TimeSeriesSample(**s) for s in data.get("samples", [])]
        # samples vem ordenado por idx do server, mas reordena por garantia
        samples.sort(key=lambda s: s.idx)
        return TimeSeries(
            samples=samples,
            layer_name=data.get("layer_name", ""),
            lat=data.get("lat", lat), lon=data.get("lon", lon),
            run_date_utc=data.get("run_date_utc", ""),
            elapsed_seconds=float(data.get("elapsed_seconds", 0.0)),
            fetched=int(data.get("fetched", 0)),
            failed=int(data.get("failed", 0)),
            extra={k: v for k, v in data.items() if k not in {
                "samples", "layer_name", "lat", "lon", "run_date_utc",
                "elapsed_seconds", "fetched", "failed"
            }},
        )

    # ─── Time series → GeoJSON (passo direto, util para QGIS) ───
    def timeseries_geojson(self, *, modelo: dict, variavel: dict,
                           data_rodada: str, lat: float, lon: float,
                           **kwargs) -> dict:
        """POST /v1/timeseries/point/geojson — retorna FeatureCollection."""
        payload = {
            "modelo": modelo, "variavel": variavel,
            "dataRodada": data_rodada, "lat": float(lat), "lon": float(lon),
            **{k: v for k, v in kwargs.items() if v is not None},
        }
        r = self.session.post(f"{self.base_url}/v1/timeseries/point/geojson",
                              json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # ─── Convenience: multi-ponto sequencial (helper ja faz cache de disk) ───
    def timeseries_multi(self, *, modelo: dict, variavel: dict,
                         data_rodada: str,
                         points: Sequence[tuple[float, float]],
                         **kwargs) -> list[TimeSeries]:
        """
        Extrai TS para varios pontos. Sequencial mas reusa o cache de
        disk/decoded do helper — fetches sao deduped automaticamente.
        """
        results = []
        for (lat, lon) in points:
            results.append(self.timeseries(
                modelo=modelo, variavel=variavel,
                data_rodada=data_rodada, lat=lat, lon=lon, **kwargs))
        return results
