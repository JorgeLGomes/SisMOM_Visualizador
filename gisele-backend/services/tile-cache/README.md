# tile-cache

Proxy + cache do FTP do CPTEC. Em Go.

## Endpoints

- `GET /v1/tiles/health` — status do serviço, métricas.
- `GET /v1/tiles/cptec/{model}/{yyyy}/{mm}/{dd}/{hh}/{kind}/{filename}` — fetch+cache transparente.

## Run local

```bash
go run .
# → :8081
curl http://localhost:8081/v1/tiles/health | jq
```

## Build

```bash
docker build -t gisele/tile-cache:dev .
```

## Status

- [x] Skeleton (health + CORS + logging)
- [ ] Cache RAM (groupcache)
- [ ] Cache disco (MinIO/FS)
- [ ] ETag/Last-Modified upstream
- [ ] Cloud Optimized GeoTIFF conversion opcional
