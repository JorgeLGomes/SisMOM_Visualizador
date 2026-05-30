# user-state

Persistencia de estado do usuario (modelos, anotacoes, configuracoes). Substitui o localStorage do frontend.

Stack: Node 22 + Fastify + Prisma + PostgreSQL+PostGIS.

## Schema

Ver `prisma/schema.prisma`. 4 tabelas:
- users
- model_configs (com flag shared_with_team)
- annotations
- saved_calcs (resultados da calculadora compartilhaveis)

## Migration

```bash
DATABASE_URL=postgres://gisele:dev@localhost:5432/gisele npm run migrate
```
