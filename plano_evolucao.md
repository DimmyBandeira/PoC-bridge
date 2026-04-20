# Plano de Evolução Incremental — PoC Bridge

Data base: 2026-04-19

## Objetivo
Evoluir a API para prontidão de produção com baixo risco, preservando funcionamento existente e evitando refatorações amplas.

## Backlog priorizado

### Etapa 0 — Estabilização imediata (P0)
1. Implementar `app/services/poc_service.py` (mínimo funcional):
   - Contrato explícito (`send_text_alert`, `send_photo_alert`, `cancel_broadcast`, `cancel_alert_by_key`, `close`).
   - Timeouts e tratamento de erro de rede.
   - Logs de sucesso/erro com contexto mínimo.
2. Garantir que app sobe sem erros de import/instância.
3. Ajustar documentação de execução (`README.md`) com comando real de start.

**Critério de aceite:** aplicação inicializa e endpoints retornam respostas controladas sem falha estrutural.

### Etapa 1 — Observabilidade e logging (P1)
1. Centralizar configuração de logging em módulo dedicado (`app/core/logging_config.py`).
2. Adicionar handlers:
   - Console (stdout).
   - Arquivo com rotação (`RotatingFileHandler`).
3. Tornar setup idempotente para evitar duplicidade de handlers.
4. Padronizar formato com campos mínimos (timestamp, level, módulo, mensagem, request id quando disponível).

**Critério de aceite:** logs em console+arquivo sem duplicação em reinicialização.

### Etapa 2 — Segurança e robustez de borda (P1)
1. Restringir CORS por ambiente (produção vs desenvolvimento).
2. Validar upload (tipo MIME, tamanho máximo, extensão permitida).
3. Tratar falhas de IO em `storage.py` com logs e erro HTTP coerente.
4. Revisar rate limit por endpoint conforme risco operacional.

**Critério de aceite:** entradas inválidas retornam erros 4xx claros; falhas de IO não derrubam serviço silenciosamente.

### Etapa 3 — Organização arquitetural (P2)
1. Extrair regras de orquestração de `alerts.py` para serviço de aplicação.
2. Definir contratos (DTOs/schemas internos) entre API e serviços.
3. Unificar eventos de lifecycle no `lifespan` (evitar dispersão por router).

**Critério de aceite:** endpoints enxutos, regras de negócio testáveis fora da camada HTTP.

### Etapa 4 — Qualidade contínua (P2)
1. Adicionar suíte mínima de testes:
   - smoke do app
   - integração dos endpoints principais
   - testes de storage (sucesso/falha)
2. Adicionar lint/format/type-check em pipeline.
3. Criar runbook operacional (restart, logs, incidentes).

**Critério de aceite:** pipeline executa checks automáticos com feedback rápido.

---

## Sequência recomendada de execução
1. Etapa 0
2. Etapa 1
3. Etapa 2
4. Etapa 3
5. Etapa 4

## Mudanças aplicadas nesta rodada
- Correção cirúrgica no tratamento de exceções do endpoint de cancelamento para preservar `HTTPException`.
- Criação de documentação de diagnóstico arquitetural e plano incremental.
