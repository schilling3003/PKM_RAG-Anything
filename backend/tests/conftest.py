"""
Pytest configuration and fixtures for the AI PKM Tool test suite.

This module provides shared fixtures and configuration for all tests,
including test database setup, mock services, and test data.
"""

import os
import sys
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import get_db, engine
from app.models.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for tests
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    yield test_engine
    
    # Cleanup
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=test_db_engine
    )
    
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_client(test_db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp(prefix="pkm_test_")
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def test_files(temp_dir):
    """Create test files for document processing tests."""
    files = {}
    
    # Text file
    text_file = os.path.join(temp_dir, "test_document.txt")
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write("""
        This is a test document for the AI PKM Tool.
        
        It contains information about artificial intelligence, machine learning, and knowledge management.
        
        Key concepts:
        - Natural Language Processing (NLP)
        - Large Language Models (LLMs)
        - Retrieval Augmented Generation (RAG)
        - Knowledge Graphs
        - Vector Embeddings
        """)
    files['text'] = text_file
    
    # Markdown file
    md_file = os.path.join(temp_dir, "test_notes.md")
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("""
# Test Notes

## Overview
This is a test markdown document.

## Features
- Document Processing
- Knowledge Graph
- Semantic Search
        """)
    files['markdown'] = md_file
    
    # JSON file
    json_file = os.path.join(temp_dir, "test_data.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write('{"test": "data", "entities": ["AI", "ML", "RAG"]}')
    files['json'] = json_file
    
    return files


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis client for testing."""
    with patch('redis.Redis') as mock_redis_class:
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.info.return_value = {"redis_version": "7.0.0"}
        mock_redis_instance.get.return_value = None
        mock_redis_instance.set.return_value = True
        mock_redis_instance.delete.return_value = 1
        mock_redis_class.return_value = mock_redis_instance
        yield mock_redis_instance


@pytest.fixture(scope="function")
def mock_celery():
    """Mock Celery app for testing."""
    with patch('app.core.celery_app.celery_app') as mock_celery_app:
        mock_celery_app.control.inspect.return_value.active.return_value = {"worker1": []}
        mock_celery_app.control.inspect.return_value.registered.return_value = {"worker1": ["app.tasks.process_document"]}
        yield mock_celery_app


@pytest.fixture(scope="function")
def mock_lightrag():
    """Mock LightRAG service for testing."""
    with patch('app.services.lightrag_service.LightRAGService') as mock_lightrag_class:
        mock_lightrag_instance = AsyncMock()
        mock_lightrag_instance.is_initialized.return_value = True
        mock_lightrag_instance.query.return_value = {
            "answer": "Test answer",
            "sources": [],
            "entities": [],
            "relationships": []
        }
        mock_lightrag_class.return_value = mock_lightrag_instance
        yield mock_lightrag_instance


@pytest.fixture(scope="function")
def mock_openai():
    """Mock OpenAI client for testing."""
    with patch('openai.OpenAI') as mock_openai_class:
        mock_client = Mock()
        mock_client.models.list.return_value.data = [
            Mock(id="gpt-4o-mini"),
            Mock(id="text-embedding-3-large")
        ]
        mock_openai_class.return_value = mock_client
        yield mock_client


@pytest.fixture(scope="function")
def mock_raganything():
    """Mock RAG-Anything processing for testing."""
    with patch('app.services.document_processor.process_with_raganything') as mock_process:
        mock_process.return_value = {
            "extracted_text": "Test extracted text",
            "metadata": {"pages": 1, "format": "text"},
            "entities": ["AI", "ML"],
            "success": True
        }
        yield mock_process


@pytest.fixture(scope="function")
def mock_all_services(mock_redis, mock_celery, mock_lightrag, mock_openai, mock_raganything):
    """Mock all external services for comprehensive testing."""
    return {
        "redis": mock_redis,
        "celery": mock_celery,
        "lightrag": mock_lightrag,
        "openai": mock_openai,
        "raganything": mock_raganything
    }


@pytest.fixture(scope="function")
def sample_document_data():
    """Sample document data for testing."""
    return {
        "filename": "test_document.txt",
        "file_type": "text/plain",
        "file_size": 1024,
        "extracted_text": "This is test content",
        "processing_status": "completed",
        "doc_metadata": {"pages": 1}
    }


# Test data fixtures
@pytest.fixture(scope="session")
def test_queries():
    """Common test queries for search and RAG testing."""
    return [
        "artificial intelligence",
        "machine learning algorithms",
        "knowledge graph construction",
        "semantic search functionality",
        "document processing pipeline"
    ]


@pytest.fixture(scope="session")
def load_test_config():
    """Configuration for load testing."""
    return {
        "concurrent_uploads": 10,
        "test_duration": 60,  # seconds
        "max_file_size": 1024 * 1024,  # 1MB
        "timeout": 30  # seconds
    }


# Error simulation fixtures
@pytest.fixture(scope="function")
def simulate_redis_failure():
    """Simulate Redis connection failure."""
    with patch('redis.Redis') as mock_redis_class:
        mock_redis_instance = Mock()
        mock_redis_instance.ping.side_effect = Exception("Redis connection failed")
        mock_redis_class.return_value = mock_redis_instance
        yield mock_redis_instance


@pytest.fixture(scope="function")
def simulate_celery_failure():
    """Simulate Celery worker failure."""
    with patch('app.core.celery_app.celery_app') as mock_celery_app:
        mock_celery_app.control.inspect.side_effect = Exception("Celery connection failed")
        yield mock_celery_app


@pytest.fixture(scope="function")
def simulate_storage_failure():
    """Simulate storage access failure."""
    with patch('os.path.exists') as mock_exists, \
         patch('os.makedirs') as mock_makedirs:
        mock_exists.return_value = False
        mock_makedirs.side_effect = PermissionError("Storage access denied")
        yield


@pytest.fixture(scope="function")
def simulate_openai_failure():
    """Simulate OpenAI API failure."""
    with patch('openai.OpenAI') as mock_openai_class:
        mock_client = Mock()
        mock_client.models.list.side_effect = Exception("OpenAI API unavailable")
        mock_openai_class.return_value = mock_client
        yield mock_client


# Performance testing fixtures
@pytest.fixture(scope="function")
def performance_monitor():
    """Monitor performance metrics during tests."""
    import time
    import psutil
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.start_memory = None
            self.end_memory = None
            self.process = psutil.Process()
        
        def start(self):
            self.start_time = time.time()
            self.start_memory = self.process.memory_info().rss
        
        def stop(self):
            self.end_time = time.time()
            self.end_memory = self.process.memory_info().rss
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
        
        @property
        def memory_delta(self):
            if self.start_memory and self.end_memory:
                return self.end_memory - self.start_memory
            return None
    
    return PerformanceMonitor()