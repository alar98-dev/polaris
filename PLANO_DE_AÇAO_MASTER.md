# PLANO DE AÇÃO MASTER - AGENTE POLARIS

Este documento resume as principais funcionalidades e componentes que precisam ser implementados para que o agente POLARIS atinja sua capacidade operacional mínima, com base na documentação existente.

## ✅ 1. Extração Automática de Slots no Discovery

**Status:** Concluído

**O que falta:** Atualmente, o método `ask_discovery_questions` não extrai informações (slots) das mensagens do usuário. É necessário implementar um extrator que utilize um LLM para interpretar a resposta do cliente e preencher automaticamente os `slots` da sessão (ex: `pain`, `users`, `kpi`, `budget`).

**Ação:**
- Criar um método `_extract_slots_from_message(session, message)` em `polaris/agent_core.py`.
- Este método deve:
    - Montar um prompt para o LLM solicitando a extração dos dados em formato JSON.
    - Chamar o LLM (`call_llm`).
    - Validar e fazer o parse da resposta JSON.
    - Atualizar o dicionário `session['slots']` com os dados extraídos e a confiança da extração.
    - Integrar a chamada deste método no fluxo do `ask_discovery_questions`.

## 2. Integração com o Serviço de Embeddings para Recomendação

**Status:** Pendente

**O que falta:** A função `select_portfolio` atualmente retorna uma lista estática de exemplos. É preciso integrar o serviço de embeddings para realizar uma busca semântica real.

**Ação:**
- No método `select_portfolio` em `polaris/agent_core.py`:
    - Chamar o `embedding_adapter.get_embedding()` para vetorizar a consulta do usuário.
    - Usar o vetor gerado para chamar `embedding_adapter.search_vector()` e obter os projetos mais relevantes da base de conhecimento.
    - Mapear os resultados da busca para o formato de resposta esperado.
    - Manter o fallback estático apenas se o serviço de embedding estiver indisponível.

## 3. Health Check Completo

**Status:** Pendente

**O que falta:** O endpoint de `health_check` verifica apenas o status do LLM. É necessário expandi-lo para monitorar todas as dependências críticas.

**Ação:**
- Modificar a função `health_check` para incluir verificações de status para:
    - Serviço de Embeddings.
    - Conexão com o banco de dados (PostgreSQL).
    - Cache (Redis, se aplicável).
- O retorno deve ser um JSON detalhado com o status de cada componente.

## ✅ 4. Endpoints Auxiliares para Gerenciamento de Sessão

**Status:** Concluído

**O que falta:** Não há uma rota na API para consultar ou atualizar manualmente os `slots` de uma sessão, o que é útil para depuração e testes.

**Ação:**
- Adicionar um novo endpoint `PATCH /api/v1/sessions/{session_id}/slots` no arquivo `polaris/app.py`.
- Este endpoint deve aceitar um JSON e atualizar diretamente os `slots` da sessão correspondente.

## 5. Cobertura de Testes Automatizados

**Status:** Pendente

**O que falta:** O projeto não possui testes automatizados, o que é um risco para a manutenção e evolução do código.

**Ação:**
- Criar a estrutura de testes usando `pytest`.
- Implementar testes unitários e de integração para as funcionalidades críticas:
    - Teste de criação de sessão (`POST /api/v1/sessions`).
    - Teste do fluxo de discovery com extração de slots (mockando a chamada ao LLM).
    - Teste da seleção de portfólio (mockando o adaptador de embeddings).
    - Teste dos endpoints de geração de artefatos (`/prototype`, `/mocks`).

## 6. Documentação e Templates para LLMs

**Status:** Pendente

**O que falta:** Faltam templates de prompts e schemas de saída bem definidos para guiar as interações com os LLMs, garantindo respostas mais consistentes e fáceis de validar.

**Ação:**
- Criar um arquivo (`LLM_PROMPTS.md` ou similar) para documentar:
    - Os templates de prompt exatos para cada tarefa (extração de slots, geração de protótipo, etc.).
    - Os schemas JSON esperados como saída dos LLMs.
    - Exemplos de interações (few-shot examples) para melhorar a precisão do modelo.

## 7. Implementação do Schema SQL e Migrations

**Status:** Pendente

**O que falta:** O `SQL_SCHEMA.md` descreve a estrutura do banco de dados, mas a implementação via modelos SQLAlchemy e as migrações Alembic precisam ser criadas.

**Ação:**
- Criar o arquivo `polaris/sql_models.py` com as classes SQLAlchemy que mapeiam as tabelas (`projects`, `artifacts`, `artifact_chunks`, etc.).
- Inicializar o Alembic no projeto.
- Gerar a primeira migração (`alembic revision --autogenerate`) para criar o schema inicial no banco de dados.
