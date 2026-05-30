"""
sampler.py — amostragem de raster GeoTIFF para a aceleracao do GISELE.

Mantem a mesma convencao do frontend:
  - bbox: {minX (lonMin), minY (latMin), maxX (lonMax), maxY (latMax)}
  - row j=0 -> topo (latMax) — convencao top-down
  - centro do pixel: lat = latMax - (j+0.5) * dLat
                     lon = lonMin + (i+0.5) * dLon
  - NoData: valor declarado + extras configuraveis
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional

import numpy as np
import rasterio
from rasterio.io import MemoryFile


@dataclass
class DecodedRaster:
    """Match logico do `decoded` do frontend."""
    width: int
    height: int
    data: np.ndarray        # shape (H, W), dtype float32 (sem mascara aplicada)
    bbox: dict              # {minX, minY, maxX, maxY}
    nodata: Optional[float]
    crs: Optional[str]
    dtype: str

    def is_masked(self, v: float, extras: Optional[list[float]] = None) -> bool:
        if not math.isfinite(v):
            return True
        if self.nodata is not None and v == self.nodata:
            return True
        if extras:
            for e in extras:
                if v == e:
                    return True
        return False


def decode_geotiff_bytes(buf: bytes) -> DecodedRaster:
    """Decodifica bytes de um GeoTIFF em DecodedRaster."""
    with MemoryFile(buf) as memfile:
        with memfile.open() as src:
            data = src.read(1).astype(np.float32, copy=False)
            b = src.bounds  # left, bottom, right, top
            return DecodedRaster(
                width=src.width,
                height=src.height,
                data=data,
                bbox={"minX": b.left, "minY": b.bottom, "maxX": b.right, "maxY": b.top},
                nodata=float(src.nodata) if src.nodata is not None else None,
                crs=str(src.crs) if src.crs else None,
                dtype=str(src.dtypes[0]),
            )


def sample_at_latlon(
    decoded: DecodedRaster,
    lat: float,
    lon: float,
    nodata_extras: Optional[list[float]] = None,
) -> Optional[float]:
    """
    Retorna o valor do pixel mais proximo de (lat, lon).
    None se o ponto estiver fora do bbox OU se o pixel for NoData.
    """
    bb = decoded.bbox
    if not (bb["minY"] <= lat <= bb["maxY"]):
        return None
    if not (bb["minX"] <= lon <= bb["maxX"]):
        return None

    W = decoded.width
    H = decoded.height
    d_lat = (bb["maxY"] - bb["minY"]) / H
    d_lon = (bb["maxX"] - bb["minX"]) / W

    # Convencao top-down: j=0 e' a linha do topo (latMax)
    j = int((bb["maxY"] - lat) / d_lat)
    i = int((lon - bb["minX"]) / d_lon)

    j = max(0, min(H - 1, j))
    i = max(0, min(W - 1, i))

    v = float(decoded.data[j, i])
    if decoded.is_masked(v, nodata_extras):
        return None
    return v


def sample_profile_line(
    decoded: DecodedRaster,
    coords: list[tuple[float, float]],
    n_samples: int = 200,
    nodata_extras: Optional[list[float]] = None,
) -> list[dict]:
    """
    Amostra o raster ao longo de uma polilinha (coords = [(lat, lon), ...]).
    Retorna lista de {distance_km, lat, lon, value} com `n_samples` pontos.
    """
    if len(coords) < 2:
        return []

    # Distancia acumulada (Haversine simplificada -> grande circulo)
    R = 6371.0088
    cum = [0.0]
    for k in range(1, len(coords)):
        lat1, lon1 = coords[k - 1]
        lat2, lon2 = coords[k]
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2
             + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        cum.append(cum[-1] + R * c)

    total = cum[-1]
    if total <= 0:
        return []

    samples = []
    for s in range(n_samples):
        d = total * s / max(1, n_samples - 1)
        # Encontra segmento
        seg = 1
        while seg < len(cum) and cum[seg] < d:
            seg += 1
        if seg >= len(cum):
            seg = len(cum) - 1
        seg_len = cum[seg] - cum[seg - 1]
        frac = 0.0 if seg_len <= 0 else (d - cum[seg - 1]) / seg_len
        lat1, lon1 = coords[seg - 1]
        lat2, lon2 = coords[seg]
        lat = lat1 + (lat2 - lat1) * frac
        lon = lon1 + (lon2 - lon1) * frac
        val = sample_at_latlon(decoded, lat, lon, nodata_extras)
        samples.append({"distance_km": round(d, 4), "lat": round(lat, 6),
                        "lon": round(lon, 6), "value": val})
    return samples
