"""
Live integration test connecting Polaris Agent to:
- Córtex Superior Gemma-3 1B on http://127.0.0.1:20003
- Subcórtex Gemma-3 270M on http://127.0.0.1:20002 (640D embeddings)
- PostgreSQL 17 swa_matrix (schema polaris) with HNSW vector index
"""

import pytest
from polaris.agent_core import PolarisAgent
from polaris.db import get_db, search_similar_chunks
from polaris.sql_models import Artifact, ArtifactChunk, Conversation
from sqlalchemy import select


@pytest.mark.asyncio
async def test_polaris_live_bi_cameral_health():
    agent = PolarisAgent(
        llm_url="http://127.0.0.1:20003",
        embedding_url="http://127.0.0.1:20002"
    )
    health = await agent.health_check()
    assert health['ok'] is True
    assert health['components']['llm']['ok'] is True
    assert health['components']['embedding']['ok'] is True


@pytest.mark.asyncio
async def test_polaris_live_extraction_and_pgvector_persistence():
    agent = PolarisAgent(
        llm_url="http://127.0.0.1:20003",
        embedding_url="http://127.0.0.1:20002"
    )

    # 1. Create session and verify DB persistence
    sid = agent.create_session(client_id="test_live_user", metadata={"test": "aeon_integration"})
    assert sid is not None

    with get_db() as db:
        conv = db.execute(select(Conversation).where(Conversation.session_id == sid)).scalar_one_or_none()
        assert conv is not None
        assert conv.client_id == "test_live_user"

    # 2. Test live prototype generation with 640D neural embedding
    proto_ctx = {
        'summary': 'Sistema de auditoria de tensores neurais e fissão bi-cameral',
        'features': [
            'Projeção vetorial 640D no PostgreSQL 17',
            'Supervisão contínua de Shannon entropy',
            'Fissão autoregressiva com Córtex Gemma 1B'
        ]
    }
    proto_res = await agent.generate_prototype(choice_id=42, context=proto_ctx)
    assert proto_res['artifact']['content'] is not None

    # 3. Verify artifact and chunks with 640D embeddings in PostgreSQL polaris schema
    with get_db() as db:
        art = db.execute(select(Artifact).order_by(Artifact.id.desc())).scalars().first()
        assert art is not None
        assert art.type == 'prototipo'
        assert len(art.chunks) >= 3

        # Check embedding dimension is 640
        first_chunk = art.chunks[0]
        assert first_chunk.embedding is not None
        assert len(first_chunk.embedding) == 640

    # 4. Perform live HNSW vector similarity search
    from polaris.adapters.embeddings import get_embedding
    query_emb = get_embedding(["auditoria de tensores e fissão bi-cameral"])
    assert len(query_emb) == 1
    assert len(query_emb[0]) == 640

    results = search_similar_chunks(query_emb[0], top_k=3)
    assert len(results) > 0
    assert results[0]['similarity'] > 0.5
    print(f"Top match similarity: {results[0]['similarity']:.4f} - Text: {results[0]['text'][:60]}")
