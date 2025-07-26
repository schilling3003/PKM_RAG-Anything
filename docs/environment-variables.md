# Environment Variables and Configuration

This document provides comprehensive documentation for all environment variables and configuration options available in the AI PKM Tool.

## Configuration Overview

The AI PKM Tool uses environment variables for configuration, which can be set in several ways:

1. **`.env` file** (recommended for development)
2. **System environment variables** (recommended for production)
3. **Docker environment** (for containerized deployments)
4. **Configuration files** (for advanced settings)

## Core Environment Variables

### API Keys and Authentication

#### `OPENAI_API_KEY`
- **Type**: String
- **Required**: Optional (system works with fallbacks)
- **Description**: OpenAI API key for AI-powered features
- **Example**: `sk-proj-...`
- **Notes**: 
  - Required for full AI functionality
  - System provides fallback behavior when not set
  - Keep secure and never commit to version control

#### `OPENAI_BASE_URL`
- **Type**: URL
- **Required**: No
- **Default**: `https://api.openai.com/v1`
- **Description**: Custom OpenAI API endpoint
- **Example**: `https://your-custom-endpoint.com/v1`
- **Use Cases**: 
  - Custom OpenAI-compatible services
  - Proxy configurations
  - Local AI model endpoints

### AI Model Configuration

#### `LLM_MODEL`
- **Type**: String
- **Required**: No
- **Default**: `gpt-4o-mini`
- **Description**: Language model for text generation and analysis
- **Options**: `gpt-4o-mini`, `gpt-4o`, `gpt-4`, `gpt-3.5-turbo`
- **Notes**: Choose based on performance needs and cost considerations

#### `VISION_MODEL`
- **Type**: String
- **Required**: No
- **Default**: `gpt-4o`
- **Description**: Vision model for image analysis
- **Options**: `gpt-4o`, `gpt-4-vision-preview`
- **Notes**: Used for OCR and image content analysis

#### `EMBEDDING_MODEL`
- **Type**: String
- **Required**: No
- **Default**: `text-embedding-3-large`
- **Description**: Model for generating text embeddings
- **Options**: `text-embedding-3-large`, `text-embedding-3-small`, `text-embedding-ada-002`
- **Notes**: Affects semantic search quality and performance

### Database Configuration

#### `DATABASE_URL`
- **Type**: Database URL
- **Required**: No
- **Default**: `sqlite:///./data/pkm.db`
- **Description**: Primary database connection string
- **Examples**:
  - SQLite: `sqlite:///./data/pkm.db`
  - PostgreSQL: `postgresql://user:pass@localhost/dbname`
  - MySQL: `mysql://user:pass@localhost/dbname`
- **Notes**: SQLite is recommended for single-user deployments

#### `CHROMA_DB_PATH`
- **Type**: File Path
- **Required**: No
- **Default**: `./data/chroma_db`
- **Description**: ChromaDB vector database storage location
- **Notes**: Used for storing document embeddings and semantic search

### Redis Configuration

#### `REDIS_URL`
- **Type**: Redis URL
- **Required**: Yes
- **Default**: `redis://localhost:6379/0`
- **Description**: Redis connection string for task queue
- **Examples**:
  - Local: `redis://localhost:6379/0`
  - Remote: `redis://user:pass@host:port/db`
  - Cluster: `redis://host1:port1,host2:port2/0`
- **Notes**: Required for background task processing

### File Storage Configuration

#### `UPLOAD_DIR`
- **Type**: Directory Path
- **Required**: No
- **Default**: `./data/uploads`
- **Description**: Directory for storing uploaded files
- **Notes**: Must be writable by the application

#### `PROCESSED_DIR`
- **Type**: Directory Path
- **Required**: No
- **Default**: `./data/processed`
- **Description**: Directory for storing processed document outputs
- **Notes**: Used for caching processed content

#### `RAG_STORAGE_DIR`
- **Type**: Directory Path
- **Required**: No
- **Default**: `./data/rag_storage`
- **Description**: LightRAG knowledge graph storage directory
- **Notes**: Contains graph data and indexes

#### `MAX_FILE_SIZE`
- **Type**: Integer (bytes)
- **Required**: No
- **Default**: `104857600` (100MB)
- **Description**: Maximum allowed file upload size
- **Examples**:
  - 50MB: `52428800`
  - 100MB: `104857600`
  - 500MB: `524288000`
- **Notes**: Consider server memory when setting large values

### MinerU Document Processing Configuration

#### `MINERU_DEVICE`
- **Type**: String
- **Required**: No
- **Default**: `cpu`
- **Description**: Processing device for MinerU document extraction
- **Options**: `cpu`, `cuda`
- **Notes**: 
  - Use `cuda` for GPU acceleration (requires CUDA setup)
  - GPU processing is significantly faster for large documents

#### `MINERU_BACKEND`
- **Type**: String
- **Required**: No
- **Default**: `pipeline`
- **Description**: MinerU processing backend
- **Options**: `pipeline`, `api`
- **Notes**: Pipeline mode is recommended for most use cases

#### `MINERU_LANG`
- **Type**: String
- **Required**: No
- **Default**: `en`
- **Description**: Primary language for document processing
- **Options**: `en`, `zh`, `fr`, `de`, `es`, etc.
- **Notes**: Affects OCR and text extraction accuracy

### Server Configuration

#### `DEBUG`
- **Type**: Boolean
- **Required**: No
- **Default**: `false`
- **Description**: Enable debug mode
- **Options**: `true`, `false`
- **Notes**: 
  - Set to `true` for development
  - Never use `true` in production

#### `HOST`
- **Type**: IP Address
- **Required**: No
- **Default**: `0.0.0.0`
- **Description**: Server bind address
- **Examples**: `0.0.0.0`, `127.0.0.1`, `localhost`
- **Notes**: Use `0.0.0.0` to accept connections from any interface

#### `PORT`
- **Type**: Integer
- **Required**: No
- **Default**: `8000`
- **Description**: Server port number
- **Range**: 1024-65535
- **Notes**: Ensure port is not in use by other services

#### `LOG_LEVEL`
- **Type**: String
- **Required**: No
- **Default**: `INFO`
- **Description**: Logging verbosity level
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Notes**: Use `DEBUG` for troubleshooting, `INFO` for production

### CORS Configuration

#### `ALLOWED_HOSTS`
- **Type**: JSON Array
- **Required**: No
- **Default**: `["http://localhost:3000", "http://127.0.0.1:3000"]`
- **Description**: Allowed origins for CORS requests
- **Example**: `["http://localhost:3000", "https://yourdomain.com"]`
- **Notes**: Add your frontend URLs for proper CORS handling

## Advanced Configuration

### Performance Tuning

#### `CELERY_WORKERS`
- **Type**: Integer
- **Required**: No
- **Default**: Auto-detected based on CPU cores
- **Description**: Number of Celery worker processes
- **Recommendation**: 2x CPU cores for I/O bound tasks
- **Notes**: More workers = more concurrent document processing

#### `UVICORN_WORKERS`
- **Type**: Integer
- **Required**: No
- **Default**: 1 (development), 4 (production)
- **Description**: Number of Uvicorn worker processes
- **Notes**: Only for production deployments

#### `CHROMA_BATCH_SIZE`
- **Type**: Integer
- **Required**: No
- **Default**: 1000
- **Description**: Batch size for ChromaDB operations
- **Notes**: Larger batches = better performance but more memory usage

### Memory and Resource Limits

#### `TORCH_CUDA_MEMORY_FRACTION`
- **Type**: Float (0.0-1.0)
- **Required**: No
- **Default**: 0.8
- **Description**: Fraction of GPU memory to use for PyTorch
- **Notes**: Only relevant when using CUDA

#### `WORKER_MEMORY_LIMIT`
- **Type**: String
- **Required**: No
- **Default**: Not set
- **Description**: Memory limit per worker process
- **Example**: `2G`, `512M`
- **Notes**: Helps prevent memory leaks in long-running processes

### Security Configuration

#### `SECRET_KEY`
- **Type**: String
- **Required**: No (auto-generated)
- **Description**: Secret key for session management
- **Notes**: Auto-generated if not provided, but should be set for production

#### `ALLOWED_FILE_TYPES`
- **Type**: JSON Array
- **Required**: No
- **Default**: `[".pdf", ".txt", ".md", ".docx", ".jpg", ".png", ".mp3", ".mp4"]`
- **Description**: Allowed file extensions for upload
- **Notes**: Restricts file types for security

## Configuration Examples

### Development Configuration (.env)

```bash
# Development settings
DEBUG=true
LOG_LEVEL=DEBUG
HOST=0.0.0.0
PORT=8000

# AI Configuration (optional for development)
OPENAI_API_KEY=your_dev_api_key_here
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Local services
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///./data/pkm.db

# File storage
UPLOAD_DIR=./data/uploads
MAX_FILE_SIZE=52428800

# MinerU settings
MINERU_DEVICE=cpu
MINERU_LANG=en

# CORS for local development
ALLOWED_HOSTS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

### Production Configuration

```bash
# Production settings
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# AI Configuration
OPENAI_API_KEY=your_production_api_key_here
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-large

# Production database
DATABASE_URL=postgresql://user:pass@db-host:5432/pkm_prod

# Redis cluster
REDIS_URL=redis://redis-cluster:6379/0

# File storage
UPLOAD_DIR=/app/data/uploads
PROCESSED_DIR=/app/data/processed
MAX_FILE_SIZE=104857600

# GPU acceleration
MINERU_DEVICE=cuda
TORCH_CUDA_MEMORY_FRACTION=0.7

# Performance tuning
CELERY_WORKERS=8
UVICORN_WORKERS=4
CHROMA_BATCH_SIZE=2000

# Security
SECRET_KEY=your_secure_secret_key_here
ALLOWED_HOSTS=["https://yourdomain.com", "https://api.yourdomain.com"]
```

### Docker Configuration

For Docker deployments, environment variables can be set in:

1. **docker-compose.yml**:
```yaml
services:
  backend:
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEBUG=false
      - REDIS_URL=redis://redis:6379/0
```

2. **Docker secrets** (production):
```yaml
services:
  backend:
    secrets:
      - openai_api_key
    environment:
      - OPENAI_API_KEY_FILE=/run/secrets/openai_api_key

secrets:
  openai_api_key:
    external: true
```

## Configuration Validation

The application validates configuration on startup and provides helpful error messages for common issues:

### Validation Checks
- Required environment variables are present
- File paths are accessible and writable
- Database connections are valid
- Redis connectivity is working
- API keys are properly formatted

### Configuration Health Check

```bash
# Check configuration status
curl http://localhost:8000/health/comprehensive

# Validate specific configurations
python -c "
from app.core.config import settings
print('Configuration loaded successfully')
print(f'Database: {settings.DATABASE_URL}')
print(f'Redis: {settings.REDIS_URL}')
"
```

## Best Practices

### Security
- Use environment variables for sensitive data
- Never commit API keys to version control
- Use different keys for development and production
- Regularly rotate API keys
- Use Docker secrets in production

### Performance
- Set appropriate worker counts based on hardware
- Use GPU acceleration when available
- Configure memory limits to prevent OOM errors
- Monitor resource usage and adjust accordingly

### Maintenance
- Document custom configurations
- Use consistent naming conventions
- Validate configurations in CI/CD pipelines
- Keep configuration templates updated

## Troubleshooting Configuration Issues

### Common Problems

1. **Missing API Key**: System works but AI features are limited
2. **Invalid Database URL**: Application fails to start
3. **Redis Connection Failed**: Background processing doesn't work
4. **File Permission Issues**: Upload/processing failures
5. **Memory Limits**: Worker processes crash under load

### Debugging Steps

1. Check environment variable loading:
   ```bash
   python -c "import os; print(os.environ.get('OPENAI_API_KEY', 'Not set'))"
   ```

2. Validate configuration:
   ```bash
   python -c "from app.core.config import settings; print(settings.dict())"
   ```

3. Test service connections:
   ```bash
   curl http://localhost:8000/health/comprehensive
   ```

4. Check logs for configuration errors:
   ```bash
   tail -f backend/logs/app.log
   ```