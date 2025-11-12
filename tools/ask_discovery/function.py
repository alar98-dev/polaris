"""Função: ask_discovery

Processa mensagens do cliente e extrai informações de discovery.
"""
from typing import Dict, Any


async def ask_discovery(
    agent_instance,
    session_id: str,
    message: str
) -> Dict[str, Any]:
    """Processa uma mensagem durante a fase de discovery.
    
    Extrai automaticamente informações-chave da mensagem do cliente:
    - pain: Dor ou problema principal
    - users: Descrição dos usuários-alvo
    - kpi: Métrica de sucesso principal
    - budget: Faixa de orçamento
    
    Args:
        agent_instance: Instância do PolarisAgent
        session_id: UUID da sessão ativa
        message: Mensagem do cliente
    
    Returns:
        Dict contendo:
        - next_question: Próxima pergunta a fazer (ou None se completo)
        - slots: Dados extraídos até o momento
        - complete: Boolean indicando se discovery está completo
        - actions: Lista de ações sugeridas (ex: mostrar portfólio)
    
    Raises:
        KeyError: Se session_id não existir
    """
    try:
        result = await agent_instance.ask_discovery_questions(
            session_id=session_id,
            message=message
        )
        return result
    except KeyError:
        return {
            "error": "session_not_found",
            "message": f"Sessão {session_id} não encontrada. Use create_session primeiro."
        }
