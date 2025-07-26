"""
LightRAG service for the PKM system.
This service provides knowledge graph and RAG capabilities using LightRAG.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
import numpy as np
from app.services.openai_service import get_openai_service
from app.core.config import settings

class LightRAGService:
    """Service for managing LightRAG knowledge graph and RAG operations."""
    
    def __init__(self, working_dir: str = "./data/rag_storage"):
        """
        Initialize LightRAG service.
        
        Args:
            working_dir: Directory for LightRAG storage
        """
        self.working_dir = working_dir
        self.rag: Optional[LightRAG] = None
        self._ensure_working_dir()
    
    def _ensure_working_dir(self):
        """Ensure the working directory exists."""
        Path(self.working_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_mock_embedding_func(self):
        """Get mock embedding function for testing without OpenAI API."""
        def mock_embedding(texts):
            if isinstance(texts, str):
                texts = [texts]
            # Return random embeddings for testing
            return np.random.rand(len(texts), 384).tolist()
        
        return EmbeddingFunc(
            embedding_dim=384,
            max_token_size=8192,
            func=mock_embedding
        )
    
    async def _mock_llm_func(self, prompt: str, **kwargs) -> str:
        """Mock LLM function for testing without OpenAI API."""
        return f"Mock response to: {prompt[:100]}..."
    
    def initialize_with_openai(self, 
                              api_key: Optional[str] = None,
                              llm_model: str = "gpt-4o-mini",
                              embedding_model: str = "text-embedding-3-large") -> bool:
        """
        Initialize LightRAG with OpenAI functions.
        
        Args:
            api_key: OpenAI API key (if None, will try to get from environment)
            llm_model: OpenAI model for text generation
            embedding_model: OpenAI model for embeddings
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Use the centralized OpenAI service
            openai_service = get_openai_service()
            
            # Configure the service if API key is provided
            if api_key:
                openai_service.configure(api_key=api_key)
            elif not openai_service._api_key:
                openai_service.configure()
            
            # Check if OpenAI service is available
            if not openai_service.is_available() and not openai_service._api_key:
                print("Warning: OpenAI service not available, falling back to mock functions")
                return self.initialize_with_mocks()
            
            self.rag = LightRAG(
                working_dir=self.working_dir,
                llm_model_func=openai_complete_if_cache,
                llm_model_name=llm_model or settings.LLM_MODEL,
                embedding_func=openai_embed,
                embedding_model_name=embedding_model or settings.EMBEDDING_MODEL
            )
            
            print(f"✓ LightRAG initialized with OpenAI (LLM: {llm_model or settings.LLM_MODEL}, Embedding: {embedding_model or settings.EMBEDDING_MODEL})")
            return True
            
        except Exception as e:
            print(f"✗ Failed to initialize LightRAG with OpenAI: {e}")
            print("Falling back to mock functions...")
            return self.initialize_with_mocks()
    
    def initialize_with_mocks(self) -> bool:
        """
        Initialize LightRAG with mock functions for testing.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.rag = LightRAG(
                working_dir=self.working_dir,
                llm_model_func=self._mock_llm_func,
                embedding_func=self._get_mock_embedding_func()
            )
            
            print("✓ LightRAG initialized with mock functions")
            return True
            
        except Exception as e:
            print(f"✗ Failed to initialize LightRAG with mocks: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """Check if LightRAG is initialized."""
        return self.rag is not None
    
    async def insert_document(self, content: str) -> bool:
        """
        Insert a document into the knowledge graph.
        
        Args:
            content: Document content to insert
            
        Returns:
            True if insertion successful, False otherwise
        """
        if not self.is_initialized():
            print("✗ LightRAG not initialized")
            return False
        
        try:
            await asyncio.to_thread(self.rag.insert, content)
            print(f"✓ Document inserted successfully ({len(content)} characters)")
            return True
            
        except Exception as e:
            print(f"✗ Failed to insert document: {e}")
            return False
    
    async def query(self, 
                   question: str, 
                   mode: str = "hybrid") -> Optional[str]:
        """
        Query the knowledge graph.
        
        Args:
            question: Question to ask
            mode: Query mode (naive, local, global, hybrid, mix)
            
        Returns:
            Query result or None if failed
        """
        if not self.is_initialized():
            print("✗ LightRAG not initialized")
            return None
        
        try:
            result = await asyncio.to_thread(
                self.rag.query, 
                question, 
                param=QueryParam(mode=mode)
            )
            print(f"✓ Query successful (mode: {mode})")
            return result
            
        except Exception as e:
            print(f"✗ Query failed: {e}")
            return None
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about the storage directory.
        
        Returns:
            Dictionary with storage information
        """
        storage_path = Path(self.working_dir)
        
        info = {
            "working_dir": self.working_dir,
            "exists": storage_path.exists(),
            "files": [],
            "total_size": 0
        }
        
        if storage_path.exists():
            for file_path in storage_path.rglob("*"):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    info["files"].append({
                        "name": file_path.name,
                        "path": str(file_path.relative_to(storage_path)),
                        "size": size
                    })
                    info["total_size"] += size
        
        return info
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on LightRAG service.
        
        Returns:
            Dictionary with health check results
        """
        openai_service = get_openai_service()
        openai_health = openai_service.health_check()
        
        health = {
            "initialized": self.is_initialized(),
            "working_dir_exists": Path(self.working_dir).exists(),
            "storage_info": self.get_storage_info(),
            "openai_service": {
                "configured": openai_health["configured"],
                "available": openai_health["available"]
            }
        }
        
        return health

# Global service instance
lightrag_service = LightRAGService()

async def initialize_lightrag_service() -> bool:
    """Initialize the global LightRAG service."""
    return lightrag_service.initialize_with_openai()

async def get_lightrag_service() -> LightRAGService:
    """Get the global LightRAG service instance."""
    if not lightrag_service.is_initialized():
        await initialize_lightrag_service()
    return lightrag_service