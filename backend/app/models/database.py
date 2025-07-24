"""
SQLAlchemy database models.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import (
    Column, String, Text, Integer, DateTime, JSON, 
    Float, Boolean, ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate UUID string."""
    return str(uuid.uuid4())


class Note(Base):
    """Note model for storing user notes."""
    
    __tablename__ = "notes"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False, default="")
    tags = Column(JSON, nullable=False, default=list)
    word_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_notes_title', 'title'),
        Index('idx_notes_created', 'created_at'),
        Index('idx_notes_updated', 'updated_at'),
    )
    
    def __repr__(self):
        return f"<Note(id='{self.id}', title='{self.title}')>"


class Document(Base):
    """Document model for storing uploaded documents."""
    
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False, index=True)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    processing_status = Column(String(50), nullable=False, default="queued", index=True)
    processing_error = Column(Text, nullable=True)
    task_id = Column(String(100), nullable=True, index=True)
    extracted_text = Column(Text, nullable=True)
    doc_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_documents_filename', 'filename'),
        Index('idx_documents_status', 'processing_status'),
        Index('idx_documents_created', 'created_at'),
        Index('idx_documents_task', 'task_id'),
    )
    
    def __repr__(self):
        return f"<Document(id='{self.id}', filename='{self.filename}', status='{self.processing_status}')>"


class KnowledgeGraphNode(Base):
    """Knowledge graph node model."""
    
    __tablename__ = "kg_nodes"
    
    id = Column(String, primary_key=True)
    label = Column(String(255), nullable=False, index=True)
    node_type = Column(String(100), nullable=False, index=True)
    properties = Column(JSON, nullable=False, default=dict)
    source_document_id = Column(String, ForeignKey('documents.id'), nullable=True)
    source_note_id = Column(String, ForeignKey('notes.id'), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source_document = relationship("Document", backref="kg_nodes")
    source_note = relationship("Note", backref="kg_nodes")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_kg_nodes_label', 'label'),
        Index('idx_kg_nodes_type', 'node_type'),
        Index('idx_kg_nodes_source_doc', 'source_document_id'),
        Index('idx_kg_nodes_source_note', 'source_note_id'),
    )
    
    def __repr__(self):
        return f"<KnowledgeGraphNode(id='{self.id}', label='{self.label}', type='{self.node_type}')>"


class KnowledgeGraphEdge(Base):
    """Knowledge graph edge model."""
    
    __tablename__ = "kg_edges"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    source_node_id = Column(String, ForeignKey('kg_nodes.id'), nullable=False)
    target_node_id = Column(String, ForeignKey('kg_nodes.id'), nullable=False)
    relation_type = Column(String(255), nullable=False, index=True)
    weight = Column(Float, nullable=False, default=1.0)
    properties = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source_node = relationship("KnowledgeGraphNode", foreign_keys=[source_node_id])
    target_node = relationship("KnowledgeGraphNode", foreign_keys=[target_node_id])
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_kg_edges_source', 'source_node_id'),
        Index('idx_kg_edges_target', 'target_node_id'),
        Index('idx_kg_edges_relationship', 'relation_type'),
        Index('idx_kg_edges_weight', 'weight'),
    )
    
    def __repr__(self):
        return f"<KnowledgeGraphEdge(source='{self.source_node_id}', target='{self.target_node_id}', rel='{self.relation_type}')>"


class SearchHistory(Base):
    """Search history model."""
    
    __tablename__ = "search_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    query = Column(Text, nullable=False)
    search_mode = Column(String(50), nullable=False)
    results_count = Column(Integer, nullable=False, default=0)
    processing_time = Column(Float, nullable=False, default=0.0)
    search_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_search_history_mode', 'search_mode'),
        Index('idx_search_history_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<SearchHistory(id='{self.id}', query='{self.query[:50]}...', mode='{self.search_mode}')>"


class RAGQueryHistory(Base):
    """RAG query history model."""
    
    __tablename__ = "rag_query_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    query = Column(Text, nullable=False)
    mode = Column(String(50), nullable=False, index=True)
    answer = Column(Text, nullable=False)
    sources_count = Column(Integer, nullable=False, default=0)
    processing_time = Column(Float, nullable=False, default=0.0)
    token_count = Column(Integer, nullable=False, default=0)
    query_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_rag_history_mode', 'mode'),
        Index('idx_rag_history_created', 'created_at'),
        Index('idx_rag_history_processing_time', 'processing_time'),
    )
    
    def __repr__(self):
        return f"<RAGQueryHistory(id='{self.id}', query='{self.query[:50]}...', mode='{self.mode}')>"


class BackgroundTask(Base):
    """Background task tracking model."""
    
    __tablename__ = "background_tasks"
    
    id = Column(String, primary_key=True)  # Celery task ID
    task_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    progress = Column(Integer, nullable=False, default=0)
    current_step = Column(String(255), nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    task_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_tasks_type', 'task_type'),
        Index('idx_tasks_status', 'status'),
        Index('idx_tasks_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<BackgroundTask(id='{self.id}', type='{self.task_type}', status='{self.status}')>"