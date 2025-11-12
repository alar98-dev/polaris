"""Função: generate_prototype

Gera documentação técnica de protótipo em Markdown.
"""
from typing import Dict, Any, Optional


async def generate_prototype(
    agent_instance,
    session_id: str,
    choice_id: int,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Gera documentação completa de protótipo.
    
    Cria um documento Markdown estruturado contendo:
    - Sumário executivo
    - Requisitos funcionais (mínimo 5)
    - Requisitos não-funcionais
    - Modelo de dados/entidades principais
    - Endpoints/APIs principais
    - Arquitetura proposta
    - Riscos e mitigações
    - Próximos passos
    
    Args:
        agent_instance: Instância do PolarisAgent
        session_id: UUID da sessão
        choice_id: ID do projeto escolhido
        context: Contexto adicional (summary, features, constraints, integrations)
    
    Returns:
        Dict contendo:
        - artifact: Dict com path e content do protótipo
          - path: Caminho onde salvar (ou None se não persistido)
          - content: Conteúdo Markdown completo
        - session_id: UUID da sessão
        - choice_id: ID do projeto
        - generated_at: Timestamp de geração
    """
    import time
    
    # Validar sessão
    session = agent_instance.sessions.get(session_id)
    if not session:
        return {
            "error": "session_not_found",
            "message": f"Sessão {session_id} não encontrada."
        }
    
    # Gerar protótipo
    result = await agent_instance.generate_prototype(
        choice_id=choice_id,
        context=context or {}
    )
    
    return {
        "artifact": result['artifact'],
        "session_id": session_id,
        "choice_id": choice_id,
        "generated_at": time.time()
    }
