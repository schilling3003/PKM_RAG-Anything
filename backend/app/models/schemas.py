"""
Pydantic models for request/response validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class ProcessingStatus(str, Enum):
    """Document processing status enum."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SearchMode(str, Enum):
    """Search mode enum."""
    SEMANTIC = "semantic"
    RAG = "rag"
    HYBRID = "hybrid"


# Base response models
class BaseResponse(BaseModel):
    """Base response model."""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "healthy"
    service: str
    version: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Note models
class NoteBase(BaseModel):
    """Base note model."""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(default="")
    tags: List[str] = Field(default_factory=list)


class NoteCreate(NoteBase):
    """Note creation model."""
    pass


class NoteUpdate(BaseModel):
    """Note update model."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class NoteResponse(NoteBase):
    """Note response model."""
    id: str
    created_at: datetime
    updated_at: datetime
    word_count: int = 0
    
    class Config:
        from_attributes = True


class NotesListResponse(BaseResponse):
    """Notes list response model."""
    notes: List[NoteResponse]
    total: int


# Document models
class DocumentBase(BaseModel):
    """Base document model."""
    filename: str = Field(..., min_length=1, max_length=255)
    file_type: str
    file_size: int = Field(..., gt=0)


class DocumentUpload(BaseModel):
    """Document upload response model."""
    document_id: str
    task_id: Optional[str] = None
    status: ProcessingStatus
    message: str


class DocumentResponse(DocumentBase):
    """Document response model."""
    id: str
    file_path: str
    processing_status: ProcessingStatus
    processing_error: Optional[str] = None
    extracted_text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="doc_metadata")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


class DocumentsListResponse(BaseResponse):
    """Documents list response model."""
    documents: List[DocumentResponse]
    total: int


class ProcessingStatusResponse(BaseModel):
    """Document processing status response."""
    document_id: str
    status: ProcessingStatus
    progress: int = Field(default=0, ge=0, le=100)
    current_step: str = ""
    error: Optional[str] = None
    estimated_time_remaining: Optional[int] = None


# Search models
class SearchQuery(BaseModel):
    """Search query model."""
    query: str = Field(..., min_length=1, max_length=1000)
    mode: SearchMode = SearchMode.SEMANTIC
    limit: int = Field(default=10, ge=1, le=100)
    filters: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Individual search result model."""
    id: str
    content: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    content_type: str  # "note", "document", etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)
    rank: int = Field(default=1, ge=1)


class SearchResponse(BaseResponse):
    """Search results response model."""
    query: str
    mode: SearchMode
    results: List[SearchResult]
    total: int
    processing_time: float


class RAGQuery(BaseModel):
    """RAG query model."""
    question: str = Field(..., min_length=1, max_length=1000)
    mode: str = Field(default="hybrid", pattern="^(local|global|hybrid)$")
    include_sources: bool = True
    max_sources: int = Field(default=5, ge=1, le=20)


class RAGResponse(BaseModel):
    """RAG response model."""
    query: str
    answer: str
    mode: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    processing_time: float
    token_count: int = Field(default=0, ge=0)


# Knowledge Graph models
class GraphNode(BaseModel):
    """Knowledge graph node model."""
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Knowledge graph edge model."""
    source: str
    target: str
    relationship: str
    weight: float = Field(default=1.0, ge=0.0)
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphData(BaseModel):
    """Knowledge graph data model."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class GraphResponse(BaseResponse):
    """Knowledge graph response model."""
    graph: GraphData
    total_nodes: int
    total_edges: int


class GraphFilters(BaseModel):
    """Graph filtering options."""
    node_types: Optional[List[str]] = None
    relationship_types: Optional[List[str]] = None
    min_weight: Optional[float] = Field(None, ge=0.0)
    max_nodes: int = Field(default=100, ge=1, le=1000)


# WebSocket models
class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProcessingUpdate(BaseModel):
    """Processing update message."""
    document_id: str
    status: ProcessingStatus
    progress: int = Field(default=0, ge=0, le=100)
    current_step: str = ""
    error: Optional[str] = None


# Task models
class TaskStatus(BaseModel):
    """Background task status model."""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: int = Field(default=0, ge=0, le=100)
    created_at: datetime
    updated_at: datetime


# Validation helpers - Note: validators will be added to specific models as needed