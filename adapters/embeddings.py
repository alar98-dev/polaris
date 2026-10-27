import os
import requests
from typing import List, Dict, Any, Optional

EMBEDDING_URL = os.getenv('EMBEDDING_URL', 'http://127.0.0.1:20002')
EMBEDDING_EMBED_PATH = os.getenv('EMBEDDING_EMBED_PATH', '/v1/embeddings')


def _url(path: str) -> str:
    return EMBEDDING_URL.rstrip('/') + '/' + path.lstrip('/')


def get_embedding(texts: List[str], model: Optional[str] = None) -> List[List[float]]:
    """Pede embeddings para o Subcórtex Gemma 270M (640D) no host 127.0.0.1:20002.
    
    Suporta payload 'input' (formato OpenAI/llama.cpp) e 'inputs' (compatibilidade).
    """
    candidates = [EMBEDDING_EMBED_PATH, '/v1/embeddings', '/embeddings', '/v1/embed', '/embed']
    payload = {'input': texts, 'inputs': texts}
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
        raise last_err or RuntimeError("Failed to obtain embeddings from upstream")

    if 'data' in body and isinstance(body['data'], list):
        out = []
        for item in body['data']:
            if isinstance(item, dict) and 'embedding' in item:
                out.append(item['embedding'])
        return out

    if 'embeddings' in body:
        return body['embeddings']

    return []


def upsert_vector(id: Any, vector: List[float], metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Insere/atualiza vetor no banco PostgreSQL 17 nativo via polaris.db."""
    try:
        from polaris.db import get_db
        from polaris.sql_models import ArtifactChunk
        from sqlalchemy import select

        with get_db() as db:
            chunk = db.execute(select(ArtifactChunk).where(ArtifactChunk.id == int(id))).scalar_one_or_none()
            if chunk:
                chunk.embedding = vector
                if metadata:
                    chunk.metadata_ = {**(chunk.metadata_ or {}), **metadata}
                return True
        return False
    except Exception:
        return False


def search_vectors(vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """Busca os k vetores mais próximos no banco PostgreSQL 17 via HNSW."""
    try:
        from polaris.db import search_similar_chunks
        return search_similar_chunks(vector, top_k=top_k)
    except Exception:
        return []
