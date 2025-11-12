"""Função: create_session

Cria uma nova sessão de conversa para rastreamento de estado.
"""
from typing import Optional, Dict, Any


def create_session(
    agent_instance,
    client_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Cria uma nova sessão de conversa.
    
    Args:
        agent_instance: Instância do PolarisAgent
        client_id: Identificador do cliente (opcional)
        metadata: Metadados adicionais (opcional)
    
    Returns:
        Dict contendo:
        - session_id: UUID da sessão criada
        - client_id: ID do cliente
        - created_at: Timestamp de criação
        - metadata: Metadados fornecidos
    """
    session_id = agent_instance.create_session(
        client_id=client_id,
        metadata=metadata or {}
    )
    
    session = agent_instance.sessions.get(session_id)
    
    return {
        "session_id": session_id,
        "client_id": session.get('client_id'),
        "created_at": session.get('created_at'),
        "metadata": session.get('metadata'),
        "status": "active"
    }
