// gisele gateway — Fase 5 do roadmap.
// Roteia para os servicos downstream: tile-cache, raster-decoder, calc-engine,
// export-service, format-converter, user-state.
import Fastify from 'fastify';
import cors from '@fastify/cors';

const PORT = Number(process.env.PORT ?? 8080);
const VERSION = '0.1.0-skeleton';
const STARTED = Date.now();

const app = Fastify({
  logger: { transport: { target: 'pino-pretty', options: { translateTime: true } } }
});

await app.register(cors, { origin: true });

app.get('/health', async () => ({
  service: 'gateway',
  version: VERSION,
  uptime_seconds: Math.round((Date.now() - STARTED) / 10) / 100,
  ready: true
}));

// Health check agregado dos downstreams (Fase 5 implementa de verdade)
app.get('/v1/health/all', async () => ({
  message: 'gateway skeleton — Fase 5 vai agregar health dos servicos',
  downstreams: ['tile-cache', 'raster-decoder', 'calc-engine',
                'export-service', 'format-converter', 'user-state']
}));

// Proxy reverso skeleton — Fase 5 troca por @fastify/http-proxy
app.all('/v1/tiles/*', async (req, reply) => reply.code(501).send({
  status: 'not_implemented',
  hint: 'gateway skeleton — Fase 5 implementa proxy para tile-cache:8081'
}));

app.all('/v1/decoder/*', async (req, reply) => reply.code(501).send({
  status: 'not_implemented',
  hint: 'gateway skeleton — Fase 5 implementa proxy para raster-decoder:8082'
}));

app.all('/v1/calc/*', async (req, reply) => reply.code(501).send({
  status: 'not_implemented',
  hint: 'gateway skeleton — Fase 5 implementa proxy para calc-engine:8083'
}));

app.all('/v1/export/*', async (req, reply) => reply.code(501).send({
  status: 'not_implemented',
  hint: 'gateway skeleton — Fase 5 implementa proxy para export-service:8084'
}));

app.all('/v1/convert/*', async (req, reply) => reply.code(501).send({
  status: 'not_implemented',
  hint: 'gateway skeleton — Fase 5 implementa proxy para format-converter:8085'
}));

app.all('/v1/state/*', async (req, reply) => reply.code(501).send({
  status: 'not_implemented',
  hint: 'gateway skeleton — Fase 5 implementa proxy para user-state:8086'
}));

try {
  await app.listen({ port: PORT, host: '0.0.0.0' });
  app.log.info(`gateway listening on :${PORT}`);
} catch (err) {
  app.log.error(err);
  process.exit(1);
}
