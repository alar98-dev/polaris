"""
Database connectivity and session factory for Polaris Agent.
Connects to PostgreSQL 17 swa_matrix under schema polaris.
"""

import os
from contextlib import contextmanager
from typing import Generator, List, Dict, Any, Optional

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker, Session
from .sql_models import Base, Project, Artifact, ArtifactChunk, Conversation, Job

DEFAULT_DB_URL = "postgresql://alifer:postgres@127.0.0.1:5432/swa_matrix"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def save_conversation_turn(session_id: str, client_id: Optional[str], transcript: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> None:
    """Save or update conversation history in polaris.conversations table."""
    with get_db() as db:
        conv = db.execute(select(Conversation).where(Conversation.session_id == session_id)).scalar_one_or_none()
        if conv:
            conv.transcript = transcript
            if metadata:
                conv.metadata_ = {**(conv.metadata_ or {}), **metadata}
        else:
            conv = Conversation(
                session_id=session_id,
                client_id=client_id,
                transcript=transcript,
                metadata_=metadata or {}
            )
            db.add(conv)


def save_artifact_with_chunks(
    project_id: Optional[int],
    artifact_type: str,
    content: str,
    chunks: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
    created_by: str = "polaris"
) -> int:
    """Save an artifact and its vectorized chunks (640D) in polaris schema."""
    with get_db() as db:
        artifact = Artifact(
            project_id=project_id,
            type=artifact_type,
            content=content,
            metadata_=metadata or {},
            created_by=created_by
        )
        db.add(artifact)
        db.flush()

        for idx, c in enumerate(chunks):
            chunk_obj = ArtifactChunk(
                artifact_id=artifact.id,
                chunk_index=idx,
                text=c.get("text", ""),
                metadata_=c.get("metadata", {}),
                embedding=c.get("embedding")
            )
            db.add(chunk_obj)
        return artifact.id


def search_similar_chunks(query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """Perform cosine similarity search on polaris.artifact_chunks using pgvector HNSW."""
    with get_db() as db:
        query = text("""
            SELECT 
                ac.id,
                ac.artifact_id,
                ac.chunk_index,
                ac.text,
                ac.metadata,
                1 - (ac.embedding <=> CAST(:vec AS vector)) AS similarity
            FROM polaris.artifact_chunks ac
            WHERE ac.embedding IS NOT NULL
            ORDER BY ac.embedding <=> CAST(:vec AS vector)
            LIMIT :k;
        """)
        vec_str = f"[{','.join(str(f) for f in query_vector)}]"
        result = db.execute(query, {"vec": vec_str, "k": top_k}).fetchall()
        
        return [
            {
                "chunk_id": r.id,
                "artifact_id": r.artifact_id,
                "chunk_index": r.chunk_index,
                "text": r.text,
                "metadata": r.metadata,
                "similarity": float(r.similarity)
            }
            for r in result
        ]
