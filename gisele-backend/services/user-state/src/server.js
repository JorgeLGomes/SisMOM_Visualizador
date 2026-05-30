// gisele user-state — Fase 2. Persistencia de modelos, anotacoes, configuracoes.
// Substitui o localStorage do frontend.
import Fastify from 'fastify';
import cors from '@fastify/cors';

const PORT = Number(process.env.PORT ?? 8086);
const VERSION = '0.1.0-skeleton';
const STARTED = Date.now();

const app = Fastify({ logger: true });
await app.register(cors, { origin: true });

app.get('/health', async () => ({
  service: 'user-state', version: VERSION,
  uptime_seconds: Math.round((Date.now() - STARTED) / 10) / 100,
  ready: true
}));

app.get('/v1/state/models', async (_, reply) => reply.code(501).send({
  status: 'not_implemented', hint: 'Fase 2 implementa Prisma + PostgreSQL'
}));

app.post('/v1/state/models', async (_, reply) => reply.code(501).send({
  status: 'not_implemented', hint: 'Fase 2 implementa CRUD de modelos'
}));

app.get('/v1/state/annotations', async (_, reply) => reply.code(501).send({
  status: 'not_implemented', hint: 'Fase 2 implementa anotacoes com PostGIS'
}));

app.post('/v1/state/share', async (_, reply) => reply.code(501).send({
  status: 'not_implemented', hint: 'Fase 2 implementa compartilhamento via token'
}));

try {
  await app.listen({ port: PORT, host: '0.0.0.0' });
} catch (err) {
  app.log.error(err); process.exit(1);
}
