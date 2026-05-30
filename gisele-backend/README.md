# GISELE Backend

Microsserviços poliglotas que dão suporte ao frontend GISELE. Detalhes em [BACKEND_PROPOSTA.md](../BACKEND_PROPOSTA.md).

**Status:** Fase 0 — esqueleto de todos os 7 serviços. Endpoints retornam `501 Not Implemented` (`/health` funciona).

## Visão geral

7 serviços:

| Serviço | Stack | Porta | Status |
|---|---|---|---|
| `gateway` | Node 22 + Fastify | 8080 | skeleton |
| `tile-cache` | Go 1.22 | 8081 | skeleton |
| `raster-decoder` | Python + FastAPI + rasterio | 8082 | skeleton |
| `calc-engine` | Python + xarray + numpy | 8083 | skeleton |
| `export-service` | Python + geopandas | 8084 | skeleton |
| `format-converter` | Python + GDAL | 8085 | skeleton |
| `user-state` | Node 22 + Fastify + Prisma | 8086 | skeleton |

Storage layer: PostgreSQL+PostGIS, Redis (cache quente), MinIO (object store).

## Quick start (modo local)

```bash
# Pré-requisitos: Docker Desktop ou Docker Engine + Compose plugin
cd gisele-backend
make up              # builda imagens + sobe todos os containers
make ps              # confirma todos running
make healthcheck     # bate /health em cada serviço
make logs SVC=tile-cache  # tail dos logs de um serviço
make down            # para tudo
```

Endpoints expostos:
- http://localhost:8080 — gateway (frontend deve apontar para aqui)
- http://localhost:9001 — console do MinIO (user: gisele, pass: gisele-dev-only)
- http://localhost:5432 — PostgreSQL (interno; use `docker compose exec postgres psql -U gisele`)

## Quick start (modo produção)

```bash
cp .env.example .env
# edite .env com secrets reais
make prod-up
```

Em produção:
- Frontend acessa via `https://gisele.cptec.inpe.br`
- Reverse proxy (nginx/traefik) termina TLS na frente do gateway
- Auth JWT obrigatória (OAuth CPTEC)
- Replicas: 4 do raster-decoder e calc-engine; 2 do gateway, tile-cache, export-service

## Estrutura

```
gisele-backend/
├── services/                       # 1 pasta por microsserviço
│   ├── gateway/                    # Node + Fastify
│   ├── tile-cache/                 # Go (binário distroless ~12 MB)
│   ├── raster-decoder/             # Python + FastAPI + rasterio
│   ├── calc-engine/                # Python + numpy + xarray
│   ├── export-service/             # Python + geopandas
│   ├── format-converter/           # Python + GDAL
│   └── user-state/                 # Node + Prisma + PostgreSQL
├── openapi/                        # OpenAPI 3.1 specs por serviço
├── docker-compose.local.yml        # Modo local (dev/Electron)
├── docker-compose.prod.yml         # Modo central (servidor CPTEC)
├── .env.example                    # Template de secrets para prod
├── .github/workflows/ci.yml        # CI: lint + build + smoke
├── Makefile                        # Atalhos: up/down/logs/healthcheck
└── README.md
```

## Roadmap de implementação

Detalhamento em [BACKEND_PROPOSTA.md §6 Plano de migração](../BACKEND_PROPOSTA.md).

| Fase | Semanas | Conteúdo |
|---|---|---|
| **0** | 1-2 | ✅ Monorepo + OpenAPI + docker-compose esqueleto |
| **1** | 3-5 | `tile-cache` funcional (proxy + cache + CORS) |
| **2** | 6-9 | `raster-decoder` + `user-state` |
| **3** | 10-12 | `calc-engine` com SSE |
| **4** | 13-15 | `export-service` + `format-converter` |
| **5** | 16-17 | `gateway` + observabilidade (OpenTelemetry/Prometheus) |
| **6** | 18 | Modo Local production-ready + installer + docs |

## Como contribuir

1. **Antes de codar**, abra/atualize a spec OpenAPI em `openapi/{service}.yaml`.
2. Implemente o endpoint no `services/{service}/`.
3. Adicione teste em `services/{service}/tests/`.
4. Garanta que `make up && make healthcheck` continua verde.
5. PR descrevendo qual seção do `BACKEND_PROPOSTA.md` está sendo entregue.

## Princípios

- **Frontend é cliente, não cobaia.** Backend nunca quebra o cliente — sempre há fallback in-browser.
- **API REST primeiro, SSE para progresso.** WebSocket só se houver razão forte.
- **Stateless quando possível.** Estado durável vai pro Postgres; estado quente pro Redis; binários grandes pro MinIO.
- **Mesma imagem em local e prod.** Só muda o `compose.yml`.
- **Observabilidade desde o dia 1.** `/health` em todo serviço; OpenTelemetry instrumentation na Fase 5.

## Suporte

- Frontend: ver [HANDOVER_GISELE.md](../HANDOVER_GISELE.md)
- Especificações originais: ver [ESPECIFICACOES_GISELE.md](../ESPECIFICACOES_GISELE.md)
- Proposta backend: ver [BACKEND_PROPOSTA.md](../BACKEND_PROPOSTA.md)

---

**Build marker / versão dos serviços:** `0.1.0-skeleton` · **Última revisão:** 29/05/2026
