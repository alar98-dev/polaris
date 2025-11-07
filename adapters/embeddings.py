import os
import requests
from typing import List, Dict, Any, Optional

EMBEDDING_URL = os.getenv('EMBEDDING_URL', 'http://localhost:8001')
# Allow overriding paths if the embedding service uses non-standard routes
EMBEDDING_EMBED_PATH = os.getenv('EMBEDDING_EMBED_PATH', '/v1/embeddings')
EMBEDDING_UPSERT_PATH = os.getenv('EMBEDDING_UPSERT_PATH', '/v1/upsert')
EMBEDDING_SEARCH_PATH = os.getenv('EMBEDDING_SEARCH_PATH', '/v1/search')


def _url(path: str) -> str:
    return EMBEDDING_URL.rstrip('/') + '/' + path.lstrip('/')


def get_embedding(texts: List[str], model: Optional[str] = None) -> List[List[float]]:
    """Pede embeddings para o serviço de embeddings.

    Assunção de contrato (ajustar conforme implementação do serviço):
    POST {EMBEDDING_URL}/v1/embeddings
    body: { "inputs": [..], "model": "..." }
    response: { "embeddings": [[...], ...] }
    """
    # try a few common paths if the configured one fails
    candidates = [EMBEDDING_EMBED_PATH, '/v1/embeddings', '/embeddings', '/v1/embed', '/embed']
    payload = {'inputs': texts}
    if model:
        payload['model'] = model
    body = None
    last_err = None
    for p in candidates:
        try:
            url = _url(p)
            r = requests.post(url, json=payload, timeout=10)
            r.raise_for_status()
            body = r.json()
            break
        except Exception as e:
            last_err = e
            continue
    if body is None:
        raise last_err
    # suportar formatos variados
    if 'embeddings' in body:
        return body['embeddings']
    if 'data' in body:
        # por exemplo: OpenAI-like { data: [ { embedding: [...] }, ... ] }
        out = []
        for item in body['data']:
            if isinstance(item, dict) and 'embedding' in item:
                out.append(item['embedding'])
        return out
    # fallback
    return []


def upsert_vector(id: Any, vector: List[float], metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Insere/atualiza vetor no serviço.

    Assunção: POST {EMBEDDING_URL}/v1/upsert { items: [{id, vector, metadata}] }
    """
    candidates = [EMBEDDING_UPSERT_PATH, '/v1/upsert', '/upsert', '/v1/collections/upsert']
    payload = {'items': [{'id': id, 'vector': vector, 'metadata': metadata or {}}]}
    last_err = None
    for p in candidates:
        try:
            url = _url(p)
            r = requests.post(url, json=payload, timeout=10)
            r.raise_for_status()
            return r.status_code == 200
        except Exception as e:
            last_err = e
            continue
    raise last_err


def search_vector(vector: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
    """Busca vetores similares.

    Assunção: POST {EMBEDDING_URL}/v1/search { vector, top_k }
    resposta esperada: { results: [ { id, score, metadata }, ... ] }
    """
    candidates = [EMBEDDING_SEARCH_PATH, '/v1/search', '/search', '/v1/query', '/query']
    payload = {'vector': vector, 'top_k': top_k}
    body = None
    last_err = None
    for p in candidates:
        try:
            url = _url(p)
            r = requests.post(url, json=payload, timeout=10)
            r.raise_for_status()
            body = r.json()
            break
        except Exception as e:
            last_err = e
            continue
    if body is None:
        raise last_err
    if 'results' in body:
        return body['results']
    return body.get('matches') or body.get('items') or []
