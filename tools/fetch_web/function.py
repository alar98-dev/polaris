"""Função: fetch_web

Busca e extrai conteúdo textual de páginas web.
"""
from typing import Dict, Any, List, Optional
import httpx
from urllib.parse import urlparse, urljoin
import re


async def fetch_web(
    agent_instance,
    url: str,
    timeout: int = 15,
    extract_links: bool = False,
    max_length: int = 5000
) -> Dict[str, Any]:
    """Busca e extrai conteúdo de uma página web.
    
    Faz requisição HTTP para a URL especificada e extrai o conteúdo
    textual principal, removendo scripts, estilos e elementos de navegação.
    
    Args:
        agent_instance: Instância do PolarisAgent
        url: URL completa a ser buscada (http:// ou https://)
        timeout: Timeout em segundos (5-30, default: 15)
        extract_links: Se deve extrair links da página
        max_length: Tamanho máximo do conteúdo (1000-50000, default: 5000)
    
    Returns:
        Dict contendo:
        - url: URL original
        - title: Título da página
        - content: Conteúdo textual extraído
        - content_length: Tamanho do conteúdo
        - links: Lista de links (se extract_links=True)
        - status_code: Código HTTP da resposta
        - success: Boolean indicando sucesso
        - error: Mensagem de erro (se houver)
    
    Raises:
        ValueError: Se URL for inválida
    """
    # Validar URL
    if not url.startswith(('http://', 'https://')):
        return {
            "success": False,
            "error": "URL deve começar com http:// ou https://",
            "url": url
        }
    
    # Validar parâmetros
    timeout = max(5, min(30, timeout))
    max_length = max(1000, min(50000, max_length))
    
    try:
        # Fazer requisição
        async with httpx.AsyncClient(follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (POLARIS Agent) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = await client.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            html_content = response.text
            status_code = response.status_code
        
        # Extrair conteúdo
        result = _extract_content(html_content, url, max_length, extract_links)
        result['url'] = url
        result['status_code'] = status_code
        result['success'] = True
        
        return result
    
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": f"Timeout após {timeout} segundos",
            "url": url
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"Erro HTTP {e.response.status_code}: {e.response.reason_phrase}",
            "url": url,
            "status_code": e.response.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao buscar página: {str(e)}",
            "url": url
        }


def _extract_content(html: str, base_url: str, max_length: int, extract_links: bool) -> Dict[str, Any]:
    """Extrai conteúdo textual de HTML."""
    
    # Remover scripts e styles
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Extrair título
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else "Sem título"
    title = re.sub(r'\s+', ' ', title)
    
    # Extrair links se solicitado
    links = []
    if extract_links:
        link_matches = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.IGNORECASE)
        for href, text in link_matches[:20]:  # Limitar a 20 links
            full_url = urljoin(base_url, href)
            link_text = re.sub(r'<[^>]+>', '', text).strip()
            link_text = re.sub(r'\s+', ' ', link_text)
            if link_text and len(link_text) > 3:
                links.append({
                    "url": full_url,
                    "text": link_text[:100]
                })
    
    # Remover todas as tags HTML
    text = re.sub(r'<[^>]+>', ' ', html)
    
    # Limpar espaços em branco
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Limitar tamanho
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return {
        "title": title,
        "content": text,
        "content_length": len(text),
        "links": links if extract_links else None
    }
