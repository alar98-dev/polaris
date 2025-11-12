# POLARIS Tools - Function Calling

Esta pasta contém todas as ferramentas (tools) disponíveis para o agente POLARIS no formato **OpenAI Function Calling**.

## 📁 Estrutura

Cada ferramenta tem sua própria pasta contendo:

```
tools/
├── __init__.py                    # Módulo principal com loaders
├── README.md                      # Esta documentação
│
├── create_session/                # 🆕 Criar sessão
│   ├── tool.json                  # Definição OpenAI format
│   └── function.py                # Implementação Python
│
├── health_check/                  # 🏥 Verificar saúde
│   ├── tool.json
│   └── function.py
│
├── ask_discovery/                 # 💬 Discovery conversacional
│   ├── tool.json
│   └── function.py
│
├── select_portfolio/              # 🎯 Buscar no portfólio (RAG)
│   ├── tool.json
│   └── function.py
│
├── generate_prototype/            # 📄 Gerar documentação
│   ├── tool.json
│   └── function.py
│
├── generate_mock/                 # 🎲 Gerar dados mock
│   ├── tool.json
│   └── function.py
│
└── estimate_development/          # ⏱️ Estimar esforço
    ├── tool.json
    └── function.py
```

## 🚀 Como Usar

### 1. Enviar todas as tools para o LLM

```python
from polaris.tools import get_all_tools

# Obter todas as definições de tools no formato OpenAI
tools = get_all_tools()

# Enviar para o LLM junto com o prompt do usuário
response = llm.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Quero criar um e-commerce"}],
    tools=tools,
    tool_choice="auto"
)
```

### 2. Executar a função chamada pelo LLM

```python
from polaris.tools import get_tool_function
from polaris.agent import PolarisAgent

# Instanciar o agente
agent = PolarisAgent()

# LLM decidiu chamar uma tool
tool_call = response.choices[0].message.tool_calls[0]
function_name = tool_call.function.name
function_args = json.loads(tool_call.function.arguments)

# Obter a função Python correspondente
function = get_tool_function(function_name)

# Executar a função (passar agent_instance como primeiro argumento)
result = await function(agent, **function_args)

# Enviar resultado de volta para o LLM
```

### 3. Exemplo Completo de Fluxo

```python
import asyncio
import json
from polaris.agent import PolarisAgent
from polaris.tools import get_all_tools, get_tool_function

async def main():
    # 1. Inicializar agente
    agent = PolarisAgent()
    
    # 2. Obter todas as tools
    tools = get_all_tools()
    
    # 3. Usuário envia mensagem
    user_message = "Quero criar um e-commerce para vender roupas"
    
    # 4. LLM processa e decide chamar create_session
    # (simulando resposta do LLM)
    tool_calls = [
        {
            "function": {
                "name": "create_session",
                "arguments": '{"client_id": "user_123"}'
            }
        }
    ]
    
    # 5. Executar tool call
    for call in tool_calls:
        func_name = call["function"]["name"]
        func_args = json.loads(call["function"]["arguments"])
        
        func = get_tool_function(func_name)
        result = await func(agent, **func_args)
        
        print(f"Tool: {func_name}")
        print(f"Result: {result}")
        
        # 6. Agora com session_id, chamar ask_discovery
        if func_name == "create_session":
            session_id = result["session_id"]
            
            # LLM chama ask_discovery
            discovery_func = get_tool_function("ask_discovery")
            discovery_result = await discovery_func(
                agent,
                session_id=session_id,
                message=user_message
            )
            print(f"\nDiscovery: {discovery_result}")

asyncio.run(main())
```

## 📋 Lista de Tools

### 1. **create_session**
Cria uma nova sessão de conversa.

**Quando usar**: No início de cada interação com o cliente.

**Parâmetros**:
- `client_id` (opcional): ID do cliente
- `metadata` (opcional): Metadados adicionais

**Retorna**: `session_id`, `client_id`, `created_at`

---

### 2. **health_check**
Verifica saúde do agente e dependências.

**Quando usar**: Para diagnóstico ou antes de operações críticas.

**Parâmetros**:
- `check_embeddings` (opcional): Verificar serviço de embeddings
- `check_database` (opcional): Verificar banco de dados

**Retorna**: Status de cada componente

---

### 3. **ask_discovery**
Processa mensagem do cliente e extrai informações.

**Quando usar**: Durante toda a fase de discovery/levantamento de requisitos.

**Parâmetros**:
- `session_id` (obrigatório): UUID da sessão
- `message` (obrigatório): Mensagem do cliente

**Retorna**: `next_question`, `slots` extraídos, `complete`, `actions`

**Slots extraídos automaticamente**:
- `pain`: Dor/problema principal
- `users`: Usuários-alvo
- `kpi`: Métrica de sucesso
- `budget`: Orçamento

---

### 4. **select_portfolio**
Busca projetos relevantes no portfólio (RAG).

**Quando usar**: Após coletar informações do cliente no discovery.

**Parâmetros**:
- `query` (obrigatório): Descrição da necessidade
- `top_k` (opcional): Número de projetos (1-10, default: 5)
- `filters` (opcional): Filtros adicionais (max_budget, required_stack, industry)

**Retorna**: Lista de candidatos com score e rationale

---

### 5. **generate_prototype**
Gera documentação técnica completa em Markdown.

**Quando usar**: Após cliente escolher projeto do portfólio.

**Parâmetros**:
- `session_id` (obrigatório): UUID da sessão
- `choice_id` (obrigatório): ID do projeto escolhido
- `context` (opcional): Contexto adicional (summary, features, constraints)

**Retorna**: Artifact com content Markdown

---

### 6. **generate_mock**
Gera dados de exemplo JSON.

**Quando usar**: Para auxiliar desenvolvedores com dados de teste.

**Parâmetros**:
- `session_id` (obrigatório): UUID da sessão
- `contract_name` (obrigatório): Nome do contrato (ex: 'User', 'Product')
- `context` (opcional): Contexto adicional
- `count` (opcional): Número de exemplos (1-100, default: 10)
- `include_invalid` (opcional): Incluir exemplos inválidos (default: true)

**Retorna**: Lista de mocks

---

### 7. **estimate_development**
Estima esforço de desenvolvimento.

**Quando usar**: Para planejamento e precificação inicial.

**Parâmetros**:
- `session_id` (obrigatório): UUID da sessão
- `features` (obrigatório): Lista de funcionalidades
- `include_buffer` (opcional): Adicionar 20% de buffer (default: false)

**Retorna**: `total_hours`, `breakdown`, `t_shirt` size (S/M/L/XL)

---

## 🔧 Adicionar Nova Tool

Para adicionar uma nova ferramenta:

1. **Criar pasta**: `tools/nome_da_tool/`

2. **Criar `tool.json`** com a definição OpenAI:
```json
{
  "type": "function",
  "function": {
    "name": "nome_da_tool",
    "description": "Descrição clara do que a tool faz",
    "parameters": {
      "type": "object",
      "properties": {
        "parametro": {
          "type": "string",
          "description": "Descrição do parâmetro"
        }
      },
      "required": ["parametro"]
    }
  }
}
```

3. **Criar `function.py`** com a implementação:
```python
async def nome_da_tool(agent_instance, parametro: str):
    """Docstring explicando a função."""
    # Implementação
    return {"result": "..."}
```

4. **Atualizar `__init__.py`**:
   - Importar a função
   - Adicionar ao `get_tool_function` mapping
   - Adicionar ao `get_all_tools` list

## 📝 Convenções

1. **Nomes**: Use snake_case para nomes de tools
2. **Async**: Todas as funções devem ser async
3. **Primeiro parâmetro**: Sempre `agent_instance` (instância do PolarisAgent)
4. **Validação**: Validar session_id e retornar erro amigável se não existir
5. **Documentação**: Docstrings completas em todas as funções
6. **Type hints**: Usar typing para todos os parâmetros e retornos

## 🧪 Testes

Criar testes para cada tool em `tests/test_tools.py`:

```python
@pytest.mark.asyncio
async def test_create_session():
    from polaris.tools.create_session.function import create_session
    from polaris.agent import PolarisAgent
    
    agent = PolarisAgent()
    result = create_session(agent, client_id="test_user")
    
    assert "session_id" in result
    assert result["client_id"] == "test_user"
```

## 📚 Recursos

- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [POLARIS Documentation](../README.md)
- [Agent Core](../agent_core.py)
