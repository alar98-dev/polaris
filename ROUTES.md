# POLARIS — Documentação das Rotas FastAPI

Este documento descreve todas as rotas (endpoints) planejadas para o serviço FastAPI do agente POLARIS. Para cada rota apresento:
- Path e método HTTP
- Autenticação e headers esperados
- Schema do request (campos, tipos, obrigatoriedade)
- Schema do response (campos, tipos, exemplos)
- Códigos de status esperados e erros comuns
- Side-effects e observability (logs, métricas)
- Notas de segurança e comportamento desejado

Observação: as rotas abaixo são um contrato/blueprint. Implementações concretas (sync/async, validation libs) devem seguir os contratos descritos.

## Convenções aplicadas a todas as rotas

- Header obrigatório: `X-Request-ID: <uuid>` (para rastreabilidade). Gerar um UUID no cliente se ausente.
- Autenticação: `Authorization: Bearer <TOKEN>` para rotas que alteram estado ou administrativas. Rotas de leitura pública (health, metrics) podem ser abertas ou protegidas conforme política.
- Content-Type: `application/json` para bodies JSON.
- Timeouts: LLM/embedding calls têm timeout configurável; apply 5–15s padrão por chamada e retries com backoff para operações LLM/embeddings.
- Rate-limiting: aplicar limites por IP/token para endpoints intensivos (ex.: `/generate/*`, `/embed`).
- Logging: cada request deve logar request_id, route, user (quando aplicável), latency_ms e status.

---

## 1) Health geral

- Path: GET /api/v1/health
- Auth: opcional
- Request: nenhum
- Response (200 OK):
  {
    "status": "ok",
    "components": {
      "db": {"ok": true, "latency_ms": 12},
      "llm": {"ok": true, "latency_ms": 120},
      "embeddings": {"ok": true}
    }
  }
- Erros:
  - 503 Service Unavailable quando dependências críticas falham
- Side-effects: leitura de health dos serviços dependentes (DB, LLM, embeddings). Não alterar estado.
- Notas: endpoint usado por orquestradores e infra para checks.

Example curl:

```bash
## POLARIS — Estado atual e guia orientado a LLM

Este documento foi reescrito como um guia prático, focado no status atual do código, lacunas conhecidas e ações práticas orientadas a LLMs (prompts, contratos de JSON, exemplos e testes). Objetivo: permitir que engenheiros e LLMs colaborem para completar/automatizar partes pendentes do agente POLARIS.

## 1) Sumário rápido do estado atual

- Código lido: `polaris/app.py`, `polaris/agent_core.py`, `polaris/agent.py`, `polaris/schemas.py`, `polaris/utils.py`, `polaris/adapters/embeddings.py`, `polaris/adapters/probe_embedding_contract.py`, `examples/python_interaction.py`.
- A API FastAPI existe (`app.py`) com rotas básicas: health, sessions (create), discovery, prototype, mocks, estimate.
- `PolarisAgent` (em `agent_core.py`) implementa lógica síncrona/async básica com fallbacks estáticos (ex.: `select_portfolio` retorna exemplos estáticos).
- Adaptador de embeddings (`adapters/embeddings.py`) existe e tenta múltiplos endpoints — mas não está integrado em todas as rotas do agente.
- Não existem testes automatizados no repositório.

## 2) Lacunas principais (o que falta)

1) Extração automática de `slots` em discovery
   - O método `ask_discovery_questions` assume que `session['slots']` está preenchido. Falta um extractor que interprete mensagens do usuário e atualize `slots` automaticamente (por LLM ou heurística).

2) Integração ativa com embeddings no fluxo de recomendação
   - `select_portfolio` usa fallback estático. Falta: geração de embedding para a query e busca semântica via `adapters.embeddings`.

3) Health-check completo
   - `health_check` checa apenas o LLM. Falta checar embeddings e reportar componentes (DB, cache) se existirem.

4) Endpoints auxiliares de sessão
   - Não há endpoint para consultar/atualizar `slots` manualmente (útil para debugging e testes).

5) Testes e CI
   - Falta cobertura mínima: unit tests e testes de integração das rotas (usando `pytest` + `httpx`/`requests`/`pytest-asyncio`).

6) Documentação orientada a LLM
   - Precisa de prompt templates, schemas de saída e exemplos para que LLMs possam preencher `slots`, validar respostas e gerar protótipos/mocks.

## 3) Contratos LLM — formatos e prompts recomendados

Objetivo: definir entradas/saídas determinísticas para chamadas LLM que extraem dados (slots) e para geração de texto (protótipos). Sempre pedir JSON válido e validar parse.

- Slot extraction — contrato de saída (JSON):

  {
    "pain": "string or null",
    "users": "string or null",
    "kpi": "string or null",
    "budget": "string or null",
    "confidence": {"pain": 0.0-1.0, "users": 0.0-1.0, "kpi": 0.0-1.0, "budget": 0.0-1.0}
  }

Prompt template (slot extraction):

  "Given the user message below, extract the following fields as a JSON object: pain, users, kpi, budget. Return only valid JSON. If a field cannot be determined, use null. Also include a confidence score (0.0-1.0) per field.\n\nMessage: \"{message}\""

Notes: sempre validar com tentativa de parse JSON e, em caso de falha, re-prompt com "You must output valid JSON only".

- Portfolio selection — contrato de entrada/saída:

  Input: { "query": "...", "top_k": 5 }
  Output: [ {"id": int, "title": str, "score": float, "rationale": str} ]

Recommended pipeline for `select_portfolio`:
1. Call embedding adapter to create vector for `query`.
2. Call embedding adapter `search_vector(vector, top_k)` to retrieve candidates.
3. For each candidate, optionally call LLM to generate a short `rationale` (prompt: "Explain why this candidate matches the query in 1-2 sentences"). Cache rationales.

## 4) Exemplos de prompts prontos (usar como templates)

- Slot extraction prompt (compact):

  "Extract 'pain', 'users', 'kpi' and 'budget' from the following message. Output strictly valid JSON with fields pain, users, kpi, budget and confidence. If unknown, use null. Message: \"{message}\""

- Rationale prompt (for each candidate):

  "Given the user query '{query}' and the candidate project description: '{candidate_text}', write a 1-2 sentence rationale explaining why this candidate matches the query. Output plain text."

## 5) Endpoints relevantes (resumo enxuto para integração LLM)

- POST /api/v1/sessions — criar sessão
- POST /api/v1/sessions/{session_id}/message — enviar mensagem e acionar extração (IMPLEMENTAR)
- GET /api/v1/health — checar LLM e embeddings (expandir)
- POST /api/v1/prototype — gerar protótipo via LLM (já presente)
- POST /api/v1/mocks — gerar mocks (já presente via `utils.generate_mock_examples`)

Observação: proponho adicionar PATCH /api/v1/sessions/{session_id}/slots para permitir updates manuais/por testes.

## 6) Plano de implementação (priorizado, 3 sprints curtos)

Curto prazo (1): habilitar slot extraction automático e endpoint PATCH
- Implementar em `polaris/agent_core.py` um método async `_extract_slots_from_message(session, message)` que:
  - monta o prompt de extração, chama `call_llm`, parseia JSON e atualiza `session['slots']`.
  - em caso de falha de parse, tenta um re-prompt simples (1 retry).
  - registra confidences e anexa ao turno.

- Modificar `ask_discovery_questions` para chamar `_extract_slots_from_message` antes de decidir `next_question`.

- Criar endpoint PATCH `/api/v1/sessions/{session_id}/slots` em `polaris/app.py` (schema simples: dict) para atualizar slots manualmente.

Curto prazo (2): integrar embeddings no `select_portfolio`
- Em `select_portfolio`, quando `embedding_adapter` estiver disponível:
  - gerar embedding para query (adapter.get_embedding)
  - chamar adapter.search_vector(vector, top_k)
  - mapear resultados para o schema de output
  - fallback: manter lista estática quando adapter ausente/erro.

Médio prazo (3): health-check e testes
- Expandir `health_check` para checar embeddings e retornar componentes detalhados.
- Escrever testes com `pytest` e `pytest-asyncio`:
  - test_create_session
  - test_discovery_flow_with_slot_extraction (mock call_llm)
  - test_select_portfolio_with_embeddings (mock embedding adapter)

Longo prazo (4): observability, retries e políticas de segurança

## 7) Exemplos práticos — payloads e resultado esperado

- Input (mensagem do usuário):

  "Quero construir uma loja online para vender roupas. Orçamento em torno de 30k. Foco em conversão e checkout simples. Usuários: pessoas entre 18-45 que compram pelo celular."

- Expected slot extraction (JSON):

  {
    "pain": "Preciso vender online com checkout simples",
    "users": "Consumidores 18-45, mobile-first",
    "kpi": "conversão",
    "budget": "~30000",
    "confidence": {"pain":0.85,"users":0.9,"kpi":0.8,"budget":0.7}
  }

## 8) Como testar localmente (passo-a-passo rápido)

1) Instale dependências (segundo `requirements.txt`). Exemplo:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2) Rodar FastAPI (desenvolvimento):

```bash
uvicorn polaris.app:app --reload --port 8002
```

3) Criar sessão e enviar mensagem (exemplo curl):

```bash
curl -s -X POST "http://localhost:8002/api/v1/sessions" -H "Content-Type: application/json" -d '{"client_id":"dev"}'
# pega session_id do retorno e usa no endpoint /sessions/{id}/message
```

4) Para testar extração sem LLM real, mocke `PolarisAgent.call_llm` retornando o JSON esperado (útil em pytest).

## 9) Checklist para entrega mínima viável (MVP)

- [ ] Implementar `_extract_slots_from_message` com 1 retry para JSON parse
- [ ] Atualizar `ask_discovery_questions` para usar o extractor
- [ ] Adicionar PATCH `/api/v1/sessions/{session_id}/slots`
- [ ] Integrar embeddings em `select_portfolio` com fallback
- [ ] Expandir `health_check` para embeddings
- [ ] Criar 3 testes com pytest-asyncio
- [ ] Atualizar `ROUTES.md` e `README_RUN.md` com instruções de execução e variáveis de ambiente

## 10) Observações finais e recursos para LLM

- Sempre pedir ao LLM que retorne apenas JSON quando estiver extraindo dados; validar com um parse e ter um re-prompt de correção.
- Use prompts curtos e exemplos (few-shot) quando as extrações forem complexas.
- Registre a cadeia de prompts e respostas (sem PII) para auditoria e melhoria do prompt.

---

Arquivo editado: `ROUTES.md` — conteúdo atualizado com foco em LLM-orientado, estado atual e próximos passos técnicos.

Se quer, aplico agora a implementação mínima (slot extractor + endpoint PATCH + testes básicos). Diga "implementar agora" e eu começo as mudanças no código e nos testes.
