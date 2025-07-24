"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
import structlog

from app.core.config import settings
from app.core.exceptions import (
    PKMException,
    pkm_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.api.routes import api_router


def setup_logging():
    """Configure structured logging."""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(message)s"
    )
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    setup_logging()
    logger = structlog.get_logger(__name__)
    logger.info("🚀 Starting AI PKM Tool backend...", version=settings.VERSION)
    
    # Create necessary directories
    import os
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
    os.makedirs(settings.RAG_STORAGE_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)
    os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
    
    logger.info("📁 Created necessary directories")
    
    # Initialize databases
    try:
        from app.core.migrations import initialize_migrations
        from app.core.vector_db import vector_db
        
        # Run database migrations
        migration_manager = initialize_migrations()
        migration_success = migration_manager.run_migrations()
        
        if migration_success:
            logger.info("✅ Database migrations completed successfully")
        else:
            logger.error("❌ Database migrations failed")
        
        # Initialize vector database
        vector_info = vector_db.get_collection_info()
        logger.info("✅ Vector database initialized", 
                   collection_name=vector_info["name"], 
                   document_count=vector_info["count"])
        
    except Exception as e:
        logger.error("❌ Database initialization failed", error=str(e))
        # Don't fail startup, but log the error
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AI PKM Tool backend...")


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="AI-focused Personal Knowledge Management Tool API",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Add custom middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add exception handlers
    app.add_exception_handler(PKMException, pkm_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI PKM Tool API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from app.models.schemas import HealthResponse
    return HealthResponse(
        status="healthy",
        service="ai-pkm-backend",
        version=settings.VERSION
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )