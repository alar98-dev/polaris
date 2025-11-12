## POLARIS — Ferramentas e Dependências

Este documento lista ferramentas, bibliotecas Python e tecnologias recomendadas para desenvolver, executar e operar o agente POLARIS.

## Resumo rápido

- Linguagem principal: Python 3.10+ (recomendado 3.11)
- Banco relacional: PostgreSQL (com extensão `pgvector` para vetores)
- Serviços LLM/Embeddings: `gemini-wrapper` (HTTP wrapper), embedding service (`embedding:8001`) ou vector DB opcional
- Orquestração: Docker / docker-compose; CI: GitHub Actions ou similar

---

## Bibliotecas Python (core)

- requests — chamadas HTTP a wrappers/serviços
- httpx — alternativa async a requests (se usar async)
- pydantic — validação e modelos de dados (v2 recomendado)
- sqlalchemy — ORM (usar 1.4+ com suporte a asyncio se necessário)
- alembic — migrações de esquema para SQLAlchemy
- psycopg2-binary — driver clássico para Postgres (ou asyncpg para asyncio)
- pgvector (pgvector.sqlalchemy) — integração SQLAlchemy com `pgvector`
- typing-extensions / mypy — tipagem estática e checagens
- python-dotenv — (opcional) carregar `.env` em dev

## Bibliotecas para embeddings/LLM e infra ML

- client do serviço de embeddings (se houver SDK interno) ou usar requests/httpx
- pinecone-client, pymilvus, weaviate-client — apenas se optar por vector DB externo
- transformers / sentence-transformers — somente para gerar embeddings localmente

## Web / API / Worker

- fastapi — recomendado para construir endpoints do agente (se expor APIs)
- uvicorn — servidor ASGI para FastAPI
- celery / rq / dramatiq — filas de background para ingestão e geração de embeddings (opcional)

## Observabilidade / Logging / Telemetria

- structlog ou standard logging (structlog recomendado para logs estruturados)
- prometheus-client — métricas expostas para Prometheus
- opentelemetry-api + opentelemetry-exporter-* — tracing (opcional)
- grafana — dashboard de visualização

## Testes / Qualidade / Devops

- pytest — testes unitários e de integração
- pytest-mock — mocking
- tox — matrizes de testes (opcional)
- black, ruff (ou flake8) — formatação e lint
- pre-commit — hooks para qualidade de código

## Segurança / Segredos

- HashiCorp Vault / AWS Secrets Manager / Kubernetes Secrets — armazenar credenciais e `DATABASE_URL` em produção
- bandit — scanner básico de segurança para Python (opcional)

## Banco de dados / Indexação vetorial

- PostgreSQL 13+ com extensão `pgvector` (recomendado) — armazena vetores e dados relacionais
- Índices: hnsw/L2 com pgvector para alta performance
- Alternativa: vector DB (Pinecone, Milvus, Weaviate) se escala de RAG aumentar

## Dependências de sistema / ferramentas CLI

- docker & docker-compose — para ambientes locais e deploys simples
- make — receita de comandos úteis (opcional)
- git — versionamento

## Exemplo mínimo de `requirements.txt`

```
requests>=2.28
httpx>=0.24
pydantic>=2.0
sqlalchemy>=1.4
alembic>=1.9
psycopg2-binary>=2.9
pgvector>=0.2
fastapi>=0.95
uvicorn[standard]>=0.22
pytest>=7.0
black>=24.0
ruff>=0.12
python-dotenv>=0.21
structlog>=22.0
prometheus-client>=0.16
```

Para projetos async substituir `psycopg2-binary` por `asyncpg` e usar `sqlalchemy[asyncio]`.

## Comandos de instalação (pip)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Instalação específica de pgvector (dependendo do sistema): a extensão `pgvector` deve ser habilitada no Postgres do servidor; em Debian/Ubuntu há pacote `postgresql-<versão>-pgvector` ou pode-se compilar/instalar via `pip install pgvector` no client e criar a extensão no DB `CREATE EXTENSION IF NOT EXISTS vector;`.

## CI / Deploy (recomendações)

- Pipeline mínimo:
  1. Lint + tests
  2. Build container (Dockerfile)
  3. Deploy para staging
  4. Run migration (Alembic) com variáveis de ambiente injetadas
  5. Smoke tests (+ healthchecks)

- GitHub Actions: usar secrets para `DATABASE_URL`, `EMBEDDING_API_KEY`, `AI_API_KEY`.

## Segurança e privacidade (obrigatório)

- Não salvar PII em campos abertos sem mascaramento.
- Encriptar tráfego entre serviços (TLS) e usar roles/permissions mínimos no Postgres.
- Rotacionar segredos periodicamente e auditar acessos.

## Extras / ferramentas úteis

- jq — manipulação rápida de JSON em scripts
- pgcli / psql — administração do Postgres
- ngrok — exposições temporárias durante dev (usar com cautela)

## Observações finais

- Versões: pinnear versões em `requirements.txt` para produção.
- Iniciar com o conjunto mínimo (core libs, requests, sqlalchemy, alembic, pydantic, psycopg2) e adicionar módulos conforme a necessidade (vector DB, transformers).

Se quiser, eu crio também:
- `requirements.txt` gerado e um `Dockerfile` mínimo para POLARIS;
- Módulo Python `models/sql_models.py` com os modelos SQLAlchemy sugeridos;
- Script de migração Alembic inicial (esqueleto).
