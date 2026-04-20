# Plano de Evolução Incremental — PoC Bridge

Data base: 2026-04-20

## Status desta rodada

### Implementado
1. `PoCService` funcional com orquestração de dispatch/cancel e estado em JSON.
2. Arquitetura provider-based mínima:
   - `BaseProvider`
   - `PoCProvider`
   - `WhatsAppProvider` (mock)
   - `TeamsProvider` (mock)
   - `ProviderRegistry`
3. Autenticação por API Key (`AuthService`).
4. Roteamento por JSON (`RoutingService`).
5. Endpoints genéricos:
   - `POST /api/v1/events/dispatch`
   - `POST /api/v1/events/cancel`
6. Logging centralizado e rotativo.
7. Endpoints legados mantidos em `/api/v1/alerts`.

## Próximas etapas curtas

### Etapa 1 — Homologação PoC real
- Ativar provider PoC no `provider_configs.json`.
- Validar assinatura MD5 e payloads contra endpoint real.
- Ajustar mapeamento de resposta para `broad_id` final.

### Etapa 2 — Robustez
- Implementar retry com backoff para `PoCProvider`.
- Criar testes automatizados (smoke + integração).
- Adicionar validações extras de payload por `event_type`.

### Etapa 3 — Operação
- Introduzir `request_id` nos logs.
- Preparar script simples de deploy/restart no Ubuntu.
- Adicionar healthcheck expandido (JSON/data/providers).
