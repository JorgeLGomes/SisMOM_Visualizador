"""
gisele raster-decoder — decodifica GeoTIFF + aplica paleta.
Fase 2 do roadmap. Stack: FastAPI + rasterio + numpy + pillow.
"""
import time
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

SERVICE = "raster-decoder"
VERSION = "0.1.0-skeleton"
STARTED = time.time()

app = FastAPI(title=SERVICE, version=VERSION,
              description="Decodifica GeoTIFFs e aplica paletas. Cache em Redis + MinIO.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class DecodeRequest(BaseModel):
    url: str = Field(..., description="URL absoluta do GeoTIFF (geralmente do tile-cache)")


class DecodeResponse(BaseModel):
    id: str
    width: int
    height: int
    bbox: dict
    nodata: Optional[float] = None
    dtype: str
    min: float
    max: float
    percentiles: dict
    dataUrl: str


class PaletteRequest(BaseModel):
    id: str
    paleta: str = "viridis"
    min: Optional[float] = None
    max: Optional[float] = None
    nodataExtras: Optional[list] = None
    clipBelow: Optional[float] = None
    clipAbove: Optional[float] = None


@app.get("/health")
def health():
    return {
        "service": SERVICE,
        "version": VERSION,
        "uptime_seconds": round(time.time() - STARTED, 2),
        "ready": True,
    }


@app.post("/v1/decoder/decode", response_model=DecodeResponse)
def decode(req: DecodeRequest):
    # SKELETON — Fase 2 implementará:
    #   1) sha256 da URL → check Redis
    #   2) on miss: GET via tile-cache, rasterio.open(BytesIO(...))
    #   3) ler banda 1 como Float32Array
    #   4) heurísticas legacy: multi-sentinel NoData, auto flipY, GTRasterTypeGeoKey
    #   5) store em MinIO; metadados em Redis
    raise HTTPException(status_code=501,
                        detail="raster-decoder skeleton — Fase 2 implementa o decode")


@app.post("/v1/decoder/palette")
def palette(req: PaletteRequest):
    raise HTTPException(status_code=501,
                        detail="raster-decoder skeleton — paleta vem na Fase 2")


@app.get("/v1/decoder/data/{decoded_id}")
def get_data(decoded_id: str):
    raise HTTPException(status_code=501,
                        detail="raster-decoder skeleton — streaming de Float32 vem na Fase 2")
