"""
Application configuration settings.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Basic app info
    PROJECT_NAME: str = "AI PKM Tool"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./data/pkm.db"
    
    # ChromaDB settings
    CHROMA_DB_PATH: str = "./data/chroma_db"
    
    # File storage settings
    UPLOAD_DIR: str = "./data/uploads"
    PROCESSED_DIR: str = "./data/processed"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # Redis settings (for Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # RAG-Anything settings
    RAG_STORAGE_DIR: str = "./data/rag_storage"
    EMBEDDING_DIM: int = 3072
    MAX_TOKEN_SIZE: int = 8192
    
    # AI Model settings (user-configurable)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    VISION_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    
    # MinerU settings
    MINERU_DEVICE: str = "cpu"  # or "cuda" if available
    MINERU_BACKEND: str = "pipeline"
    MINERU_LANG: str = "en"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()