"""
gisele export-service — exporta dados em multiplos formatos.
Fase 4. Stack: FastAPI + geopandas + fiona.
"""
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

SERVICE = "export-service"
VERSION = "0.1.0-skeleton"
STARTED = time.time()

app = FastAPI(title=SERVICE, version=VERSION,
              description="Exporta raster ou serie temporal para GeoJSON/GeoParquet/NetCDF/Shapefile/CSV.")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class RasterExportRequest(BaseModel):
    decodedId: str
    format: str  # geojson|geoparquet|csv|netcdf|shapefile
    mask: dict | None = None


@app.get("/health")
def health():
    return {"service": SERVICE, "version": VERSION,
            "uptime_seconds": round(time.time() - STARTED, 2), "ready": True}


@app.post("/v1/export/raster")
def export_raster(req: RasterExportRequest):
    raise HTTPException(501, "export-service skeleton — Fase 4 implementa raster->GeoJSON/etc")


@app.post("/v1/export/timeseries")
def export_timeseries():
    raise HTTPException(501, "export-service skeleton — Fase 4 implementa serie temporal export")


@app.get("/v1/export/{job_id}")
def export_status(job_id: str):
    raise HTTPException(501, "export-service skeleton — status de job vem na Fase 4")


@app.get("/v1/export/{job_id}/download")
def export_download(job_id: str):
    raise HTTPException(501, "export-service skeleton — download vem na Fase 4")
