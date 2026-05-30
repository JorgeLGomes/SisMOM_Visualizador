# GISELE backend — Makefile com comandos comuns
# Use `make help` para listar.

SHELL := /bin/bash
COMPOSE_LOCAL := docker compose -f docker-compose.local.yml
COMPOSE_PROD  := docker compose -f docker-compose.prod.yml

.PHONY: help up down build logs ps healthcheck clean prod-up prod-down lint test

help:  ## Lista comandos disponiveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Modo Local ───

up:  ## Sobe o backend em modo local (todos os 7 servicos + postgres/redis/minio)
	$(COMPOSE_LOCAL) up -d --build

down:  ## Para tudo
	$(COMPOSE_LOCAL) down

build:  ## Build de todas as imagens locais
	$(COMPOSE_LOCAL) build

logs:  ## Tail dos logs (use SVC=tile-cache para um servico)
	$(COMPOSE_LOCAL) logs -f $(SVC)

ps:  ## Lista containers
	$(COMPOSE_LOCAL) ps

healthcheck:  ## Bate /health em todos os servicos
	@echo "─── gateway ────────────────────"
	@curl -fsS http://localhost:8080/health | jq . || echo "DOWN"
	@echo "─── tile-cache ─────────────────"
	@curl -fsS http://localhost:8081/v1/tiles/health | jq . || echo "DOWN"
	@echo "─── raster-decoder ─────────────"
	@curl -fsS http://localhost:8082/health | jq . || echo "DOWN"
	@echo "─── calc-engine ────────────────"
	@curl -fsS http://localhost:8083/health | jq . || echo "DOWN"
	@echo "─── export-service ─────────────"
	@curl -fsS http://localhost:8084/health | jq . || echo "DOWN"
	@echo "─── format-converter ───────────"
	@curl -fsS http://localhost:8085/health | jq . || echo "DOWN"
	@echo "─── user-state ─────────────────"
	@curl -fsS http://localhost:8086/health | jq . || echo "DOWN"

clean:  ## Para tudo + remove volumes (CUIDADO: apaga dados)
	$(COMPOSE_LOCAL) down -v
	rm -rf data/

# ─── Modo Producao ───

prod-up:  ## Sobe em modo Central (precisa de .env configurado)
	@test -f .env || (echo "ERRO: crie .env baseado em .env.example"; exit 1)
	$(COMPOSE_PROD) --env-file .env up -d

prod-down:
	$(COMPOSE_PROD) down

# ─── Qualidade ───

lint:  ## Lint dos OpenAPI specs (precisa npx)
	@cd openapi && for f in *.yaml; do echo "Linting $$f"; npx -y @redocly/cli@latest lint "$$f"; done

test:  ## Roda os testes de cada servico (a implementar por fase)
	@echo "Tests serão implementados conforme cada fase do roadmap."
	@echo "Fase 1: tile-cache go test ./..."
	@echo "Fase 2: raster-decoder pytest tests/"
	@echo "Fase 3: calc-engine pytest tests/"
