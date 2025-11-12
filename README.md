# POLARIS — Agente de Desenvolvimento de Software

## 🚀 Início Rápido

O POLARIS é um agente de IA que auxilia no desenvolvimento de software, desde descoberta de requisitos até geração de protótipos e estimativas.

### Como Usar a API

Para instruções completas de uso da API FastAPI, consulte: **[API_USAGE.md](API_USAGE.md)**

**Iniciar servidor:**
```bash
uvicorn polaris.app:app --host 0.0.0.0 --port 8000
```

**Documentação interativa:** http://localhost:8000/docs

---

# POLARIS — Guia de Interação com Modelos do Servidor

Este documento descreve como o agente POLARIS deve interagir com os modelos hospedados no servidor (LLMs, embeddings, modelos de visão, etc.). Contém convenções, endpoints recomendados, exemplos e boas práticas.

Local dos arquivos
- Diretório desta documentação: `models/agents/polaris/`
- Template de metadados de modelos: `models/docs/METADATA_TEMPLATE.md`

Referências principais
- Plano operacional do agente: `models/agents/polaris/plan.md` (visão, contratos I/O, artefatos e integração com infra).
- Perfil completo: `models/agents/polaris/POLARIS_PROFILE.md` (atributos, persona, SLAs, exemplos).
- Métodos e contratos: `models/agents/polaris/POLARIS_METHODS.md` (assinaturas, I/O, erros, exemplos de teste).
- Ferramentas e dependências: `models/agents/polaris/TOOLS.md` (bibliotecas, CLI, CI recomendadas).

Visão geral
- POLARIS é um agente orquestrador que toma decisões, cria planos e invoca inferências em modelos (LLM, embeddings, etc.).
- A comunicação ideal se dá via APIs internas (serviços Docker Compose) ou através de URIs externas se modelos estiverem em object storage ou serviços gerenciados.

Sumário rápido
1. Autenticação e segurança
2. Endpoints e convenções de URL
3. Exemplo de fluxo (RAG)
4. Exemplo em Python (arquivo de exemplo)
5. METADATA e versionamento
6. Deploy e recursos necessários
7. Boas práticas e limitações

---

1) Autenticação e segurança

- Em ambiente local (docker compose), prefira usar nomes de serviço da rede Docker: `ai-agent:8002`, `embedding:8001`, `ollama:11434`.
- Em produção, use URLs internas/privadas e variáveis de ambiente para chaves (ex.: `AI_API_KEY`, `EMBEDDING_API_KEY`).
- Nunca envie dados sensíveis sem anonimização. Se for necessário, aplique pseudonimização e registre no `METADATA.md` do modelo.
- POLARIS deve incluir um header `X-Request-ID` para rastreabilidade em logs e `Authorization: Bearer <TOKEN>` quando aplicável.

2) Endpoints e convenções

- Endpoints do ecossistema (exemplos):
  - Agente / Orquestração: `http://ai-agent:8002/api/` ou `http://localhost:8002/api/`
  - Embeddings: `http://embedding:8001/embed`, `http://embedding:8001/store`, `http://embedding:8001/search`
  - LLM local (Ollama): `http://ollama:11434` (API específica do Ollama para inferência)

- Convenção de uso:
  - Prefira `POST` para inferência com payload JSON. Inclua `timeout` apropriado e retry conservador com backoff exponencial.
  - Para requests com payloads grandes (arquivos, documentos), envie o arquivo para storage (S3/MinIO) e passe a URI ao serviço de ingestão.

3) Fluxo de exemplo: RAG (Retrieval-Augmented Generation)

1. POLARIS recebe tarefa com `question` ou `prompt`.
2. Chamar serviço de embeddings para gerar embedding da `query`:
   - POST `http://embedding:8001/embed` com JSON: `{ "text": "..." }` -> responde `embedding: [..]`.
3. Chamar coleção vetorial para buscar documentos relevantes:
   - POST `http://embedding:8001/search` com `{ "query": "...", "collection": "kb" }`.
4. Reunir contexto retornado (top-k), montar prompt e chamar LLM via `ai-agent` ou diretamente `ollama`.
5. Validar resposta, registrar logs e retornar resultado.

4) Exemplo de arquitetura de chamada (alt. simplificada)

- POLARIS -> Embeddings service -> Vector DB -> POLARIS -> ai-agent / Ollama -> POLARIS -> Client

5) METADATA e versionamento

- Cada modelo usado deve ter `METADATA.md` conforme template em `models/docs/METADATA_TEMPLATE.md`.
- Exemplo de versão: `v1.0.0` seguindo semver. Atualize `METADATA.md` e `models/docs/CHANGELOG.md` (se houver) em cada release.

6) Deploy e recursos

- Recursos indicativos para LLMs locais: 8–16GB RAM para modelos médios (depende do modelo). Para quantização e inferência eficiente usar GPUs quando possível.
- Use `models/pipelines/` para colocar manifests de deploy (Dockerfile, k8s manifests).

7) Boas práticas

- Use `X-Request-ID` e correlacione logs entre serviços.
- Sanitize inputs (tamanho máximo de prompt, remoção de PII quando aplicável).
- Versione prompts e templates no repositório (`docs/LLM_Prompts.md`) para reprodutibilidade.
- Teste respostas com conjunto de casos (unitários) e mantenha métricas de qualidade (F1, precisão, taxa de rejeição).

---


Infra / Operacional (resumo)

- Banco de dados: este agente deve usar o PostgreSQL provisionado no servidor ORION quando necessário para persistência de artefatos e logs. Consulte `plan.md` para recomendações completas de variáveis de ambiente (`DATABASE_URL` / `POSTGRES_*`) e procedimentos de healthcheck.
- Variáveis de ambiente e segredos: nunca commitar `.env`. Use secret manager ou variáveis injetadas pelo runtime/CI. Se precisar checar a existência das variáveis no servidor, use os comandos de verificação descritos no `plan.md`.


Healthcheck e teste rápido

Exemplo rápido que o operador pode rodar (não inclui segredos):

```bash
# listar variáveis DATABASE no .env (operações no servidor)
grep -E "DATABASE_URL|POSTGRES_" /srv/SERVER_ORION/.env || true

# conectar e testar conexão (substituir DATABASE_URL se necessário)
python - <<'PY'
import os
import sys
try:
  import psycopg2
except Exception:
  print('psycopg2 não instalado; instale: pip install psycopg2-binary')
  sys.exit(1)
url = os.getenv('DATABASE_URL') or ''
if not url:
  print('DATABASE_URL não definida no ambiente — injetar variáveis antes de rodar o teste')
  sys.exit(2)
try:
  conn = psycopg2.connect(url, connect_timeout=5)
  cur = conn.cursor()
  cur.execute('SELECT 1')
  print('DB OK')
  cur.close(); conn.close()
except Exception as e:
  print('ERRO DB:', e)
  raise
PY
```

Observações de segurança

- Não copie/cole senhas em chats ou repositórios públicos.
- Para inspeção por terceiros, forneça apenas nomes de variáveis (ex.: `POSTGRES_PASSWORD`) sem revelar valores.


---

Quickstart (rápido)

1. Crie e ative um virtualenv, instale dependências:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r models/agents/polaris/requirements.txt  # ou instalar as libs listadas em TOOLS.md
```

2. Ajuste variáveis de ambiente (usar secret manager em produção). Exemplos mínimos:

```bash
export DATABASE_URL='postgresql://user:pass@db:5432/polaris'
export LLM_URL='http://localhost:8100'
export EMBEDDING_URL='http://embedding:8001'
```

3. Rodar healthchecks:

```bash
# validar DB
python -c "import os,psycopg2; print('OK' if os.getenv('DATABASE_URL') else 'NO_DB')"
# validar LLM
curl -sS ${LLM_URL:-http://localhost:8100}/v1/health || echo 'LLM unavailable'
```

4. Rodar migrations (exemplo com Alembic):

```bash
alembic upgrade head
```

5. Start POLARIS (exemplo local):

```bash
uvicorn polaris.app:app --host 0.0.0.0 --port 8002
```


