"""
OpenAI API service for the PKM system.
This service handles OpenAI API integration, connectivity testing, and fallback behavior.
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion
from openai.types import CreateEmbeddingResponse
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for managing OpenAI API integration."""
    
    def __init__(self):
        """Initialize OpenAI service."""
        self.client: Optional[OpenAI] = None
        self.async_client: Optional[AsyncOpenAI] = None
        self._api_key: Optional[str] = None
        self._base_url: Optional[str] = None
        self._is_available: bool = False
        self._last_test_result: Optional[Dict[str, Any]] = None
    
    def configure(self, 
                  api_key: Optional[str] = None, 
                  base_url: Optional[str] = None) -> bool:
        """
        Configure OpenAI API client.
        
        Args:
            api_key: OpenAI API key (if None, uses settings or environment)
            base_url: OpenAI base URL (if None, uses settings or default)
            
        Returns:
            True if configuration successful, False otherwise
        """
        try:
            # Use provided values or fall back to settings/environment
            self._api_key = (
                api_key or 
                settings.OPENAI_API_KEY or 
                os.getenv("OPENAI_API_KEY")
            )
            
            self._base_url = (
                base_url or 
                settings.OPENAI_BASE_URL or 
                os.getenv("OPENAI_BASE_URL")
            )
            
            if not self._api_key:
                logger.warning("No OpenAI API key provided")
                self._is_available = False
                return False
            
            # Initialize clients
            client_kwargs = {"api_key": self._api_key}
            if self._base_url:
                client_kwargs["base_url"] = self._base_url
            
            self.client = OpenAI(**client_kwargs)
            self.async_client = AsyncOpenAI(**client_kwargs)
            
            logger.info(f"OpenAI client configured with base_url: {self._base_url or 'default'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure OpenAI client: {e}")
            self._is_available = False
            return False
    
    async def test_connectivity(self) -> Dict[str, Any]:
        """
        Test OpenAI API connectivity and model access.
        
        Returns:
            Dictionary with test results
        """
        test_result = {
            "api_key_configured": bool(self._api_key),
            "client_initialized": bool(self.async_client),
            "connectivity_test": False,
            "model_access": {},
            "embedding_access": False,
            "error": None,
            "response_time": None
        }
        
        if not self.async_client:
            test_result["error"] = "OpenAI client not initialized"
            self._last_test_result = test_result
            return test_result
        
        try:
            import time
            start_time = time.time()
            
            # Test basic connectivity with a simple completion
            response = await self.async_client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            test_result["connectivity_test"] = True
            test_result["model_access"][settings.LLM_MODEL] = True
            test_result["response_time"] = time.time() - start_time
            
            # Test embedding model
            try:
                await self.async_client.embeddings.create(
                    model=settings.EMBEDDING_MODEL,
                    input="test"
                )
                test_result["embedding_access"] = True
                test_result["model_access"][settings.EMBEDDING_MODEL] = True
            except Exception as e:
                logger.warning(f"Embedding model test failed: {e}")
                test_result["model_access"][settings.EMBEDDING_MODEL] = False
            
            # Test vision model if different from LLM model
            if settings.VISION_MODEL != settings.LLM_MODEL:
                try:
                    await self.async_client.chat.completions.create(
                        model=settings.VISION_MODEL,
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=5
                    )
                    test_result["model_access"][settings.VISION_MODEL] = True
                except Exception as e:
                    logger.warning(f"Vision model test failed: {e}")
                    test_result["model_access"][settings.VISION_MODEL] = False
            
            self._is_available = True
            logger.info("OpenAI API connectivity test passed")
            
        except Exception as e:
            test_result["error"] = str(e)
            test_result["connectivity_test"] = False
            self._is_available = False
            logger.error(f"OpenAI API connectivity test failed: {e}")
        
        self._last_test_result = test_result
        return test_result
    
    def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        return self._is_available
    
    def get_last_test_result(self) -> Optional[Dict[str, Any]]:
        """Get the last connectivity test result."""
        return self._last_test_result
    
    async def chat_completion(self, 
                             messages: List[Dict[str, str]], 
                             model: Optional[str] = None,
                             **kwargs) -> Optional[str]:
        """
        Create a chat completion with fallback behavior.
        
        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to settings.LLM_MODEL)
            **kwargs: Additional parameters for the API call
            
        Returns:
            Completion text or None if failed
        """
        if not self.is_available() or not self.async_client:
            logger.warning("OpenAI API not available, returning fallback response")
            return self._get_fallback_response(messages)
        
        try:
            response = await self.async_client.chat.completions.create(
                model=model or settings.LLM_MODEL,
                messages=messages,
                **kwargs
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return self._get_fallback_response(messages)
    
    async def create_embeddings(self, 
                               texts: List[str], 
                               model: Optional[str] = None) -> Optional[List[List[float]]]:
        """
        Create embeddings with fallback behavior.
        
        Args:
            texts: List of texts to embed
            model: Model to use (defaults to settings.EMBEDDING_MODEL)
            
        Returns:
            List of embedding vectors or None if failed
        """
        if not self.is_available() or not self.async_client:
            logger.warning("OpenAI API not available, returning fallback embeddings")
            return self._get_fallback_embeddings(texts)
        
        try:
            response = await self.async_client.embeddings.create(
                model=model or settings.EMBEDDING_MODEL,
                input=texts
            )
            
            return [embedding.embedding for embedding in response.data]
            
        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            return self._get_fallback_embeddings(texts)
    
    def _get_fallback_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate fallback response when OpenAI API is unavailable.
        
        Args:
            messages: Original messages for context
            
        Returns:
            Fallback response string
        """
        last_message = messages[-1]["content"] if messages else "unknown query"
        return f"I apologize, but I'm currently unable to process your request due to AI service unavailability. Your query was: '{last_message[:100]}...'"
    
    def _get_fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate fallback embeddings when OpenAI API is unavailable.
        
        Args:
            texts: Texts that need embeddings
            
        Returns:
            List of random embedding vectors
        """
        import numpy as np
        # Return random embeddings with the expected dimension
        embedding_dim = 3072  # text-embedding-3-large dimension
        return np.random.rand(len(texts), embedding_dim).tolist()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on OpenAI service.
        
        Returns:
            Dictionary with health check results
        """
        return {
            "service": "openai",
            "configured": bool(self._api_key),
            "available": self._is_available,
            "base_url": self._base_url,
            "models": {
                "llm": settings.LLM_MODEL,
                "vision": settings.VISION_MODEL,
                "embedding": settings.EMBEDDING_MODEL
            },
            "last_test": self._last_test_result,
            "fallback_enabled": True
        }


# Global service instance
openai_service = OpenAIService()


async def initialize_openai_service() -> bool:
    """Initialize the global OpenAI service."""
    configured = openai_service.configure()
    if configured:
        test_result = await openai_service.test_connectivity()
        return test_result["connectivity_test"]
    return False


def get_openai_service() -> OpenAIService:
    """Get the global OpenAI service instance."""
    return openai_service