# Análise Arquitetural — PoC Bridge

Data da análise: 2026-04-20

## 1) Leitura estrutural atual

### Estrutura encontrada
- `app/main.py`: bootstrap FastAPI, lifecycle, CORS, rate limit, wiring de routers.
- `app/api/v1/alerts.py`: endpoints legados de texto/foto/cancel preservados.
- `app/api/v1/events.py`: endpoints genéricos de dispatch/cancel com API key.
- `app/services/poc_service.py`: orquestração principal (auth, routing, dispatch, estado).
- `app/services/auth_service.py`: autenticação por API key.
- `app/services/routing_service.py`: resolução de providers por regra JSON.
- `app/services/dispatch_service.py`: execução dos providers.
- `app/services/provider_registry.py`: registro e lifecycle dos providers.
- `app/providers/`: `BaseProvider`, `PoCProvider`, `WhatsAppProvider` mock, `TeamsProvider` mock.
- `app/data/*.json`: persistência/configuração alpha local.

## 2) Compatibilidade preservada

- Endpoints existentes em `/api/v1/alerts` mantidos.
- Fluxo legado reutiliza `PoCService` e regras JSON para roteamento.
- Assinatura MD5 (`app/core/security.py`) preservada e reutilizada pelo `PoCProvider`.

## 3) Observabilidade e operação

- Logging centralizado em `app/core/logging_config.py`.
- Saída em console + arquivo com rotação (`app/logs/poc_bridge.log`).
- Startup/shutdown previsível via lifespan e fechamento de clients/providers.

## 4) Riscos aceitos (alpha)

1. `PoCProvider` vem desabilitado por padrão (`enabled: false`) para subir o ambiente sem dependência externa imediata.
2. Persistência em JSON local (`state.json`) sem lock distribuído; suficiente para alpha single-instance.
3. Sem fila assíncrona/broker nesta etapa para manter simplicidade operacional.

## 5) Próximos passos recomendados

1. Ativar `PoCProvider` em ambiente homologado com endpoints reais.
2. Adicionar testes automatizados de integração para `events/dispatch` e `alerts/photo`.
3. Evoluir rastreabilidade de logs com `request_id` por requisição.
