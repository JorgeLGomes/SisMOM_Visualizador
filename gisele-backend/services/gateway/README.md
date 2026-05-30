# gateway

API gateway do GISELE. Stack: Node 22 + Fastify.

Responsabilidades (Fase 5):
- Roteamento por path para os 6 servicos downstream
- Auth JWT (OAuth CPTEC)
- Rate-limit por usuario
- CORS uniforme
- Telemetria OpenTelemetry

## Run local

```bash
npm install
node src/server.js
curl http://localhost:8080/health | jq
```
