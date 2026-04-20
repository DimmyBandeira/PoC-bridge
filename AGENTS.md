# AGENTS.md — Guia Operacional do Repositório `PoC-bridge`

## Objetivo
Este repositório implementa uma API FastAPI (bridge) para integração entre WebGuardião e iConvNet.
A evolução deve priorizar estabilidade operacional, observabilidade e mudanças pequenas/verificáveis.

## Princípios de colaboração
1. **Não quebrar comportamento existente** sem justificativa técnica explícita.
2. **Preferir patches cirúrgicos** a refatorações amplas.
3. **Manter rastreabilidade**: toda alteração relevante deve ser acompanhada de diagnóstico/justificativa.
4. **Evitar acoplamento extra** entre camada HTTP, regra de negócio e infraestrutura.
5. **Não adicionar dependência nova** sem ganho operacional claro.

## Convenções de arquitetura
- Separar responsabilidades em camadas:
  - `app/main.py`: bootstrap da aplicação e wiring.
  - `app/api/`: contratos HTTP (routers, schemas de borda, validação de entrada).
  - `app/services/`: orquestração e integrações externas/IO.
  - `app/core/`: utilitários transversais (segurança, config, logging).
- Evitar lógica de negócio complexa dentro de endpoints.
- Introduzir contratos explícitos (tipagem/interfaces) quando módulos crescerem.

## Convenções de logging
- Usar sempre `logger = logging.getLogger(__name__)` por módulo.
- Em exceções reais, registrar com stacktrace (`logger.exception(...)` ou `exc_info=True`).
- Evitar `print` para logs operacionais.
- Configuração de logging deve ser centralizada e idempotente (sem duplicação de handlers).
- Meta de produção: suporte a console + arquivo com rotação.

## Qualidade e robustez
- Adicionar type hints em funções públicas e pontos críticos.
- Tratar erros de IO/rede com mensagens operacionais claras.
- Não mascarar `HTTPException` em blocos `except Exception`.
- Validar entradas de usuário (incluindo arquivos upload).
- Garantir startup/shutdown previsíveis.

## Fluxo recomendado para mudanças
1. Ler estrutura atual e mapear impacto.
2. Propor mudança mínima.
3. Implementar.
4. Validar com testes/checks disponíveis.
5. Documentar decisão e próximos passos.

## Entregáveis mínimos em alterações arquiteturais
- Atualização de `analise_arquitetura.md` (diagnóstico).
- Atualização de `plano_evolucao.md` (prioridades e execução incremental).
- Registro explícito de riscos aceitos (quando aplicável).
