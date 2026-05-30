# calc-engine

Calculadora Algebrica + Temporal vetorizada (numpy). SSE para progresso.

## Endpoints

| Método | Path | Status |
|---|---|---|
| GET  | `/health` | skeleton |
| POST | `/v1/calc/algebraic` | Fase 3 |
| POST | `/v1/calc/temporal` | Fase 3 |
| GET  | `/v1/calc/{jobId}/stream` (SSE) | Fase 3 |

Meta de performance: `sum(t1..t72)` no Eta-3km em <= 8 s (hoje ~45 s no browser).
