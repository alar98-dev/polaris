## POLARIS — Plano do Agente

Descrição formal do agente e plano operativo para uso interno da agência ORION.

## Quem é

POLARIS é um Agente de Inteligência Artificial conversacional e autônomo, integrante da arquitetura ORION (a "Server IA" da agência). Atua como ponto de contato inicial, guia estratégico e gerador de artefatos para pré-venda e início de projetos.

## Descrição

POLARIS funciona como um vendedor consultivo e engenheiro de requisitos automatizado. Seu objetivo é reduzir o atrito entre a visão do cliente e a entrega técnica da agência. Ele combina capacidades conversacionais (discovery, qualificação, empatia) com produção técnica (documentação de protótipo em Markdown, mocks JSON validados por contratos Pydantic).

## Qual sua função

- Realizar discovery e qualificação do cliente.
- Mapear necessidades de negócio para requisitos técnicos claros.
- Selecionar e propor até 5 soluções/projetos do portfólio da agência mais adequados ao cliente (RAG sobre base ORION).
- Após escolha do cliente, gerar imediatamente os artefatos iniciais: documentação do protótipo (Markdown) e um mock de dados (JSON validado).
- Acelerar o ciclo de vendas ao entregar artefatos prontos para início do desenvolvimento.

## Quais suas características

O POLARIS combina características de interação e técnicas:

### 1) Características de interação (o vendedor)

- Inteligência conversacional: condução de diálogo fluido, perguntas de sondagem e validação contínua.
- Empatia digital: tom profissional, paciente, evitando jargões até a fase técnica.
- Foco em resultado: direciona a conversa para soluções viáveis e prioriza eficiência.
- Transparência: explica o processo ao cliente (o que será entregue e em que formato).

### 2) Características técnicas (o engenheiro)

- Especialista em requisitos: converte linguagem de negócio em especificações técnicas.
- Acesso ao conhecimento (RAG): consulta a base ORION para selecionar itens do portfólio.
- Geração estruturada: entrega Markdown e JSON de alta fidelidade, prontos para o time de desenvolvimento.
- Velocidade: gera os artefatos imediatamente após confirmação do cliente.

## Fluxo do cliente com POLARIS

1. Entrada: cliente inicia contato (site/chat/etc.).
2. Sondagem: POLARIS faz perguntas de discovery (escopo, público, métricas de sucesso, orçamento, restrições).
3. Proposta: POLARIS sugere as 5 melhores soluções do portfólio.
4. Decisão: cliente escolhe uma opção.
5. Entrega: POLARIS gera Documentação Técnica (Markdown) e Mock de Dados (JSON), prontos para desenvolvimento.

Obs: o agente deve registrar a conversa e os artefatos em um repositório interno ligado à ORION para rastreabilidade (logs e versão dos artefatos).

## Artefatos gerados

- Documento de Protótipo (Markdown): visão geral do projeto, requisitos funcionais e não funcionais, endpoints/integrações principais, modelos de dados, wireframes ou links para protótipos.
- Mock de Dados (JSON): conjunto de amostras de dados conformes aos contratos Pydantic, incluindo exemplos válidos e exemplos de erro quando relevante.
- Registro de Conversa/Decisão: resumo em texto com os motivos e opções apresentadas.

## Contrato (Inputs / Outputs / Erros)

- Inputs esperados:
  - Respostas do cliente a perguntas de discovery (texto estruturado livre).
  - Acesso RAG ao portfólio/KB ORION (metadados dos projetos: tags, orçamento estimado, time necessário).
  - Modelos Pydantic (contratos) para validar mocks JSON.

- Outputs produzidos:
  - `protótipo.md` (Markdown com a documentação inicial).
  - `mock.json` (JSON validado contra o contrato).
  - `resumo_conversa.txt` (resumo com decisões e next-steps).

- Modo de erro / falhas:
  - Falta de dados do cliente: solicitar clarificação com perguntas direcionadas.
  - Falta de contrato Pydantic para um domínio: gerar um mock genérico e marcar como "requer contrato".
  - Inconsistência na base ORION: registrar e notificar curador/operador.

## Casos de borda e riscos

- Cliente com escopo muito amplo/indefinido: POLARIS deve convergir priorizando MVP e métricas de sucesso.
- Dados sensíveis: não incluir PII em mocks; mascarar e sinalizar quando necessário.
- Requisitos regulamentares (LGPD, GDPR, etc.): destacar nas restrições e acionar compliance.
- Orçamento irrealista: comunicar limites e apresentar alternativas escaláveis.

## Critérios de aceitação / sucesso

- O `protótipo.md` contém: sumário executivo, requisitos funcionais (mínimo 5 itens), mapa de dados/entidades, endpoints-chave, e um plano de next-steps (3 itens).
- O `mock.json` passa na validação do(s) modelo(s) Pydantic disponíveis ou é acompanhado de um aviso se o contrato estiver ausente.
- Tempo de entrega do artefato: objetivo de < 10 minutos após a escolha do cliente (tempo operacional alvo).

## Exemplos de prompt e templates (uso interno)

- Prompt de discovery (template):
  - "Olá! Para eu entender melhor, qual é a dor principal que você quer resolver? Quem são os usuários-alvo? Qual o orçamento aproximado e o prazo desejado?"

- Template de instrução para geração de `protótipo.md`:
  - Incluir sumário executivo (1 parágrafo), requisitos funcionais e não-funcionais, proposta de MVP, modelo de dados (exemplo), endpoints principais, riscos e next-steps.

- Template para `mock.json`:
  - Gerar 10 exemplos válidos + 2 exemplos inválidos (caso aplicável) com campos-chave e tipos coerentes.

## Métricas e telemetria

- Taxa de conversão (conversas iniciadas → propostas aceitas).
- Tempo médio entre escolha e entrega de artefatos.
- Qualidade dos artefatos medida por checklist (completeness score).

## Integração e operacionais

- Integração com ORION RAG para o portfólio e com repositório de artefatos (ex.: storage interno/Git).
- Hooks para operador humano revisar artefatos antes do envio (opcional, por SLA).
- Logs e versionamento dos artefatos por interação.

## Infraestrutura: PostgreSQL (servidor)

O ambiente de produção/piloto usará o PostgreSQL já existente no servidor ORION. Regras e recomendações operacionais:

- Localização do serviço: utilizar o banco PostgreSQL hospedado no servidor ORION (URI interna).
- Variáveis de ambiente esperadas (padrões recomendados):
  - `DATABASE_URL` (preferencial) — ex.: `postgresql://user:password@host:port/dbname`
  - Ou individualmente: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`.
- Segurança de segredos:
  - NÃO comitar o arquivo `.env` contendo senha no repositório.
  - Use um secret manager (Vault, AWS Secrets Manager, etc.) ou variáveis de ambiente do serviço/CI para provisionamento em produção.
  - Em ambientes locais, manter `.env` em diretório fora do controle de versão e com permissões restritas.
- Conexão e migrações:
  - Use `DATABASE_URL` para configuração de runtime e ferramentas de migração (Alembic, Django migrations, Flyway, etc.).
  - Validar a conexão com um pequeno script/healthcheck antes de iniciar o agente:
    - conectar com pool limitado (ex.: max_connections=5), executar `SELECT 1`.
    - rodar migrações em modo transacional/lock-safe.
- Boas práticas operacionais:
  - Aplicar TLS/SSL entre a aplicação e o banco se houver comunicação por rede pública ou atravessando sub-redes não confiáveis.
  - Criar contas de DB com privilégios mínimos para as operações do POLARIS (separar conta de leitura/escrita quando aplicável).
  - Habilitar monitoramento (métricas de conexão, latência de queries, locks) e alertas.

Nota sobre verificação da senha no `.env` do servidor ORION:

- Eu não tenho acesso direto ao arquivo `/srv/SERVER_ORION/.env` a partir deste workspace (restrição de leitura do ambiente). Portanto, não posso extrair ou exibir a senha aqui.
- Se você quiser que eu verifique a presença e o nome exato da variável (por exemplo, `DATABASE_URL` ou `POSTGRES_PASSWORD`), você pode:
  1. Copiar/colar aqui as linhas relevantes do `.env` sem expor a senha (por exemplo, só o nome da variável), ou
  2. Conceder acesso ao `.env` dentro do workspace (movendo/ligando o arquivo) ou me pedir para executar um comando local que verifique a existência (eu posso sugerir o comando a executar no servidor).

Exemplo de passos rápidos para validar a DB no servidor (para o operador executar):

```bash
# Verificar variáveis de ambiente (exemplo; não exibe senha caso esteja exportada apenas no ambiente)
grep -E "DATABASE_URL|POSTGRES_" /srv/SERVER_ORION/.env || true

# Teste simples de conexão (substitua pelo DATABASE_URL adequado)
python - <<'PY'
import os
import psycopg2
url = os.getenv('DATABASE_URL') or 'postgresql://user:password@host:5432/dbname'
try:
    conn = psycopg2.connect(url, connect_timeout=5)
    cur = conn.cursor()
    cur.execute('SELECT 1')
    print('OK')
    cur.close(); conn.close()
except Exception as e:
    print('CONN_ERROR', e)
    raise
PY
```

Adicionar isto ao plano: quando quisermos validar automaticamente na pipeline, usar um job de `healthcheck` que execute o teste acima com variáveis injetadas pelo CI/CD.

## Integração LLM: gemini-wrapper

Descrição rápida

O servidor roda um wrapper HTTP para o LLM chamado `gemini-wrapper`, exposto em `http://<HOST>:8100`. POLARIS deve consumir esse endpoint para gerar texto/infra de conversação quando necessário.

EndPoints

- Generate: `POST http://<HOST>:8100/v1/generate` — corpo JSON com `prompt` (string) e parâmetros opcionais (`max_tokens`, `temperature`).
- Health: `GET http://<HOST>:8100/v1/health` — retorna status do wrapper/LLM.

Recomendações de configuração

- Se POLARIS roda no mesmo host/container: prefira `http://127.0.0.1:8100/v1/generate` ou `http://localhost:8100/v1/generate`.
- Se POLARIS roda em outro host na mesma rede: use a IP/hostname interno (ex.: `http://10.0.0.5:8100/v1/generate`).
- Use `X-Request-ID` em todos os requests para rastreabilidade.
- Inclua headers de `Authorization` quando aplicável (configured by infra). Não envie secrets no body.

Payload e resposta

- Request (exemplo):

  {
  "prompt": "Explique IA em 2 linhas",
  "max_tokens": 100,
  "temperature": 0.2
  }

- Response esperada (exemplo):

  {
  "id": "...",
  "text": "Resposta como string ou objeto",
  "latency_ms": 123,
  "usage": {...}
  }

- Observação importante: `text` pode ser uma `string` ou um `object` com `parts` (alguns providers retornam estrutura). POLARIS deve normalizar ambos os casos:
  - Se `text` for string -> usar diretamente.
  - Se `text` for objeto com `parts` -> concatenar/pegar o primeiro `part` textual.

Exemplo de parsing em pseudocódigo

  resp = requests.post(url, json=payload, headers=hdrs, timeout=timeout)
  body = resp.json()
  t = body.get('text')
  if isinstance(t, str):
    text = t
  elif isinstance(t, dict) and 'parts' in t:
    # parts pode ser lista de strings/objetos
    parts = t.get('parts') or []
    if parts and isinstance(parts[0], str):
      text = parts[0]
    elif parts and isinstance(parts[0], dict) and 'text' in parts[0]:
      text = parts[0]['text']
    else:
      text = json.dumps(t)
  else:
    text = str(t)

Resiliência e performance

- Timeouts: definir timeout baixo por request (ex.: 5–15s) e ajustar por SLA.
- Retries: aplicar retry com backoff exponencial (3 tentativas padrão).
- Rate limiting / concurrency: monitorar QPS e usar um pool de reqs com limite (ex.: max_workers=10) para evitar saturar o wrapper.
- Circuit breaker: após N falhas consecutivas, entrar em degraded mode e informar operador.

Healthcheck

- Periodicamente (job de heartbeat) chamar `GET /v1/health` e registrar latência/uptime.
- Em startup, validar `health` antes de aceitar requisições que dependam do LLM.

Exemplo mínimo em Python (requests)

```python
import requests
import uuid
import time

URL = 'http://127.0.0.1:8100/v1/generate'

def call_llm(prompt, max_tokens=200, temperature=0.2, timeout=10):
  headers = {'X-Request-ID': str(uuid.uuid4()), 'Content-Type': 'application/json'}
  payload = {'prompt': prompt, 'max_tokens': max_tokens, 'temperature': temperature}
  for attempt in range(3):
    try:
      r = requests.post(URL, json=payload, headers=headers, timeout=timeout)
      r.raise_for_status()
      body = r.json()
      text = None
      t = body.get('text')
      if isinstance(t, str):
        text = t
      elif isinstance(t, dict):
        parts = t.get('parts') or []
        if parts:
          part = parts[0]
          text = part if isinstance(part, str) else part.get('text')
        else:
          text = str(t)
      else:
        text = str(t)
      return {'ok': True, 'text': text, 'meta': body}
    except requests.RequestException as e:
      wait = (2 ** attempt) * 0.5
      time.sleep(wait)
  return {'ok': False, 'error': 'failed after retries'}
```

Instrumentação

- Registre latência (`latency_ms`), token usage (se retornado), request id e status code.
- Correlacione logs entre POLARIS, embedding service e wrapper via `X-Request-ID`.

Segurança e saneamento

- Sanitize inputs: limite de tamanho do prompt (ex.: 8k chars), remova PII antes de enviar quando aplicável.
- Não enviar dados sensíveis ou PII sem aprovação/compliance.

Observações finais

- O wrapper pode retornar diferentes shapes dependendo do provider; POLARIS deve ser tolerante e ter um adaptador (adapter layer) para normalizar respostas.
- Para testes locais, configure `URL` para `http://localhost:8100` e use o healthcheck antes de start.

## Representação do Conhecimento: SQL + Embeddings (SQLAlchemy & Alembic)

Objetivo

Descrever como POLARIS irá representar, armazenar e buscar conhecimento (documentos, artefatos, trechos de conversas, metadados do portfólio) usando SQL (PostgreSQL) e embeddings. Implementação recomendada: modelos de dados em SQLAlchemy e migrações com Alembic; vetores armazenados em Postgres com a extensão `pgvector` quando possível.

Por que usar SQL + embeddings

- Persistência transacional, flexibilidade para consultas relacionais e histórico de artefatos.
- Embeddings para buscas semânticas (RAG) combinadas com filtros relacionais (metadados) oferecem precisão e governança.

Schema recomendado (alto nível)

- `projects` — metadados do portfólio (id, title, tags, estimated_budget, stack, created_at)
- `artifacts` — artefatos gerados (id, project_id, type (protótipo/mock/conversation), content, language, metadata JSON, created_at)
- `artifact_chunks` — chunks de `artifacts` (id, artifact_id, chunk_index, text)
- `embeddings` — tabela de embeddings (id, chunk_id, vector, model_name, vector_dim, created_at)
- `conversations` — registro de interações (id, client_id, transcript, summary, created_at)

Observação: `embeddings.vector` deve usar `pgvector` (type: vector) para consultas de similaridade nativas. Se `pgvector` não estiver disponível, armazenar como JSON/bytea e usar um serviço de vector search externo.

SQLAlchemy — modelo exemplo (resumido)

```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship, declarative_base
from pgvector.sqlalchemy import Vector
import datetime

Base = declarative_base()

class Artifact(Base):
    __tablename__ = 'artifacts'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    type = Column(String, nullable=False)
    content = Column(String)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    chunks = relationship('ArtifactChunk', back_populates='artifact')

class ArtifactChunk(Base):
    __tablename__ = 'artifact_chunks'
    id = Column(Integer, primary_key=True)
    artifact_id = Column(Integer, ForeignKey('artifacts.id'))
    chunk_index = Column(Integer)
    text = Column(String)
    embedding = Column(Vector(1536))  # ajustar dim conforme modelo
    artifact = relationship('Artifact', back_populates='chunks')
```

Alembic

- Gerar migração inicial com a criação das tabelas acima.
- Incluir comando de instalação/checagem da extensão `pgvector` quando for usar vetores nativos:

  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

- Criar índices para aceleração (ex.: `hnsw` ou `l2` index conforme `pgvector`):

  ```sql
  -- exemplo
  CREATE INDEX ON artifact_chunks USING hnsw (embedding vector_l2_ops);
  ```

Ingestão (pipeline)

1. Normalização e chunking: ao gerar/receber um artefato (documento/protótipo/transcript), normalizar texto e dividi-lo em chunks (ex.: 200–500 tokens) com referência a `artifact_id` e `chunk_index`.
2. Geração de embedding: chamar o serviço de embeddings (ex.: `http://embedding:8001/embed`) para cada chunk.
3. Upsert em SQL: inserir/atualizar `artifact_chunks` com o `text` e o `embedding` (vetor). Usar transação para consistência.
4. Deduplicação: calcular fingerprint (hash) do chunk para evitar reinserções desnecessárias.

Query de similaridade (exemplo SQL com pgvector)

```sql
SELECT ac.id, ac.text, 1 - (ac.embedding <#> $query_embedding) AS similarity
FROM artifact_chunks ac
WHERE ac.metadata->>'lang' = 'pt'
ORDER BY ac.embedding <=> $query_embedding
LIMIT 10;
```

Notas de implementação

- Dimensão do vetor: alinhar ao embedding model (ex.: 1536, 1024).
- Normalização de texto: limpar HTML, remover excesso de whitespace, opcionalmente aplicar stemming/lemmatization antes de chunking.
- Atualizações: quando o artifact mudar, re-gerar e atualizar chunks/embeddings atomically.
- Backfill: criar job de backfill para processar artefatos antigos e gerar embeddings.

Considerações de segurança e privacidade

- Não armazenar PII em texto/embeddings sem mascaramento. Armazene apenas metadados autorizados.
- Implementar políticas de expurgo (retention) e logs de acesso para auditoria.

Validação e testes

- Cobertura unitária para:
  - geração/armazenamento de embeddings,
  - normalização/chunking,
  - consultas de similaridade (mockando vetores),
  - migrações Alembic.

Observação operacional

- Se a carga de RAG crescer muito, avaliar um vector DB dedicado (Pinecone, Milvus, Weaviate) e manter Postgres para metadados relacionais.


## Próximos passos (recomendações)

1. Definir o portfólio canônico da agência e modelar metadados consumíveis pela ORION (tags, orçamento, tempo, stack).
2. Entregar os contratos Pydantic mínimos para os domínios mais comuns (ex.: usuário, produto, transação) para que os mocks sejam validados.
3. Implementar o primeiro fluxo piloto com supervisão humana e telemetria ativada.
4. Criar prompt principal (prompt-engineered) e um conjunto de exemplos de conversa (few-shot) para treinamento fino do comportamento.

---

Arquivo: `plan.md`
Local: `/srv/SERVER_ORION/models/agents/POLARIS/plan.md`

Se quiser, eu já gero: 1) o prompt principal do POLARIS, 2) um `protótipo.md` de exemplo e 3) um `mock.json` com base em um dos projetos do portfólio — indique qual projeto ou descreva um cenário de cliente e eu crio os artefatos imediatamente.
