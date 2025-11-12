"""
Exemplo completo de uso das POLARIS Tools com LLM.

Este script demonstra como integrar as tools do POLARIS com um LLM
que suporta function calling (OpenAI, Anthropic, etc.).
"""

import asyncio
import json
import os
from typing import List, Dict, Any

# Importar componentes do POLARIS
from polaris.agent import PolarisAgent
from polaris.tools import get_all_tools, get_tool_function


class MockLLM:
    """Mock de um LLM para demonstração (substituir por OpenAI/Anthropic real)."""
    
    def __init__(self):
        self.conversation_history = []
    
    def chat(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Simula resposta do LLM com tool calls."""
        # Na prática, aqui você chamaria:
        # openai.chat.completions.create(messages=messages, tools=tools)
        
        last_message = messages[-1]["content"]
        
        # Simular decisão do LLM baseado na mensagem
        if "criar" in last_message.lower() or "novo" in last_message.lower():
            # LLM decide criar sessão
            return {
                "tool_calls": [{
                    "function": {
                        "name": "create_session",
                        "arguments": json.dumps({"client_id": "demo_client"})
                    }
                }]
            }
        elif "e-commerce" in last_message.lower() or "loja" in last_message.lower():
            # LLM decide fazer discovery
            return {
                "tool_calls": [{
                    "function": {
                        "name": "ask_discovery",
                        "arguments": json.dumps({
                            "session_id": "session_123",  # Obtido de create_session
                            "message": last_message
                        })
                    }
                }]
            }
        else:
            # LLM responde diretamente
            return {
                "message": "Como posso ajudá-lo?"
            }


async def execute_tool_call(agent: PolarisAgent, tool_call: Dict) -> Dict[str, Any]:
    """Executa uma tool call e retorna o resultado."""
    function_name = tool_call["function"]["name"]
    function_args = json.loads(tool_call["function"]["arguments"])
    
    print(f"\n🔧 Executando tool: {function_name}")
    print(f"   Argumentos: {json.dumps(function_args, indent=2)}")
    
    # Obter função Python
    func = get_tool_function(function_name)
    
    if not func:
        return {"error": f"Tool '{function_name}' não encontrada"}
    
    # Executar função
    try:
        result = await func(agent, **function_args)
        print(f"✅ Resultado: {json.dumps(result, indent=2)[:200]}...")
        return result
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return {"error": str(e)}


async def chat_with_polaris(user_message: str):
    """Simula uma conversa completa com o POLARIS."""
    
    print("=" * 80)
    print("🌟 POLARIS Agent - Function Calling Demo")
    print("=" * 80)
    
    # 1. Inicializar agente
    agent = PolarisAgent()
    
    # 2. Obter todas as tools disponíveis
    tools = get_all_tools()
    print(f"\n📋 {len(tools)} tools disponíveis:")
    for tool in tools:
        print(f"   - {tool['function']['name']}: {tool['function']['description'][:60]}...")
    
    # 3. Inicializar LLM (mock para demonstração)
    llm = MockLLM()
    
    # 4. Histórico de conversa
    messages = [
        {"role": "system", "content": "Você é POLARIS, um agente de vendas consultivas."},
        {"role": "user", "content": user_message}
    ]
    
    print(f"\n💬 Usuário: {user_message}")
    
    # 5. Loop de conversação (até 5 iterações)
    session_id = None
    for iteration in range(5):
        print(f"\n--- Iteração {iteration + 1} ---")
        
        # LLM processa e pode chamar tools
        response = llm.chat(messages, tools)
        
        # Verificar se há tool calls
        if "tool_calls" in response:
            for tool_call in response["tool_calls"]:
                # Executar tool
                result = await execute_tool_call(agent, tool_call)
                
                # Salvar session_id se foi criado
                if tool_call["function"]["name"] == "create_session":
                    session_id = result.get("session_id")
                    print(f"\n🆔 Session ID: {session_id}")
                
                # Adicionar resultado ao histórico
                messages.append({
                    "role": "function",
                    "name": tool_call["function"]["name"],
                    "content": json.dumps(result)
                })
                
                # LLM pode chamar mais tools ou responder
                # (simplificado - na prática, chamar LLM novamente)
        
        elif "message" in response:
            # LLM respondeu diretamente
            print(f"\n🤖 POLARIS: {response['message']}")
            break
        
        else:
            print("\n⚠️ Resposta inesperada do LLM")
            break


async def demo_complete_flow():
    """Demonstração de um fluxo completo de discovery."""
    
    print("\n" + "=" * 80)
    print("📊 DEMO: Fluxo Completo de Discovery")
    print("=" * 80)
    
    agent = PolarisAgent()
    
    # 1. Criar sessão
    print("\n1️⃣ Criando sessão...")
    from polaris.tools.create_session.function import create_session
    session_result = create_session(agent, client_id="demo_user")
    session_id = session_result["session_id"]
    print(f"   ✅ Session criada: {session_id}")
    
    # 2. Discovery - Primeira mensagem
    print("\n2️⃣ Discovery - Mensagem do cliente...")
    from polaris.tools.ask_discovery.function import ask_discovery
    
    discovery1 = await ask_discovery(
        agent,
        session_id=session_id,
        message="Quero criar um e-commerce para vender roupas, orçamento de 50 mil"
    )
    print(f"   Slots extraídos: {discovery1.get('slots')}")
    print(f"   Próxima pergunta: {discovery1.get('next_question')}")
    
    # 3. Discovery - Segunda mensagem
    if discovery1.get('next_question'):
        print("\n3️⃣ Discovery - Resposta do cliente...")
        discovery2 = await ask_discovery(
            agent,
            session_id=session_id,
            message="O público são mulheres de 25-40 anos que compram pelo celular. KPI principal é conversão."
        )
        print(f"   Slots atualizados: {discovery2.get('slots')}")
        print(f"   Discovery completo? {discovery2.get('complete')}")
    
    # 4. Buscar no portfólio
    if discovery2.get('complete'):
        print("\n4️⃣ Buscando no portfólio...")
        from polaris.tools.select_portfolio.function import select_portfolio
        
        portfolio = await select_portfolio(
            agent,
            query="e-commerce mobile para roupas femininas foco em conversão",
            top_k=3
        )
        print(f"   {len(portfolio['candidates'])} projetos encontrados:")
        for i, candidate in enumerate(portfolio['candidates'], 1):
            print(f"      {i}. {candidate['title']} (score: {candidate['score']})")
    
    # 5. Gerar protótipo (simulando escolha do cliente)
    print("\n5️⃣ Gerando protótipo do projeto escolhido...")
    from polaris.tools.generate_prototype.function import generate_prototype
    
    prototype = await generate_prototype(
        agent,
        session_id=session_id,
        choice_id=1,
        context={
            "summary": "E-commerce mobile para roupas femininas com foco em conversão",
            "features": [
                "Catálogo de produtos com filtros",
                "Carrinho de compras",
                "Checkout simplificado",
                "Integração com gateway de pagamento",
                "Painel administrativo"
            ]
        }
    )
    print(f"   ✅ Protótipo gerado ({len(prototype['artifact']['content'])} chars)")
    print(f"\n   Preview:\n{prototype['artifact']['content'][:300]}...")
    
    # 6. Estimar desenvolvimento
    print("\n6️⃣ Estimando esforço de desenvolvimento...")
    from polaris.tools.estimate_development.function import estimate_development
    
    estimate = await estimate_development(
        agent,
        session_id=session_id,
        features=[
            "Catálogo de produtos com filtros avançados",
            "Carrinho de compras persistente",
            "Checkout com múltiplos métodos de pagamento",
            "Painel administrativo completo com relatórios",
            "Sistema de notificações push"
        ],
        include_buffer=True
    )
    print(f"   ⏱️ Total: {estimate['total_hours']} horas")
    print(f"   📦 Com buffer: {estimate['total_hours_with_buffer']} horas")
    print(f"   👕 Tamanho: {estimate['t_shirt']}")


async def main():
    """Executar todas as demos."""
    
    # Demo 1: Conversa simples
    await chat_with_polaris("Quero criar um e-commerce para vender roupas")
    
    # Demo 2: Fluxo completo
    await demo_complete_flow()


if __name__ == "__main__":
    # Executar demos
    asyncio.run(main())
