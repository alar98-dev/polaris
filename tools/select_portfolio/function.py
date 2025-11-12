"""Função: select_portfolio

Busca projetos relevantes no portfólio usando RAG.
"""
from typing import Dict, Any, List, Optional


async def select_portfolio(
    agent_instance,
    query: str,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Busca e recomenda projetos do portfólio.
    
    Usa busca semântica (RAG) para encontrar os projetos mais relevantes
    com base na necessidade do cliente.
    
    Args:
        agent_instance: Instância do PolarisAgent
        query: Descrição da necessidade do cliente
        top_k: Número de projetos a retornar (1-10)
        filters: Filtros opcionais (max_budget, required_stack, industry)
    
    Returns:
        Dict contendo:
        - candidates: Lista de projetos recomendados
          - id: ID do projeto
          - title: Título do projeto
          - score: Score de similaridade (0-1)
          - rationale: Justificativa da recomendação
          - metadata: Metadados adicionais (stack, orçamento estimado, etc)
        - query: Query original usada
        - total_found: Total de projetos encontrados
    """
    # Validar top_k
    top_k = max(1, min(10, top_k))
    
    # Buscar no portfólio
    candidates = await agent_instance.select_portfolio(
        query=query,
        top_k=top_k
    )
    
    # TODO: Aplicar filtros quando implementado
    if filters:
        # Filtrar por orçamento máximo
        if 'max_budget' in filters and filters['max_budget']:
            max_budget = filters['max_budget']
            candidates = [
                c for c in candidates
                if c.get('estimated_budget', float('inf')) <= max_budget
            ]
        
        # Filtrar por stack obrigatório
        if 'required_stack' in filters and filters['required_stack']:
            required = set(filters['required_stack'])
            candidates = [
                c for c in candidates
                if required.issubset(set(c.get('stack', [])))
            ]
    
    return {
        "candidates": candidates[:top_k],
        "query": query,
        "total_found": len(candidates),
        "filters_applied": filters or {}
    }
