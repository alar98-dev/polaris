import os
import requests
from typing import List, Dict, Any, Optional

EMBEDDING_URL = os.getenv('EMBEDDING_URL', 'http://127.0.0.1:20002')


def get_embedding(texts: List[str], model: Optional[str] = None) -> List[List[float]]:
    """Pede embeddings para o Subcórtex Gemma 270M (640D) no host 127.0.0.1:20002."""
    url = f"{EMBEDDING_URL.rstrip('/')}/v1/embeddings"
    payload = {'input': texts}
    if model:
        payload['model'] = model

    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    body = r.json()

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
