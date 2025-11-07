# POLARIS — Interação detalhada com modelos

Este arquivo contém exemplos práticos (curl e HTTP) e padrões de payload que o agente POLARIS deve usar ao chamar serviços de modelos.

## 1) Gerar embedding (exemplo curl)

```bash
curl -s -X POST http://embedding:8001/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "Como otimizar latência em serviços web?"}'
```

Resposta esperada (exemplo):

```json
{
  "embedding": [0.123, 0.456, ...],
  "model": "all-MiniLM-L6-v2",
  "dimensions": 384
}
```

## 2) Buscar documentos (exemplo curl)

```bash
curl -s -X POST http://embedding:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "otimizar latencia web", "collection": "knowledge_base", "limit": 5}'
```

Resposta esperada (exemplo):

```json
{
  "results": [
    {"id": "doc_01", "score": 0.92, "text": "...", "metadata": {...}},
    ...
  ]
}
```

## 3) Chamar LLM via ai-agent (exemplo de criação de tarefa)

```bash
curl -s -X POST http://ai-agent:8002/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Responder pergunta",
    "description": "Gerar resposta com contexto",
    "task_type": "chat_completion",
    "input_data": {
      "prompt": "{PROMPT_WITH_CONTEXT}",
      "max_tokens": 512
    }
  }'
```

Resposta esperada (exemplo):

```json
{
  "task_id": "task_123",
  "status": "queued",
  "assigned_agent": "polaris"
}
```

## 4) Timeouts e retries

- Timeout padrão: 30s para chamadas LLM/embedding em requests síncronos.
- Retries: 3 tentativas com backoff exponencial (e.g., 1s, 2s, 4s).
- Circuit breaker: após N falhas consecutivas (configurável), marcar serviço como degradado e escalar para fallback.

## 5) Formato de logs

- Incluir no corpo do request: `x_request_id` header e, no JSON, `metadata.request_id`.
- Exemplo de log correlacionado:
  - POLARIS: request_id XYZ -> Embedding request -> vectordb -> ai-agent -> response

## 6) Tratamento de erros (padrão)

- 4xx: validar payload e abortar (registrar erro e enviar feedback ao usuário caso exista)
- 5xx: retry com backoff; se persistir, abrir incidente e retornar mensagem padrão de falha

## 7) Segurança de payloads

- Limitar tamanho do prompt (`MAX_PROMPT_TOKENS` configurável)
- Remover/mascarar PII antes de enviar para serviços externos

