"""Função: generate_mock

Gera dados de exemplo (mocks) JSON para o projeto.
"""
from typing import Dict, Any, List, Optional


async def generate_mock(
    agent_instance,
    session_id: str,
    contract_name: str,
    context: Optional[Dict[str, Any]] = None,
    count: int = 10,
    include_invalid: bool = True
) -> Dict[str, Any]:
    """Gera dados de exemplo JSON.
    
    Cria mocks validados contra contratos Pydantic (quando disponíveis).
    Inclui exemplos válidos e opcionalmente inválidos para testes.
    
    Args:
        agent_instance: Instância do PolarisAgent
        session_id: UUID da sessão
        contract_name: Nome do contrato (ex: 'User', 'Product')
        context: Contexto adicional (example_base, domain, locale)
        count: Número de exemplos válidos (1-100)
        include_invalid: Se deve incluir exemplos inválidos
    
    Returns:
        Dict contendo:
        - mocks: Lista de objetos mock
        - valid_count: Número de exemplos válidos
        - invalid_count: Número de exemplos inválidos
        - contract_name: Nome do contrato usado
        - validated: Boolean indicando se passou por validação Pydantic
    """
    # Validar sessão
    session = agent_instance.sessions.get(session_id)
    if not session:
        return {
            "error": "session_not_found",
            "message": f"Sessão {session_id} não encontrada."
        }
    
    # Validar count
    count = max(1, min(100, count))
    
    # Gerar mocks
    mocks = await agent_instance.generate_mock(
        contract_name=contract_name,
        context=context or {},
        count=count
    )
    
    # TODO: Adicionar exemplos inválidos quando include_invalid=True
    invalid_mocks = []
    if include_invalid:
        # Gerar 2 exemplos inválidos (implementação futura)
        pass
    
    return {
        "mocks": mocks,
        "valid_count": len(mocks),
        "invalid_count": len(invalid_mocks),
        "contract_name": contract_name,
        "validated": False,  # TODO: Implementar validação Pydantic
        "session_id": session_id
    }
