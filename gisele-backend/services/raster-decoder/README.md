# raster-decoder

Decodifica GeoTIFF e aplica paletas no servidor. Cache em Redis + MinIO. Em Python (FastAPI + rasterio).

## Endpoints (planejados)

| Método | Path | Status |
|---|---|---|
| `GET`  | `/health` | ✅ skeleton |
| `POST` | `/v1/decoder/decode` | 🚧 Fase 2 |
| `POST` | `/v1/decoder/palette` | 🚧 Fase 2 |
| `GET`  | `/v1/decoder/data/{id}` | 🚧 Fase 2 |

## Run local

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8082
curl http://localhost:8082/health | jq
```

## Status

- [x] Skeleton (health + CORS + OpenAPI)
- [ ] decode + cache Redis
- [ ] paleta byte-idêntica ao frontend
- [ ] streaming de Float32 via `/data/{id}`
- [ ] heurísticas legacy (multi-sentinel NoData, flipY, GTRasterTypeGeoKey)
