# Análise Arquitetural — PoC Bridge

Data da análise: 2026-04-19

## 1) Leitura estrutural do sistema

### Estrutura encontrada
- `app/main.py`: entrypoint FastAPI, CORS, rate limit global, lifespan, rota de health.
- `app/api/v1/alerts.py`: endpoints `/text`, `/photo`, `/cancel` e shutdown hook.
- `app/services/storage.py`: criação de diretório e persistência de upload em disco.
- `app/services/poc_service.py`: **arquivo vazio** (serviço crítico ausente).
- `app/core/security.py`: geração de assinatura (MD5 em 2 etapas) e timestamp.
- `README.md` e `ARQUITETURA.md`: documentação incompleta.
- `requirements.txt` (raiz): vazio; `app/requirements.txt` possui dependências.

### Responsabilidades por módulo (estado atual)
- **API e orquestração parcialmente acopladas** em `alerts.py`.
- **Bootstrap e configuração** misturados em `main.py`.
- **Infra de storage** em módulo dedicado (`storage.py`) — ponto positivo.
- **Serviço de domínio/integrador externo ausente** (`poc_service.py` vazio).

---

## 2) Avaliação de logging

### Achados
- Existe configuração básica central em `main.py` via `logging.basicConfig(...)`.
- Módulos usam `logging.getLogger(__name__)` em `main.py` e `alerts.py`.
- Não foram encontrados `print` em código de runtime.
- `logger.exception(...)` já é utilizado em erros de endpoint (bom para stacktrace).

### Lacunas
- Não há estratégia de arquivo + rotação (somente configuração simples, sem handlers explícitos).
- `basicConfig` pode não ser suficiente em execução multiprocessada (ex.: gunicorn/uvicorn workers).
- Não existe correlação de contexto (request_id, origem, etc.).
- Falta padronização de estrutura de logs (campos mínimos para produção).

---

## 3) Avaliação arquitetural

### Pontos fortes
- Estrutura inicial por camadas (`api`, `services`, `core`) já estabelecida.
- Uso de FastAPI com tipagem básica via Pydantic.
- Rate limiting presente (slowapi).
- Lifespan para startup/shutdown já implementado.

### Pontos fracos
- `app/services/poc_service.py` vazio quebra contrato central da aplicação.
- `alerts.py` concentra validação HTTP + orquestração + detalhes de cache_key.
- Hook de shutdown no router (`@router.on_event("shutdown")`) em vez de unificado no lifespan.
- Falta módulo de configuração central (env/config) com validação.
- Documentação operacional insuficiente/incompleta.

### Arquivos com responsabilidade excessiva
- `app/api/v1/alerts.py`: concentra decisões de negócio (composição de cache_key, fluxo de cancelamento, persistência indireta).
- `app/main.py`: configuração global + middleware + wiring + logging sem abstração.

---

## 4) Robustez de produção

### Situação atual
- Startup cria diretório de storage (`ensure_storage_dir`) — positivo.
- Há rota de health simples.
- Tratamento de exceção genérica presente nos endpoints.

### Riscos
- **Crítico:** serviço externo essencial ausente (`poc_service.py` vazio) inviabiliza execução normal.
- Tratamento de exceção em `cancel_alert` mascarava `HTTPException` (400/404 -> 500) — corrigido de forma cirúrgica.
- Persistência de upload não valida tamanho/ctype/extensão do arquivo.
- Falta tratamento explícito para falhas de IO em `save_uploaded_photo`.
- CORS permissivo (`allow_origins=["*"]`) inadequado para produção.
- Sem métricas, sem tracing, sem logs estruturados.

---

## 5) Qualidade de código

### Observações
- Typing parcial e simples, aceitável para estágio inicial.
- Nomes de funções são claros.
- Comentários em português ajudam entendimento, mas há excesso de comentário explicando óbvio em alguns pontos.
- Ausência de testes automatizados no repositório.
- Arquivos de documentação base ainda não consolidados.

---

## 6) Diagnóstico consolidado

### Riscos prioritários
1. **[P0] Serviço de integração ausente** (`poc_service.py` vazio).
2. **[P1] Observabilidade insuficiente para produção** (logs sem rotação/estrutura).
3. **[P1] Falta de contratos de configuração/env validados**.
4. **[P2] Acoplamento de regras no endpoint** (`alerts.py`).
5. **[P2] Segurança operacional básica incompleta** (CORS amplo, upload sem validação forte).

### Quick wins
- Corrigir mascaramento de `HTTPException` em endpoint de cancelamento (**aplicado**).
- Completar documentação arquitetural e plano de evolução (**aplicado**).
- Consolidar requirements na raiz e remover ambiguidade de instalação.
- Introduzir módulo de config (`BaseSettings`) sem alterar contrato externo.

### Melhorias estruturais futuras
- Implementar `poc_service.py` com interface explícita + retries + timeout + erros de domínio.
- Criar pacote `app/core/logging_config.py` com logging idempotente (console + rotating file).
- Extrair regras de negócio de `alerts.py` para serviço de aplicação.
- Introduzir testes de integração mínimos para endpoints críticos.
