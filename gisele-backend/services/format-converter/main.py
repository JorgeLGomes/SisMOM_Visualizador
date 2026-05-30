"""
gisele format-converter — aceita formatos GIS diversos e normaliza para GeoJSON EPSG:4326.
Fase 4. Stack: FastAPI + GDAL + fiona.
"""
import time
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

SERVICE = "format-converter"
VERSION = "0.1.0-skeleton"
STARTED = time.time()

app = FastAPI(title=SERVICE, version=VERSION,
              description="Aceita .shp/.zip/.kml/.gpkg/.geojson; converte para GeoJSON EPSG:4326.")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"service": SERVICE, "version": VERSION,
            "uptime_seconds": round(time.time() - STARTED, 2), "ready": True}


@app.post("/v1/convert/upload")
async def upload(file: UploadFile = File(...)):
    raise HTTPException(501, "format-converter skeleton — Fase 4 implementa GDAL ingest")


@app.post("/v1/convert/reproject")
def reproject():
    raise HTTPException(501, "format-converter skeleton — reprojecao via pyproj vem na Fase 4")


@app.get("/v1/convert/{file_id}/as/geojson")
def as_geojson(file_id: str):
    raise HTTPException(501, "format-converter skeleton — saida normalizada vem na Fase 4")
