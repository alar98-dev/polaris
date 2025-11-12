"""
POLARIS Tools - Guia Rápido de Integração
==========================================

Este arquivo mostra como integrar as POLARIS tools com diferentes LLMs.
"""

# =============================================================================
# 1. OPENAI (GPT-4, GPT-3.5-turbo)
# =============================================================================

"""
from openai import OpenAI
from polaris.agent import PolarisAgent
from polaris.tools import get_all_tools, get_tool_function
import json

# Configurar cliente OpenAI
client = OpenAI(api_key="your-api-key")

# Inicializar agente POLARIS
agent = PolarisAgent()

# Obter todas as tools
tools = get_all_tools()

# Conversa
messages = [
    {"role": "system", "content": "Você é POLARIS, vendedor consultivo."},
    {"role": "user", "content": "Quero criar um e-commerce"}
]

# Chamar OpenAI com tools
response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

# Processar tool calls
message = response.choices[0].message
if message.tool_calls:
    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        # Executar função
        func = get_tool_function(function_name)
        result = await func(agent, **function_args)
        
        # Adicionar resultado ao histórico
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": function_name,
            "content": json.dumps(result)
        })
    
    # Continuar conversa com resultados
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages
    )
"""


# =============================================================================
# 2. ANTHROPIC (Claude)
# =============================================================================

"""
from anthropic import Anthropic
from polaris.agent import PolarisAgent
from polaris.tools import get_all_tools, get_tool_function
import json

# Configurar cliente Anthropic
client = Anthropic(api_key="your-api-key")

# Inicializar agente POLARIS
agent = PolarisAgent()

# Obter todas as tools (formato OpenAI precisa ser convertido para Anthropic)
openai_tools = get_all_tools()

# Converter para formato Anthropic
anthropic_tools = []
for tool in openai_tools:
    func = tool['function']
    anthropic_tools.append({
        "name": func['name'],
        "description": func['description'],
        "input_schema": func['parameters']
    })

# Chamar Claude
response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    tools=anthropic_tools,
    messages=[
        {"role": "user", "content": "Quero criar um e-commerce"}
    ]
)

# Processar tool use
for content in response.content:
    if content.type == "tool_use":
        # Executar função
        func = get_tool_function(content.name)
        result = await func(agent, **content.input)
        
        # Continuar conversa com resultado
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            tools=anthropic_tools,
            messages=[
                {"role": "user", "content": "Quero criar um e-commerce"},
                {"role": "assistant", "content": response.content},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": json.dumps(result)
                        }
                    ]
                }
            ]
        )
"""


# =============================================================================
# 3. GOOGLE GEMINI
# =============================================================================

"""
import google.generativeai as genai
from polaris.agent import PolarisAgent
from polaris.tools import get_all_tools, get_tool_function
import json

# Configurar Gemini
genai.configure(api_key="your-api-key")

# Inicializar agente POLARIS
agent = PolarisAgent()

# Obter tools (formato OpenAI precisa ser adaptado)
openai_tools = get_all_tools()

# Converter para formato Gemini
gemini_tools = []
for tool in openai_tools:
    func = tool['function']
    gemini_tools.append({
        "function_declarations": [{
            "name": func['name'],
            "description": func['description'],
            "parameters": func['parameters']
        }]
    })

# Criar modelo com tools
model = genai.GenerativeModel('gemini-pro', tools=gemini_tools)

# Iniciar chat
chat = model.start_chat()
response = chat.send_message("Quero criar um e-commerce")

# Processar function calls
for part in response.parts:
    if fn := part.function_call:
        # Executar função
        func = get_tool_function(fn.name)
        result = await func(agent, **dict(fn.args))
        
        # Enviar resultado de volta
        response = chat.send_message({
            "function_response": {
                "name": fn.name,
                "response": {"result": result}
            }
        })
"""


# =============================================================================
# 4. LOCAL LLM (Ollama, LM Studio)
# =============================================================================

"""
import requests
from polaris.agent import PolarisAgent
from polaris.tools import get_all_tools, get_tool_function
import json

# Configurar LLM local
LLM_URL = "http://localhost:11434"  # Ollama default

# Inicializar agente POLARIS
agent = PolarisAgent()

# Obter tools
tools = get_all_tools()

# Preparar prompt com descrição das tools
tools_description = "\\n\\n".join([
    f"{t['function']['name']}: {t['function']['description']}"
    for t in tools
])

system_prompt = f'''Você é POLARIS, um assistente com acesso às seguintes ferramentas:

{tools_description}

Para usar uma ferramenta, responda no formato JSON:
{{"tool": "nome_da_tool", "args": {{"parametro": "valor"}}}}
'''

# Chamar LLM local
response = requests.post(f"{LLM_URL}/api/generate", json={
    "model": "llama2",
    "prompt": f"{system_prompt}\\n\\nUsuário: Quero criar um e-commerce",
    "stream": False
})

# Parse resposta e executar tool
result = response.json()
text = result['response']

try:
    # Tentar parsear como JSON (tool call)
    tool_call = json.loads(text)
    
    if 'tool' in tool_call and 'args' in tool_call:
        func = get_tool_function(tool_call['tool'])
        result = await func(agent, **tool_call['args'])
        
        # Continuar conversa com resultado
        response = requests.post(f"{LLM_URL}/api/generate", json={
            "model": "llama2",
            "prompt": f"{system_prompt}\\n\\nResultado da ferramenta {tool_call['tool']}: {json.dumps(result)}\\n\\nContinue a conversa.",
            "stream": False
        })
except json.JSONDecodeError:
    # Resposta não é tool call, é mensagem normal
    print(f"POLARIS: {text}")
"""


# =============================================================================
# 5. LANGCHAIN
# =============================================================================

"""
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.tools import StructuredTool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from polaris.agent import PolarisAgent
from polaris.tools import get_all_tools, get_tool_function

# Inicializar agente POLARIS
agent = PolarisAgent()

# Converter POLARIS tools para LangChain tools
langchain_tools = []
openai_tools = get_all_tools()

for tool_def in openai_tools:
    func_def = tool_def['function']
    func_name = func_def['name']
    
    # Obter função Python
    python_func = get_tool_function(func_name)
    
    # Criar LangChain tool
    langchain_tool = StructuredTool.from_function(
        func=lambda **kwargs: python_func(agent, **kwargs),
        name=func_name,
        description=func_def['description'],
        # args_schema pode ser gerado de func_def['parameters']
    )
    langchain_tools.append(langchain_tool)

# Criar prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é POLARIS, um vendedor consultivo."),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Criar LLM
llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)

# Criar agente
langchain_agent = create_openai_tools_agent(llm, langchain_tools, prompt)
agent_executor = AgentExecutor(agent=langchain_agent, tools=langchain_tools)

# Executar
result = agent_executor.invoke({"input": "Quero criar um e-commerce"})
print(result)
"""


# =============================================================================
# EXEMPLO MINIMALISTA (para testes rápidos)
# =============================================================================

if __name__ == "__main__":
    import asyncio
    from polaris.agent import PolarisAgent
    from polaris.tools.create_session.function import create_session
    from polaris.tools.ask_discovery.function import ask_discovery
    
    async def quick_test():
        # Inicializar agente
        agent = PolarisAgent()
        
        # Criar sessão
        session = create_session(agent, client_id="test")
        print(f"✅ Sessão criada: {session['session_id']}")
        
        # Fazer discovery
        result = await ask_discovery(
            agent,
            session_id=session['session_id'],
            message="Quero criar um e-commerce de roupas, orçamento 50k"
        )
        print(f"✅ Slots: {result['slots']}")
        print(f"✅ Próxima: {result['next_question']}")
    
    asyncio.run(quick_test())
