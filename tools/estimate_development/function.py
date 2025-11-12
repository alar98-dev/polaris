"""Função: estimate_development

Estima esforço de desenvolvimento baseado em features.
"""
from typing import Dict, Any, List


async def estimate_development(
    agent_instance,
    session_id: str,
    features: List[str],
    include_buffer: bool = False
) -> Dict[str, Any]:
    """Estima o esforço de desenvolvimento.
    
    Classifica cada feature por complexidade (simple/medium/complex)
    e calcula horas totais. Retorna também tamanho t-shirt (S/M/L/XL).
    
    Heurística de complexidade baseada no tamanho da descrição:
    - Simple: < 20 chars → 8 horas
    - Medium: 20-60 chars → 24 horas
    - Complex: > 60 chars → 80 horas
    
    Args:
        agent_instance: Instância do PolarisAgent
        session_id: UUID da sessão
        features: Lista de funcionalidades a estimar
        include_buffer: Se deve adicionar 20% de buffer
    
    Returns:
        Dict contendo:
        - total_hours: Horas totais estimadas
        - total_hours_with_buffer: Com buffer aplicado (se solicitado)
        - breakdown: Lista detalhada por feature
          - feature: Descrição da feature
          - complexity: simple|medium|complex
          - hours: Horas estimadas para esta feature
        - t_shirt: Tamanho (S/M/L/XL)
        - session_id: UUID da sessão
    """
    # Validar sessão
    session = agent_instance.sessions.get(session_id)
    if not session:
        return {
            "error": "session_not_found",
            "message": f"Sessão {session_id} não encontrada."
        }
    
    # Validar features
    if not features or len(features) == 0:
        return {
            "error": "invalid_input",
            "message": "A lista de features não pode estar vazia."
        }
    
    # Gerar estimativa
    result = await agent_instance.estimate_development(features=features)
    
    # Adicionar buffer se solicitado
    total_hours = result['total_hours']
    if include_buffer:
        buffered = int(total_hours * 1.2)
        result['total_hours_with_buffer'] = buffered
        result['buffer_percentage'] = 20
    else:
        result['total_hours_with_buffer'] = total_hours
        result['buffer_percentage'] = 0
    
    result['session_id'] = session_id
    
    return result
