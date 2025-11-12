# POLARIS Agent API - Instruções de Uso

Este documento descreve como usar a API REST do agente POLARIS via FastAPI. O POLARIS é um agente de IA projetado para auxiliar no desenvolvimento de software, desde descoberta de requisitos até geração de protótipos e estimativas.

## Pré-requisitos

- Python 3.8+
- Dependências instaladas: `pip install -r requirements.txt`
- Servidor rodando: `uvicorn polaris.app:app --host 0.0.0.0 --port 8000`

## Base URL

```
http://localhost:8000/api/v1
```

## Autenticação

Atualmente, a API não requer autenticação (desenvolvimento). Em produção, implemente autenticação adequada.

## Endpoints

### 1. Health Check

Verifica o status do agente e suas dependências.

**Endpoint:** `GET /health`

**Resposta:**
```json
{
  "ok": true,
  "components": {
    "llm": {
      "ok": true,
      "status_code": 200
    }
  }
}
```

**Exemplo de uso:**
```bash
curl http://localhost:8000/api/v1/health
```

### 2. Criar Sessão

Inicia uma nova sessão de conversa com o agente.

**Endpoint:** `POST /sessions`

**Request Body:**
```json
{
  "client_id": "cliente123",
  "metadata": {
    "source": "web",
    "user_agent": "Mozilla/5.0"
  }
}
```

**Resposta:**
```json
{
  "session_id": "sess_abc123"
}
```

**Exemplo de uso:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"client_id": "teste"}'
```

### 3. Discovery (Descoberta de Requisitos)

Envia mensagens para o agente descobrir requisitos do projeto.

**Endpoint:** `POST /discovery`

**Request Body:**
```json
{
  "session_id": "sess_abc123",
  "message": "Quero desenvolver um app de delivery de comida"
}
```

**Resposta:**
```json
{
  "next_question": "Qual é o seu orçamento aproximado?",
  "slots": {
    "pain": "Preciso de um app de delivery",
    "users": "Clientes finais",
    "budget": null
  },
  "complete": false,
  "actions": [
    {
      "type": "portfolio_suggestion",
      "data": {
        "candidates": [
          {
            "id": 1,
            "title": "E-commerce Platform",
            "score": 0.85,
            "rationale": "Similar user base and functionality"
          }
        ]
      }
    }
  ]
}
```

**Exemplo de uso:**
```bash
curl -X POST http://localhost:8000/api/v1/discovery \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_abc123",
    "message": "Preciso reduzir churn em meu app mobile"
  }'
```

### 4. Atualizar Slots da Sessão

Atualiza manualmente os slots de uma sessão (útil para debug).

**Endpoint:** `PATCH /sessions/{session_id}/slots`

**Request Body:**
```json
{
  "budget": "50000",
  "kpi": "retenção de usuários"
}
```

**Resposta:**
```json
{
  "session_id": "sess_abc123",
  "slots": {
    "budget": "50000",
    "kpi": "retenção de usuários"
  }
}
```

### 5. Gerar Protótipo

Gera um protótipo baseado na escolha do portfólio.

**Endpoint:** `POST /prototype`

**Request Body:**
```json
{
  "session_id": "sess_abc123",
  "choice_id": 1,
  "context": {
    "additional_requirements": "Deve ser responsivo"
  }
}
```

**Resposta:**
```json
{
  "artifact": {
    "type": "prototype",
    "content": "Código HTML/CSS/JS do protótipo...",
    "metadata": {
      "framework": "React",
      "components": ["Header", "ProductList", "Cart"]
    }
  }
}
```

### 6. Gerar Mocks

Gera dados mock para testes.

**Endpoint:** `POST /mocks`

**Request Body:**
```json
{
  "session_id": "sess_abc123",
  "contract_name": "User",
  "context": {
    "fields": ["name", "email", "age"]
  },
  "count": 5
}
```

**Resposta:**
```json
{
  "mocks": [
    {
      "name": "João Silva",
      "email": "joao@example.com",
      "age": 30
    },
    {
      "name": "Maria Santos",
      "email": "maria@example.com",
      "age": 25
    }
  ]
}
```

### 7. Estimar Desenvolvimento

Estima tempo e custo de desenvolvimento.

**Endpoint:** `POST /estimate`

**Request Body:**
```json
{
  "session_id": "sess_abc123",
  "features": [
    "Autenticação de usuário",
    "Sistema de pedidos",
    "Integração com pagamento",
    "Dashboard admin"
  ]
}
```

**Resposta:**
```json
{
  "total_hours": 320,
  "breakdown": [
    {
      "feature": "Autenticação de usuário",
      "hours": 80,
      "complexity": "medium"
    }
  ],
  "t_shirt": "L"
}
```

### 8. Chat Conversacional

Endpoint para conversa livre com o agente.

**Endpoint:** `POST /chat`

**Request Body:**
```json
{
  "message": "Como posso melhorar a performance do meu app?",
  "session_id": "sess_abc123"
}
```

**Resposta:**
```json
{
  "response": "Para melhorar a performance, considere otimizar imagens, implementar cache e usar lazy loading.",
  "session_id": "sess_abc123"
}
```

## Fluxo Típico de Uso

1. **Criar Sessão**
   ```bash
   SESSION_ID=$(curl -s -X POST http://localhost:8000/api/v1/sessions \
     -H "Content-Type: application/json" \
     -d '{"client_id": "cliente123"}' | jq -r .session_id)
   ```

2. **Discovery Iterativo**
   ```bash
   # Primeira mensagem
   curl -X POST http://localhost:8000/api/v1/discovery \
     -H "Content-Type: application/json" \
     -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"Quero um app de e-commerce\"}"

   # Responder perguntas até complete=true
   curl -X POST http://localhost:8000/api/v1/discovery \
     -H "Content-Type: application/json" \
     -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"Orçamento de R$ 100.000\"}"
   ```

3. **Gerar Artefatos**
   ```bash
   # Protótipo
   curl -X POST http://localhost:8000/api/v1/prototype \
     -H "Content-Type: application/json" \
     -d "{\"session_id\": \"$SESSION_ID\", \"choice_id\": 1}"

   # Mocks
   curl -X POST http://localhost:8000/api/v1/mocks \
     -H "Content-Type: application/json" \
     -d "{\"session_id\": \"$SESSION_ID\", \"contract_name\": \"Product\", \"count\": 10}"

   # Estimativa
   curl -X POST http://localhost:8000/api/v1/estimate \
     -H "Content-Type: application/json" \
     -d "{\"session_id\": \"$SESSION_ID\", \"features\": [\"login\", \"checkout\"]}"
   ```

## Uso em Python

```python
import httpx
import asyncio

BASE_URL = "http://localhost:8000/api/v1"

async def use_polaris():
    async with httpx.AsyncClient() as client:
        # Criar sessão
        response = await client.post(f"{BASE_URL}/sessions", json={"client_id": "python_client"})
        session_id = response.json()["session_id"]
        
        # Discovery
        response = await client.post(f"{BASE_URL}/discovery", json={
            "session_id": session_id,
            "message": "Preciso de um sistema de gestão de tarefas"
        })
        data = response.json()
        print(f"Próxima pergunta: {data['next_question']}")
        print(f"Slots preenchidos: {data['slots']}")
        
        # Chat
        response = await client.post(f"{BASE_URL}/chat", json={
            "session_id": session_id,
            "message": "Como implementar autenticação?"
        })
        print(f"Resposta: {response.json()['response']}")

# Executar
asyncio.run(use_polaris())
```

## Tratamento de Erros

A API retorna códigos HTTP padrão:

- `200`: Sucesso
- `400`: Bad Request (dados inválidos)
- `404`: Not Found (sessão não existe)
- `502`: Bad Gateway (erro no LLM)

**Exemplo de erro:**
```json
{
  "detail": "session not found"
}
```

## Documentação Interativa

Para documentação interativa com Swagger UI, acesse:
```
http://localhost:8000/docs
```

Ou ReDoc:
```
http://localhost:8000/redoc
```

## Notas de Desenvolvimento

- Todas as respostas seguem schemas Pydantic para validação
- Sessões são armazenadas em memória (reiniciam com o servidor)
- Implemente persistência de sessão para produção
- Configure CORS adequadamente para produção
- Adicione rate limiting e autenticação