## POLARIS — Documentação de Métodos e Funções

Este arquivo lista e documenta os métodos e funções públicos e internos esperados para o agente POLARIS. Para cada item apresento: propósito, assinatura esperada, parâmetros, retorno, erros/side-effects, exemplos de uso e notas de teste.

Observação: os nomes e assinaturas são sugeridos como contrato para implementação. Ajuste conforme o estilo e arquitetura do código-base (sincrono/assíncrono, classes ou funções funcionais).

---

SUMÁRIO RÁPIDO (métodos principais)

- Agent lifecycle
  - start()
  - stop()
  - health_check()

- Conversação / Discovery
  - ask_discovery_questions(session_id, message)
  - summarize_conversation(session_id)

- Portfólio & RAG
  - select_portfolio(query, top_k=5)
  - fetch_portfolio_metadata(ids)

- Geração de artefatos
  - generate_prototype(choice_id, context, output_path=None)
  - generate_mock(contract_name, context, count=10)

- LLM & Embeddings (adapters)
  - call_llm(prompt, max_tokens=..., temperature=..., headers=None)
  - embed_text(texts, model_name=None)

- Persistência / Knowledge
  - save_artifact(artifact: dict)
  - get_artifact(artifact_id)
  - ingest_and_index(artifact_id, text)
  - query_similar(query_embedding, filters=None, top_k=10)

- Infra / DB / Migrations
  - run_migrations()
  - check_db_connection()

- Utilities / Security
  - mask_pii(text)
  - validate_with_pydantic(contract_name, data)

---

## Agent lifecycle

start()
- Propósito: inicializar recursos (conexões DB, clients LLM/embeddings, pools, métricas) e começar listeners/queues.
- Assinatura: start() -> None
- Retorno: None
- Erros: lança Exception se recursos críticos falharem (DB unreachable, LLM health fail).
- Side-effects: inicia conexões, threads/async tasks.
- Exemplo:
  - agent.start()
- Testes sugeridos:
  - mock DB e LLM health -> start() retorna sem exceção
  - DB inacessível -> start levanta erro controlado

stop()
- Propósito: liberar recursos, fechar pools e garantir shutdown limpo.
- Assinatura: stop(force: bool = False) -> None
- Parâmetros: force — encerra imediatamente sem aguardar jobs pendentes
- Erros: raramente; log de falha no fechamento.
- Side-effects: flush de filas, persistência de estado.

health_check()
- Propósito: checar saúde das dependências (DB, LLM wrapper, embeddings) e retornar um resumo.
- Assinatura: health_check() -> dict
- Retorno eg:
  {
    'db': {'ok': True, 'latency_ms': 12},
    'llm': {'ok': True, 'latency_ms': 120},
    'embeddings': {'ok': True}
  }
- Erros: retorna dict marcando falhas; não deve lançar em condições normais.

---

## Conversação / Discovery

ask_discovery_questions(session_id: str, message: str) -> dict
- Propósito: processar um input do cliente e responder com a próxima pergunta/ação de discovery.
- Entrada:
  - session_id: identificador da sessão do cliente
  - message: texto do cliente
- Retorno: dict contendo: { 'next_question': str, 'slots': {..}, 'complete': bool }
- Erros: validação de input; retorna erro amigável se message vazio
- Observações: persiste o turno na tabela `conversations`.

summarize_conversation(session_id: str) -> str
- Propósito: gerar um resumo executivo da conversa (para `resumo_conversa.txt`).
- Entrada: session_id
- Retorno: resumo em texto
- Implementação: pode chamar LLM com prompt template "resuma esta conversa em 3 parágrafos" e retornar a resposta após validação.

---

## Portfólio & RAG

select_portfolio(query: str, top_k: int = 5) -> List[dict]
- Propósito: executar busca RAG na base de conhecimento para selecionar até top_k projetos do portfólio.
- Entrada: query (texto ou dict com metadados), top_k
- Retorno: lista de metadados de projetos: [{id, title, score, rationale}, ...]
- Erros: se embeddings/DB indisponível retorna lista vazia e log de erro.
- Notas: usa `embed_text()` + `query_similar()` + filtros relacionais.

fetch_portfolio_metadata(ids: List[int]) -> List[dict]
- Retorno: metadados completos dos ids solicitados.

---

## Geração de Artefatos

generate_prototype(choice_id: int, context: dict, output_path: Optional[str]=None) -> dict
- Propósito: gerar `protótipo.md` com conteúdo estruturado.
- Entrada:
  - choice_id: id do projeto/escolha do portfólio
  - context: dicionário com resultados do discovery, requisitos, restrições
  - output_path: caminho opcional para salvar em storage
- Retorno: { 'path': '/path/to/prototipo.md', 'content': '...' }
- Erros: validação de contexto; falha no LLM -> gerar fallback (template) e marcar para revisão manual.
- Notas: template deve seguir critério de aceitação (sumário, ≥5 reqs, mapa de dados, endpoints, riscos, next-steps).

generate_mock(contract_name: str, context: dict, count: int = 10) -> List[dict]
- Propósito: gerar mocks JSON conforme contrato Pydantic.
- Entrada: contract_name (ex.: 'User'), context (ex.: domain hints), count
- Retorno: lista de exemplos JSON; inclui também exemplos inválidos (2 por padrão)
- Erros: se contrato Pydantic não existe -> gerar mock genérico e incluir warning no retorno.

---

## LLM & Embeddings (adapters)

call_llm(prompt: str, max_tokens: int = 512, temperature: float = 0.2, headers: Optional[dict]=None, timeout: int = 15) -> dict
- Propósito: chamar o wrapper LLM (`gemini-wrapper`) e retornar texto normalizado + meta.
- Entrada: prompt, params
- Retorno: { 'ok': True/False, 'text': str, 'meta': {...} }
- Erros: em falhas de request retorna {'ok': False, 'error': '...'}; não propaga exceções não tratadas.
- Behavior: aplica retries com backoff; normaliza `text` que pode ser string ou objeto com `parts`.
- Exemplo de uso: see `plan.md` call_llm example.

embed_text(texts: List[str], model_name: Optional[str] = None, timeout: int = 10) -> List[List[float]]
- Propósito: chamar o serviço de embeddings e retornar vetores.
- Entrada: lista de strings
- Retorno: lista de vetores (listas de float)
- Erros: documentar quota/limits; em erro parcial retornar vetores para itens bem-sucedidos e incluir `errors` no retorno.

---

## Persistência / Knowledge

save_artifact(artifact: dict) -> int
- Propósito: persistir um artifact (protótipo/mock/resumo) no DB e retornar artifact_id.
- Entrada: artifact com campos mínimos (type, content, metadata)
- Retorno: artifact_id (int)
- Erros: falha DB -> raise or return error code dependendo do design; prefer transacionalmente consistente.

get_artifact(artifact_id: int) -> dict
- Retorno: registro completo do artifact.

ingest_and_index(artifact_id: int, text: str) -> dict
- Propósito: chunkar texto, gerar embeddings e inserir chunks+vetores na tabela `artifact_chunks`.
- Retorno: {'chunks': N, 'indexed': N}
- Erros: se embedding service indisponível -> rollback; criar job para retry/backfill.

query_similar(query_embedding: List[float], filters: Optional[dict] = None, top_k: int = 10) -> List[dict]
- Propósito: executar busca de similaridade e retornar chunks ordenados por similaridade.
- Retorno: lista com {chunk_id, text, similarity, artifact_id}

---

## Infra / DB / Migrations

run_migrations(alembic_cfg_path: str = 'alembic.ini') -> bool
- Propósito: executar migrações Alembic no ambiente configurado.
- Retorno: True se sucesso
- Erros: erros de migration devem abortar deploy e logar stack trace.

check_db_connection() -> bool
- Propósito: test connection `SELECT 1`.

---

## Utilities / Segurança

mask_pii(text: str, level: str = 'partial') -> str
- Propósito: detectar e mascarar PII (emails, CPFs, telefones).
- Parâmetros: level (partial/full)
- Retorno: texto mascarado
- Notas: usar bibliotecas de PII detection ou regexs; registrar no metadata onde foi mascarado.

validate_with_pydantic(contract_name: str, data: dict) -> (bool, List[str])
- Propósito: validar `data` contra contrato Pydantic identificado por `contract_name`.
- Retorno: (is_valid, errors)

---

## Admin / Backfill / Maintenance

backfill_embeddings(batch_size: int = 100) -> dict
- Propósito: processar artifacts antigos em batches e gerar embeddings.
- Retorno: { 'processed': N, 'errors': M }

export_artifacts(since: Optional[str] = None, path: str = './export') -> str
- Propósito: exportar artifacts e mocks para um diretório ou storage para auditoria.

---

## Erros comuns e handling

- LLM timeout: retry with backoff; if still fails, fallback to template and set `requires_human_review = True`.
- DB transaction conflict: retry a limited number of times; escalate if persists.
- Embedding service rate limit: backoff and queue items for background processing.

---

## Contratos, Tests e Exemplos

- Para cada método público, escrever 2 tipos de testes:
  1. Unit: mockar dependências (LLM, DB) e validar comportamento esperado.
  2. Integration (fast): usar sqlite/PG test instance + local gemini-wrapper stub.

- Exemplos de testes para `generate_mock`:
  - Caso feliz: contrato Pydantic existe -> retorna 10 exemplos válidos + 2 inválidos e validação passa.
  - Contrato ausente: retorna warning e mocks gerados com esquema inferido.

---

## Notas finais

- Padronize logs e nomes de métricas para facilitar dashboards.
- Prefira return objects/dicts (não imprimir) para facilitar testes.
- Documente a versão das dependências do LLM/embedding model nos metadados dos artifacts para reprodutibilidade.

Arquivo: `POLARIS_METHODS.md`
Local: `/srv/SERVER_ORION/models/agents/polaris/POLARIS_METHODS.md`

Se quiser, implemento automaticamente os stubs Python para estes métodos (`polaris/agent.py`) e test skeletons (`tests/test_agent.py`).
