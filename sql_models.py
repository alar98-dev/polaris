"""
SQLAlchemy ORM models for Polaris Agent integrated with PostgreSQL 17 swa_matrix.
Schema: polaris
Vector dimension: 640D (matching Aeon Subcortex Gemma-3 270M)
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, Integer, String, Text, Numeric, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Project(Base):
    __tablename__ = 'projects'
    __table_args__ = {'schema': 'polaris'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(ARRAY(Text), nullable=True)
    estimated_budget = Column(Numeric(12, 2), nullable=True)
    stack = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    artifacts = relationship('Artifact', back_populates='project', cascade='all, delete-orphan')


class Artifact(Base):
    __tablename__ = 'artifacts'
    __table_args__ = {'schema': 'polaris'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('polaris.projects.id', ondelete='SET NULL'), nullable=True)
    type = Column(Text, nullable=False)  # 'prototipo', 'mock', 'requirements', 'architecture'
    content = Column(Text, nullable=True)
    metadata_ = Column('metadata', JSONB, default=dict)
    created_by = Column(Text, default='polaris')
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = relationship('Project', back_populates='artifacts')
    chunks = relationship('ArtifactChunk', back_populates='artifact', cascade='all, delete-orphan')


class ArtifactChunk(Base):
    __tablename__ = 'artifact_chunks'
    __table_args__ = (
        UniqueConstraint('artifact_id', 'chunk_index', name='uq_artifact_chunk_index'),
        {'schema': 'polaris'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    artifact_id = Column(Integer, ForeignKey('polaris.artifacts.id', ondelete='CASCADE'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    metadata_ = Column('metadata', JSONB, default=dict)
    embedding = Column(Vector(640), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    artifact = relationship('Artifact', back_populates='chunks')


class Conversation(Base):
    __tablename__ = 'conversations'
    __table_args__ = {'schema': 'polaris'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    client_id = Column(Text, nullable=True)
    transcript = Column(JSONB, default=list)
    summary = Column(Text, nullable=True)
    metadata_ = Column('metadata', JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Job(Base):
    __tablename__ = 'jobs'
    __table_args__ = {'schema': 'polaris'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default='queued')
    payload = Column(JSONB, default=dict)
    result = Column(JSONB, default=dict)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
