"""Função: search_google

Realiza pesquisas no Google e retorna resultados estruturados.
"""
from typing import Dict, Any, List, Optional
import httpx
from urllib.parse import quote_plus, urlencode
import re
import json


async def search_google(
    agent_instance,
    query: str,
    num_results: int = 5,
    language: str = "pt",
    safe_search: bool = True,
    time_range: Optional[str] = None
) -> Dict[str, Any]:
    """Realiza busca no Google e retorna resultados estruturados.
    
    Faz requisição para a API de busca do Google (ou scraping como fallback)
    e retorna os resultados mais relevantes com título, snippet e URL.
    
    Args:
        agent_instance: Instância do PolarisAgent
        query: Termo de busca
        num_results: Número de resultados (1-10, default: 5)
        language: Código do idioma (default: 'pt')
        safe_search: Filtrar conteúdo adulto (default: true)
        time_range: Filtro temporal ('day', 'week', 'month', 'year', null)
    
    Returns:
        Dict contendo:
        - query: Query original
        - results: Lista de resultados
          - title: Título do resultado
          - url: URL do resultado
          - snippet: Descrição/snippet
          - position: Posição no ranking
        - total_results: Total de resultados encontrados
        - search_time: Tempo de busca
        - success: Boolean indicando sucesso
        - error: Mensagem de erro (se houver)
    
    Note:
        Esta implementação usa scraping básico do Google como fallback.
        Para produção, recomenda-se usar Google Custom Search API ou
        Serper API para melhores resultados e confiabilidade.
    """
    # Validar parâmetros
    if not query or len(query.strip()) == 0:
        return {
            "success": False,
            "error": "Query não pode estar vazia",
            "query": query
        }
    
    num_results = max(1, min(10, num_results))
    
    # Verificar se há API key configurada
    import os
    google_api_key = os.getenv('GOOGLE_API_KEY')
    google_cx = os.getenv('GOOGLE_CX')
    serper_api_key = os.getenv('SERPER_API_KEY')
    
    # Tentar Serper API primeiro (mais confiável para produção)
    if serper_api_key:
        return await _search_with_serper(
            query, num_results, language, safe_search, time_range, serper_api_key
        )
    
    # Tentar Google Custom Search API
    elif google_api_key and google_cx:
        return await _search_with_google_api(
            query, num_results, language, safe_search, time_range, 
            google_api_key, google_cx
        )
    
    # Fallback: scraping básico (menos confiável, usar apenas em dev)
    else:
        return await _search_with_scraping(
            query, num_results, language, safe_search, time_range
        )


async def _search_with_serper(
    query: str,
    num_results: int,
    language: str,
    safe_search: bool,
    time_range: Optional[str],
    api_key: str
) -> Dict[str, Any]:
    """Busca usando Serper API (https://serper.dev)."""
    
    url = "https://google.serper.dev/search"
    
    payload = {
        "q": query,
        "num": num_results,
        "gl": language,
    }
    
    if time_range:
        time_map = {
            "day": "d",
            "week": "w",
            "month": "m",
            "year": "y"
        }
        payload["tbs"] = f"qdr:{time_map.get(time_range, '')}"
    
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for i, item in enumerate(data.get("organic", [])[:num_results], 1):
            results.append({
                "position": i,
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_results": len(results),
            "search_time": data.get("searchParameters", {}).get("time", 0),
            "source": "serper"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro na Serper API: {str(e)}",
            "query": query
        }


async def _search_with_google_api(
    query: str,
    num_results: int,
    language: str,
    safe_search: bool,
    time_range: Optional[str],
    api_key: str,
    cx: str
) -> Dict[str, Any]:
    """Busca usando Google Custom Search API."""
    
    url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": num_results,
        "lr": f"lang_{language}",
        "safe": "active" if safe_search else "off"
    }
    
    if time_range:
        time_map = {
            "day": "d1",
            "week": "w1",
            "month": "m1",
            "year": "y1"
        }
        params["dateRestrict"] = time_map.get(time_range, "")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for i, item in enumerate(data.get("items", []), 1):
            results.append({
                "position": i,
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_results": int(data.get("searchInformation", {}).get("totalResults", 0)),
            "search_time": float(data.get("searchInformation", {}).get("searchTime", 0)),
            "source": "google_api"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro na Google API: {str(e)}",
            "query": query
        }


async def _search_with_scraping(
    query: str,
    num_results: int,
    language: str,
    safe_search: bool,
    time_range: Optional[str]
) -> Dict[str, Any]:
    """Fallback: scraping básico do Google (menos confiável).
    
    ATENÇÃO: Este método é apenas para desenvolvimento/testes.
    Para produção, use Serper API ou Google Custom Search API.
    """
    
    # Construir URL de busca
    base_url = "https://www.google.com/search"
    params = {
        "q": query,
        "num": num_results,
        "hl": language,
    }
    
    if safe_search:
        params["safe"] = "active"
    
    if time_range:
        time_map = {
            "day": "qdr:d",
            "week": "qdr:w",
            "month": "qdr:m",
            "year": "qdr:y"
        }
        params["tbs"] = time_map.get(time_range, "")
    
    url = f"{base_url}?{urlencode(params)}"
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = await client.get(url, headers=headers, timeout=10, follow_redirects=True)
            response.raise_for_status()
            html = response.text
        
        # Extrair resultados via regex (muito básico)
        results = []
        
        # Pattern para resultados orgânicos
        pattern = r'<div class="g"[^>]*>.*?<h3[^>]*>(.*?)</h3>.*?<a href="([^"]+)".*?<div[^>]*>(.*?)</div>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        for i, (title, url_match, snippet) in enumerate(matches[:num_results], 1):
            # Limpar HTML
            title_clean = re.sub(r'<[^>]+>', '', title).strip()
            snippet_clean = re.sub(r'<[^>]+>', '', snippet).strip()
            
            # Extrair URL
            if url_match.startswith('/url?q='):
                url_clean = url_match.split('/url?q=')[1].split('&')[0]
            else:
                url_clean = url_match
            
            if title_clean and url_clean:
                results.append({
                    "position": i,
                    "title": title_clean[:200],
                    "url": url_clean,
                    "snippet": snippet_clean[:300]
                })
        
        # Se não encontrou resultados via regex, retornar aviso
        if not results:
            return {
                "success": False,
                "error": "Não foi possível extrair resultados. Configure SERPER_API_KEY ou GOOGLE_API_KEY para melhores resultados.",
                "query": query,
                "source": "scraping_failed"
            }
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_results": len(results),
            "search_time": 0,
            "source": "scraping",
            "warning": "Usando scraping básico. Para produção, configure SERPER_API_KEY ou GOOGLE_API_KEY."
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao fazer scraping: {str(e)}",
            "query": query,
            "suggestion": "Configure SERPER_API_KEY ou GOOGLE_API_KEY para busca confiável."
        }
