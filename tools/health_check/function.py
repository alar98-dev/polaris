"""Função: health_check

Verifica a saúde do agente e suas dependências.
"""
from typing import Dict, Any


async def health_check(
    agent_instance,
    check_embeddings: bool = False,
    check_database: bool = False
) -> Dict[str, Any]:
    """Verifica o status de saúde dos componentes do agente.
    
    Args:
        agent_instance: Instância do PolarisAgent
        check_embeddings: Se deve verificar o serviço de embeddings
        check_database: Se deve verificar o banco de dados
    
    Returns:
        Dict contendo:
        - ok: Boolean indicando saúde geral
        - components: Dict com status de cada componente
          - llm: Status do serviço LLM
          - embeddings: Status do serviço de embeddings (se solicitado)
          - database: Status do banco de dados (se solicitado)
    """
    result = await agent_instance.health_check()
    
    # TODO: Expandir para incluir embeddings e database quando implementado
    if check_embeddings:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{agent_instance.embedding_url}/health", timeout=3.0)
                result['components']['embeddings'] = {
                    'ok': r.status_code == 200,
                    'status_code': r.status_code
                }
                if r.status_code != 200:
                    result['ok'] = False
        except Exception as e:
            result['components']['embeddings'] = {'ok': False, 'error': str(e)}
            result['ok'] = False
    
    if check_database:
        # TODO: Implementar quando houver conexão com DB
        result['components']['database'] = {
            'ok': False,
            'error': 'Database check not implemented yet'
        }
    
    return result
