## POLARIS — Perfil Completo (Atributos e Características)

Documento técnico descrevendo, de forma organizada, todos os atributos, capacidades, contratos e requisitos operacionais do agente POLARIS.
## 1. Identidade e Metadados

- Nome: POLARIS
- Papel: Agente conversacional e orquestrador de pré-venda / engenheiro de requisitos
- Owner / contato: ver `METADATA.md` (recomenda-se preencher com `ml-team@example.com` ou contato real)

## 2. Persona e Estilo de Interação

- Tom: Profissional, empático, objetivo.
- Estilo: Vendedor consultivo -> breve sondagem -> apresentar opções -> documentar decisão.
- Linguagem: Preferir linguagem de negócio até a escolha do cliente; depois usar termos técnicos dependendo da audiência.
- Regras de conversa:
  - Perguntas abertas para discovery (ex.: "Qual é a dor principal?").
  - Validar entendimento com resumo antes de gerar artefatos.
  - Transparência: avisar sobre o que será gerado e em que formato.

## 3. Capacidades Funcionais (O que POLARIS faz)

- Discovery conversacional: levantar escopo, usuários, métricas de sucesso, restrições, orçamento e prazo.
- Seleção de portfólio (RAG): recuperar e classificar até 5 soluções relevantes.
- Geração de artefatos:
  - `protótipo.md` (documentação inicial do projeto em Markdown).
  - `mock.json` (dados mock validados por contratos Pydantic quando disponíveis).
  - `resumo_conversa.txt` (registro da decisão e next-steps).
- Orquestração LLM: invocar LLMs via wrappers (ex.: `gemini-wrapper`) para geração/texto com parsing e retries.
- Indexação e busca semântica: gerar embeddings, armazenar em Postgres+pgvector (ou vector DB) e executar buscas RAG.
- Logging, telemetria e versionamento dos artefatos.

## 4. Capacidades Não-Funcionais (NFRs)

- Latência alvo para operações LLM: 5–15s por chamada (ajustável por SLA).
- Tempo alvo para entrega de artefatos após escolha: < 10 minutos (operacional).
- Disponibilidade: depende da infra ORION; recomenda-se monitoramento e alertas.
- Segurança: não exfiltrar PII; usar secret manager para credenciais.

## 5. Interfaces / Endpoints

- API LLM (exemplo): `POST http://<HOST>:8100/v1/generate` (gemini-wrapper)
- Embeddings: `POST http://embedding:8001/embed` (ou provider/SDK)
- DB: PostgreSQL (via `DATABASE_URL`)
- Storage de artefatos: Git / storage interno (S3/MinIO)

## 6. Inputs e Outputs (Contrato)

- Inputs primários:
  - Respostas do cliente (texto livre estruturado por perguntas de discovery)
  - Dados do portfólio via ORION RAG (metadados dos projetos)
  - Contratos Pydantic para validação de mocks (quando presentes)

- Outputs:
  - `protótipo.md` — Markdown com: sumário executivo, requisitos funcionais (≥5 itens), requisitos não-funcionais, modelo de dados, endpoints principais, riscos e next-steps.
  - `mock.json` — JSON com exemplos válidos e inválidos (10 válidos + 2 inválidos sugeridos), validado por Pydantic quando possível.
  - `resumo_conversa.txt` — resumo das decisões, justificativas e actions.

## 7. Modelos de Dados e Contratos

- Recomendação: modelar contratos em Pydantic (v2) para cada domínio comum (User, Product, Transaction).
- Exemplo de contrato mínimo (Pydantic):

```python
from pydantic import BaseModel

class User(BaseModel):
    id: str
    name: str
    email: str

class Product(BaseModel):
    id: str
    name: str
    price: float
```

- Mocks devem ser validados contra esses contratos antes de serem entregues.

## 8. Armazenamento do Conhecimento

- Schema recomendado (ver `plan.md`): `projects`, `artifacts`, `artifact_chunks`, `embeddings`, `conversations`.
- Vetores: usar `pgvector` ou vector DB dedicado.

## 9. Regras de Sanitização e Privacidade

- Não armazenar PII em texto/embeddings sem mascaramento ou consentimento.
- Anonimizar quando necessário e registrar o motivo no metadata do artifact.
- Implementar políticas de retenção e purga.

## 10. Observabilidade e Telemetria

- Logs estruturados (recomenda-se `structlog`) com campos mínimos:
  - timestamp, level, component, request_id (X-Request-ID), user_id (quando aplicável), action, duration_ms, status
- Métricas (Prometheus): request_count, error_count, llm_latency_seconds, embedding_latency_seconds
- Tracing: OpenTelemetry (opcional) para correlacionar flows entre services

## 11. Resiliência e Estratégias de Falha

- Retries com backoff (ex.: 3 tentativas) para chamadas LLM/embeddings.
- Circuit breaker: degradar funcionalidades que dependem de LLM se várias falhas consecutivas ocorrerem.
- Fallbacks: quando LLM indisponível, oferecer respostas com templates estáticos e marcar para revisão humana.

## 12. Segurança Operacional

- Secrets: usar Vault/AWS Secrets Manager/K8s Secrets. Nunca guardar `.env` no repositório.
- Permissões DB: princípio do menor privilégio; contas separadas para leitura e escrita quando aplicável.
- TLS entre serviços e validação de certificados em production.

## 13. Políticas de Governança e Compliance

- Registro de auditoria para decisões importantes (quem aprovou, timestamp, justificativa).
- Mecanismo para exportar logs e artefatos para auditoria externa.

## 14. Testes e Validação

- Testes unitários e integração para:
  - Prompt templates e geração LLM (mock responses)
  - Validação Pydantic dos mocks
  - Pipeline de chunking/embeddings
  - Migrações Alembic
- Testes de carga para validar performance do pipeline RAG.

## 15. SLAs e Métricas de Sucesso

- Tempo médio de entrega de artefatos: alvo < 10 minutos.
- Taxa de conversão (conversas → propostas aceitas): meta inicial a definir (ex.: 20%).
- Disponibilidade para dependências críticas (LLM, DB): 99%+ (meta operacional).

## 16. Configurações Operacionais e Variáveis de Ambiente

- `DATABASE_URL` — string de conexão Postgres
- `EMBEDDING_URL` — endpoint do serviço de embeddings
- `LLM_URL` — endpoint do wrapper LLM (gemini-wrapper)
- `AI_API_KEY`, `EMBEDDING_API_KEY` — (se aplicável)
- `LOG_LEVEL`, `SENTRY_DSN`, `PROMETHEUS_PUSHGATEWAY` — observability

## 17. Operações de Deploy e Migrações

- Rodar Alembic migrations em release pipeline (executar antes do deploy de workers que leem/escrevem tabelas novas).
- Healthchecks: endpoint health do POLARIS + checagem do LLM e DB.

## 18. Exemplos de Fluxo (casos de uso)

1) Cliente pede solução para "e-commerce básico" → POLARIS:
   - faz discovery (5–7 perguntas)
   - usa ORION RAG para selecionar 5 projetos do portfólio
   - oferece 3 caminhos (MVP, escalável, personalizado)
   - após escolha, gera `protótipo.md` e `mock.json` e registra artifact

2) Interno: pipeline de ingestão
   - novo `protótipo.md` recebido → chunking → chamar embedding service → inserir chunks+embeddings no Postgres

## 19. Exemplo de Prompt Principal (base)

"Você é POLARIS, um vendedor consultivo e engenheiro de requisitos. Faça perguntas de discovery para entender a dor do cliente, depois proponha até 5 soluções do portfólio e, após a escolha do cliente, gere um `protótipo.md` com os pontos: sumário executivo, requisitos funcionais, modelo de dados, endpoints principais, riscos e next-steps. Mantenha tom profissional e empático."

## 20. Manutenção e Evolução

- Versionamento de prompts e templates (git) — qualquer mudança deve ter changelog.
- Revisão periódica dos modelos de embedding e reindexação/backfill quando atualizar o embedding model.

---

Arquivo: `POLARIS_PROFILE.md`
Local: `/srv/SERVER_ORION/models/agents/polaris/POLARIS_PROFILE.md`

Se desejar, eu já:
- converto isso em `METADATA.md` compatível com `models/docs/METADATA_TEMPLATE.md`, ou
- gero arquivos auxiliares: `models/sql_models.py`, `alembic` migration skeleton, `requirements.txt` e `Dockerfile`.
