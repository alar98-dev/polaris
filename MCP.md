# MCP - Manual de Comunicação da API do Agente POLARIS

Este documento descreve como interagir com a API do agente POLARIS, com foco nas funcionalidades de discovery e extração de slots.

## 1. Visão Geral do Fluxo de Discovery

O fluxo de discovery conversacional com o POLARIS ocorre da seguinte forma:

1.  **Criação da Sessão**: O cliente inicia uma nova conversa e obtém uma `session_id`.
2.  **Interação e Extração de Slots**: O cliente envia mensagens para a sessão. A cada mensagem, o agente POLARIS processa o texto para extrair informações relevantes (slots), como a dor do cliente, o orçamento, o público-alvo, etc.
3.  **Seleção de Portfólio**: Com base nos slots preenchidos, o agente recomenda soluções do portfólio.
4.  **Geração de Artefatos**: Após a escolha do cliente, o agente gera os artefatos do projeto.

## 2. Endpoints da API

### 2.1. Criar uma nova sessão

- **Endpoint**: `POST /api/v1/sessions`
- **Descrição**: Inicia uma nova sessão de conversa.
- **Request Body**:
  ```json
  {
    "client_id": "identificador_do_cliente"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "session_id": "uuid_da_sessao",
    "slots": {},
    "history": []
  }
  ```

### 2.2. Enviar uma mensagem e acionar o Discovery

- **Endpoint**: `POST /api/v1/discovery`
- **Descrição**: Envia uma mensagem do usuário para a sessão. Esta ação aciona o processo de extração de slots. O agente analisará a `message` para preencher os `slots` da sessão.
- **Request Body**:
  ```json
  {
    "session_id": "uuid_da_sessao",
    "message": "A mensagem do usuário vai aqui. Por exemplo: 'Quero criar um e-commerce para vender sapatos, com um orçamento de R$ 50.000,00.'"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "next_question": "Qual é o público-alvo para esta loja de sapatos?",
    "slots": {
      "pain": "Criar um e-commerce para vender sapatos",
      "budget": "50000",
      "users": null,
      "kpi": null
    },
    "recommendations": [],
    "complete": false
  }
  ```

### 2.3. Atualizar/Forçar Slots Manualmente

- **Endpoint**: `PATCH /api/v1/sessions/{session_id}/slots`
- **Descrição**: Permite a atualização manual dos slots de uma sessão. Útil para testes, depuração ou para integrar com sistemas externos que já possuam algumas dessas informações.
- **Request Body**: Um objeto JSON contendo os `slots` a serem atualizados.
  ```json
  {
    "budget": "75000",
    "kpi": "Aumentar a conversão em 20%"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "session_id": "uuid_da_sessao",
    "slots": {
      "pain": "Criar um e-commerce para vender sapatos",
      "budget": "75000",
      "users": null,
      "kpi": "Aumentar a conversão em 20%"
    },
    "history": [...]
  }
  ```

## 3. Estrutura dos Slots

Os `slots` são as informações estruturadas que o agente extrai da conversa. O objetivo é preencher o máximo de campos possível para qualificar a necessidade do cliente.

**Schema de Slots (Exemplo):**

```json
{
  "pain": "A dor ou necessidade principal do cliente (string, ex: 'Preciso de um sistema de gestão de estoque').",
  "users": "Descrição do público-alvo (string, ex: 'Pequenos varejistas com pouca experiência técnica').",
  "kpi": "O principal indicador de sucesso do projeto (string, ex: 'Reduzir o tempo de inventário em 50%').",
  "budget": "O orçamento disponível (string, ex: '100000').",
  "deadline": "O prazo desejado (string, ex: '3 meses').",
  "restrictions": "Restrições técnicas ou de negócio (string, ex: 'Deve integrar com nosso ERP atual via API REST')."
}
```

## 4. Contrato com o LLM para Extração de Slots

Para que a extração funcione, o agente POLARIS fará uma chamada a um modelo de linguagem (LLM) com um prompt específico.

- **Prompt Template (Exemplo)**:
  ```
  Dada a mensagem do usuário, extraia as seguintes informações em um objeto JSON: 'pain', 'users', 'kpi', 'budget'. Retorne apenas o JSON. Se um campo não for encontrado, use o valor null.

  Mensagem: "{message}"
  ```

- **Resposta JSON esperada do LLM**:
  ```json
  {
    "pain": "Criar um e-commerce para vender sapatos",
    "users": null,
    "kpi": null,
    "budget": "50000"
  }
  ```
A resposta do LLM é então utilizada para atualizar os `slots` da sessão.
