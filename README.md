# PoC Bridge API (Alpha)

Middleware FastAPI entre WebGuardião e iConvNet com arquitetura modular baseada em Providers.

## O que este alpha entrega

- Endpoints legados mantidos:
  - `POST /api/v1/alerts/text`
  - `POST /api/v1/alerts/photo`
  - `POST /api/v1/alerts/cancel`
- Endpoints genéricos novos:
  - `POST /api/v1/events/dispatch`
  - `POST /api/v1/events/cancel`
- Autenticação por API Key para endpoints genéricos.
- Roteamento por regras JSON (`routing_rules.json`).
- Providers:
  - `PoCProvider` (real, configurável)
  - `WhatsAppProvider` (mock)
  - `TeamsProvider` (mock)
- Logging centralizado com console + arquivo rotativo (`app/logs/poc_bridge.log`).

## Estrutura principal

- `app/main.py`: bootstrap FastAPI + wiring.
- `app/api/v1/alerts.py`: compatibilidade com endpoints existentes.
- `app/api/v1/events.py`: dispatch/cancel genéricos.
- `app/services/poc_service.py`: orquestração principal.
- `app/services/auth_service.py`: autenticação API Key.
- `app/services/routing_service.py`: resolução de providers por regras.
- `app/services/dispatch_service.py`: execução de dispatch/cancel.
- `app/services/provider_registry.py`: registro de providers.
- `app/providers/`: implementação dos providers.
- `app/data/*.json`: configuração/persistência do alpha.

## Execução no Ubuntu (venv)

```bash
cd /workspace/PoC-bridge
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000
```

## Configuração JSON (alpha)

Arquivos em `app/data/`:

- `api_keys.json`: chaves e vínculo parceiro.
- `partners.json`: cadastro de parceiros.
- `routing_rules.json`: regras de roteamento por parceiro/tipo de evento.
- `provider_configs.json`: configuração dos providers.
- `state.json`: estado simples de dispatches ativos.

> Para ativar o provider PoC real, altere `provider_configs.json` para `"enabled": true` e configure endpoints/chaves reais.

## Exemplos de teste com curl

### 1) Health

```bash
curl -s http://127.0.0.1:3000/health
```

### 2) Endpoint legado de texto

```bash
curl -s -X POST http://127.0.0.1:3000/api/v1/alerts/text \
  -H "Content-Type: application/json" \
  -d '{"content":"Teste alpha","member":"all","brd_hz":2}'
```

### 3) Dispatch genérico

```bash
curl -s -X POST http://127.0.0.1:3000/api/v1/events/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: alpha-partner-a-key" \
  -d '{
    "partner_id": "partner_a",
    "event_type": "intrusion",
    "payload": {"content": "Evento de intrusão", "member": "all"}
  }'
```

### 4) Cancel genérico

```bash
curl -s -X POST http://127.0.0.1:3000/api/v1/events/cancel \
  -H "Content-Type: application/json" \
  -H "X-API-Key: alpha-partner-a-key" \
  -d '{"dispatch_id":"<UUID-retornado-no-dispatch>"}'
```

## Plano curto de validação manual

1. Subir aplicação no Ubuntu e validar `GET /health`.
2. Testar `alerts/text` e confirmar retorno com `broad_id`/`cache_key`.
3. Testar `events/dispatch` com API key válida/ inválida.
4. Testar `events/cancel` com `dispatch_id` existente e inexistente.
5. Verificar logs em console e em `app/logs/poc_bridge.log`.
6. Simular erro de IO em upload e validar resposta HTTP defensiva.
