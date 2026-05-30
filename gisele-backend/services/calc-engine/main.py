"""
gisele calc-engine — Calculadora Algébrica + Temporal no servidor.
Fase 3. Stack: FastAPI + numpy + xarray + numexpr.
"""
import time
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

SERVICE = "calc-engine"
VERSION = "0.1.0-skeleton"
STARTED = time.time()

app = FastAPI(title=SERVICE, version=VERSION,
              description="Calculadora algebrica + temporal. SSE para progresso.")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class AlgebraicRequest(BaseModel):
    expression: str
    layers: dict  # {token: decoded_id}


class TemporalRequest(BaseModel):
    expression: str
    modelId: str
    variavelId: str
    dataRodada: str


@app.get("/health")
def health():
    return {"service": SERVICE, "version": VERSION,
            "uptime_seconds": round(time.time() - STARTED, 2), "ready": True}


@app.post("/v1/calc/algebraic")
def calc_algebraic(req: AlgebraicRequest):
    raise HTTPException(501, "calc-engine skeleton — Fase 3 implementa algebra raster")


@app.post("/v1/calc/temporal")
def calc_temporal(req: TemporalRequest):
    raise HTTPException(501, "calc-engine skeleton — Fase 3 implementa calc temporal")


@app.get("/v1/calc/{job_id}/stream")
def calc_stream(job_id: str):
    raise HTTPException(501, "calc-engine skeleton — SSE de progresso vem na Fase 3")
