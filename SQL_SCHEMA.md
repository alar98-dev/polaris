## Esquema relacional SQL do POLARIS (PostgreSQL)

Este documento descreve a estrutura relacional (tabelas, colunas, tipos, índices e relações) recomendada para o agente POLARIS. Inclui exemplos DDL, considerações sobre `pgvector`, índices, queries de similaridade, retenção e notas para migrações Alembic.

Observação de segurança: não armazene senhas ou PII sem consentimento; siga as regras de mascaramento descritas em `POLARIS_PROFILE.md`.

---

## Visão geral das entidades

- `projects` — metadados do portfólio (projetos/soluções que POLARIS pode sugerir).
- `artifacts` — artefatos gerados (protótipos, mocks, transcrições, resumos).
- `artifact_chunks` — fragmentos de `artifacts` preparados para indexação e busca semântica.
- `conversations` — registro das interações com clientes (sessões, mensagens, resumo).
- `users` — clientes/contatos (opcional, dependendo do fluxo de autenticação).
- `jobs` — jobs assíncronos (ingest, backfill, generation) para rastreio/monitoramento.

Em geral, vetores (embeddings) serão armazenados em `artifact_chunks.embedding` com o tipo `vector` (pgvector) quando disponível.

---

## Pré-requisitos no banco

1. PostgreSQL 13+ (recomendado).
2. Extensão pgvector instalada no servidor Postgres:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

3. Habilitar configurações necessárias no Postgres (memória, work_mem tuning) se indexação ivfflat for usada.

---

## DDL recomendado (exemplos)

Observação: ajustar tipos/lengths conforme necessidades (UTF8 text, JSONB para metadata).

```sql
-- projects
CREATE TABLE projects (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  tags TEXT[],
  estimated_budget NUMERIC(12,2),
  stack JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- artifacts
CREATE TABLE artifacts (
  id SERIAL PRIMARY KEY,
  project_id INT REFERENCES projects(id) ON DELETE SET NULL,
  type TEXT NOT NULL, -- prototipo|mock|conversation
  content TEXT, -- full content (markdown, json string, transcript)
  metadata JSONB DEFAULT '{}',
  created_by TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- artifact_chunks (text chunks + embedding vector)
CREATE TABLE artifact_chunks (
  id SERIAL PRIMARY KEY,
  artifact_id INT REFERENCES artifacts(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  text TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  embedding vector(1536), -- ajuste a dimensão conforme o modelo de embedding
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(artifact_id, chunk_index)
);

-- conversations / sessions
CREATE TABLE conversations (
  id SERIAL PRIMARY KEY,
  session_id UUID UNIQUE,
  client_id TEXT,
  transcript JSONB, -- array de turnos: [{from, text, ts}, ...]
  summary TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- jobs (background tasks)
CREATE TABLE jobs (
  id UUID PRIMARY KEY,
  type TEXT NOT NULL,
  status TEXT NOT NULL, -- queued|running|done|failed
  payload JSONB,
  result JSONB,
  attempts INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## Índices e performance (pgvector)

1. Índices para campos consultados frequentemente:

```sql
CREATE INDEX idx_projects_tags ON projects USING GIN (tags);
CREATE INDEX idx_artifacts_project ON artifacts (project_id);
CREATE INDEX idx_artifacts_created_at ON artifacts (created_at);

-- index por metadata jsonb (ex.: buscar por language)
CREATE INDEX idx_artifact_chunks_metadata ON artifact_chunks USING GIN (metadata);
```

2. Índice vetorial para busca semântica com pgvector (ivfflat speeds up nearest neighbor):

```sql
-- ajustar 'lists' conforme Tamanho do dataset e memória
CREATE INDEX idx_artifact_chunks_embedding_ivfflat ON artifact_chunks USING ivfflat (embedding) WITH (lists = 100);
```

Notas:
- Antes de criar ivfflat index, execute `SELECT vector_cosine_distance(...)` load check; o ivfflat index precisa de build time e tuning das lists.
- Se dataset pequeno, busca linear (`ORDER BY embedding <-> query`) pode ser suficiente sem índice.

---

## Entradas e Upserts (exemplos)

Inserir artifact e chunks (transacional):

```sql
BEGIN;
INSERT INTO artifacts (project_id, type, content, metadata, created_by)
VALUES (12, 'protótipo', $1, $2::jsonb, 'polaris')
RETURNING id INTO artifact_id;

-- inserir chunks em batch (exemplo via client code)
INSERT INTO artifact_chunks (artifact_id, chunk_index, text, metadata, embedding)
VALUES
  (artifact_id, 0, 'texto 1', '{}'::jsonb, $embedding1),
  (artifact_id, 1, 'texto 2', '{}'::jsonb, $embedding2);

COMMIT;
```

Recomendação: calcular fingerprint/hash (SHA256) de cada chunk para evitar duplicação antes do insert; usar upsert baseando-se em (artifact_id, chunk_index) ou fingerprint.

---

## Queries de similaridade (exemplos)

1) Consulta básica (top-k nearest neighbors)

```sql
-- $query_embedding é um vector pass-through
SELECT ac.id, ac.artifact_id, ac.text, (ac.embedding <-> $query_embedding) AS distance
FROM artifact_chunks ac
WHERE ac.metadata->>'lang' = 'pt' -- filtro relacional opcional
ORDER BY ac.embedding <-> $query_embedding
LIMIT 10;
```

2) Recuperar contexto com join nos artifacts

```sql
SELECT a.id AS artifact_id, a.type, ac.chunk_index, ac.text
FROM artifact_chunks ac
JOIN artifacts a ON a.id = ac.artifact_id
WHERE ac.embedding IS NOT NULL
ORDER BY ac.embedding <-> $query_embedding
LIMIT 10;
```

Notas sobre score: `ac.embedding <-> $query_embedding` retorna distância (menor = mais próximo). Para transformar em similaridade use por exemplo `similarity = 1/(1+distance)`.

---

## Particionamento e retenção

- Retention: artefatos grandes ou sensíveis podem ter política de retenção (ex.: purge após X anos) e marcação via `metadata->'retention'`.
- Partitioning por data para `artifact_chunks` quando houver grande volume (range partitioning por created_at) para acelerar deletes e manutenção.

Exemplo (particionamento por mês):

```sql
-- criar parent table and monthly partitions (exemplo simplificado)
-- ver docs Postgres para syntax completa
```

---

## Alembic / Migrações

Recomendações:

- Incluir a criação da extensão `vector` numa migração inicial (executada com privilégios suficientes):

```sql
-- alembic migration up
op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
```

- Gerar migração automática após definir modelos SQLAlchemy (alembic revision --autogenerate).
- Testar migrações em environment de staging antes de aplicar em production.

Exemplo: skeleton alembic migration:

```python
def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    op.create_table(...)

def downgrade():
    op.drop_table(...)
```

---

## Consistência e transações

- Sempre usar transações ao inserir artefatos + chunks + embeddings para manter consistência.
- Se geração de embedding for externa (service), considerar inserir chunks sem embedding e usar job que atualiza embeddings e only mark chunk as indexed once embedding saved.

---

## Segurança, PII e governança

- Nunca gravar PII não mascarada nos campos `text`/`content` sem consentimento; se necessário, armazenar versão mascarada e registrar máscara no `metadata`.
- Auditar acessos e logs para queries que retornam conteúdo sensível.

---

## Monitoramento e operações

- Monitorar cardinalidade de `artifact_chunks` e latência das queries de similaridade.
- Script de manutenção: reindex periodicamente, VACUUM/ANALYZE conforme carga.

---

## Modelagem SQLAlchemy (mapa rápido)

Exemplo resumido (ver também `plan.md`):

```python
class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    tags = Column(ARRAY(Text))

class Artifact(Base):
    __tablename__ = 'artifacts'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    content = Column(Text)
    metadata = Column(JSONB)

class ArtifactChunk(Base):
    __tablename__ = 'artifact_chunks'
    id = Column(Integer, primary_key=True)
    artifact_id = Column(Integer, ForeignKey('artifacts.id'))
    chunk_index = Column(Integer)
    text = Column(Text)
    embedding = Column(pgvector.Vector(1536))
```

---

## Exemplos de operações comuns (resumo rápido)

- Inserir artifact -> gerar chunks -> gerar embeddings -> upsert chunks
- Query user query -> gerar embedding da query -> buscar top-k chunks -> montar contexto -> chamar LLM

---

## Checklist antes de produção

- Verificar instalação `pgvector` no Postgres
- Definir dimensão de vector (conforme modelo de embedding)
- Tunning `ivfflat lists` com base no dataset
- Criar backups e plano de rollback para migrações
- Definir políticas de retenção e masking para PII

---

Arquivo: `SQL_SCHEMA.md`
Local: `/srv/SERVER_ORION/models/agents/POLARIS/SQL_SCHEMA.md`

Se quiser, eu gero automaticamente:
- `models/sql_models.py` com os modelos SQLAlchemy completos (base no trecho acima), e
- um esqueleto de migração Alembic `versions/0001_init.py` que cria as tabelas e a extensão `vector`.
