# AI PKM Tool Setup Guide

This guide provides comprehensive instructions for setting up the AI Personal Knowledge Management Tool with all required dependencies and services.

## Quick Start

For the fastest setup experience, use our automated setup scripts:

```bash
# 1. Install dependencies
python scripts/install-deps.py

# 2. Run initial setup
python setup.py

# 3. Start development environment
python scripts/start-dev.py
```

## Prerequisites

### System Requirements

- **Python 3.9+** - Required for backend services
- **Node.js 18+** - Required for frontend development
- **Git** - For version control
- **4GB+ RAM** - Recommended for AI processing
- **10GB+ disk space** - For dependencies and data storage

### Optional Requirements

- **Docker & Docker Compose** - For containerized deployment
- **CUDA-compatible GPU** - For accelerated document processing
- **Redis** - Will be installed automatically or via Docker

## Installation Methods

### Method 1: Automated Setup (Recommended)

The automated setup handles all dependencies and configuration:

```bash
# Clone the repository
git clone <repository-url>
cd ai-pkm-tool

# Install all dependencies
python scripts/install-deps.py

# Run setup configuration
python setup.py

# Start development servers
python scripts/start-dev.py
```

### Method 2: Docker Setup

Use Docker for a consistent environment across all platforms:

```bash
# Clone the repository
git clone <repository-url>
cd ai-pkm-tool

# Start with Docker Compose (development)
python scripts/start-docker.py --mode dev --build

# Or start production environment
python scripts/start-docker.py --mode prod --build
```

### Method 3: Manual Setup

For advanced users who want full control over the installation:

#### Step 1: System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y build-essential python3-dev python3-venv nodejs npm redis-server
```

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.9 node redis
brew services start redis
```

**Windows:**
- Install Python 3.9+ from [python.org](https://python.org)
- Install Node.js from [nodejs.org](https://nodejs.org)
- Install Redis via Docker or WSL2

#### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 3: Frontend Setup

```bash
cd frontend
npm install
```

#### Step 4: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Add your OpenAI API key and other settings
```

#### Step 5: Database Setup

```bash
cd backend
python -c "from app.database import create_tables; create_tables()"
```

## Configuration

### Environment Variables

Edit the `.env` file to configure the application:

```bash
# AI Configuration (optional but recommended)
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-large

# Database Configuration
DATABASE_URL=sqlite:///./data/pkm.db
CHROMA_DB_PATH=./data/chroma_db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# File Storage
UPLOAD_DIR=./data/uploads
PROCESSED_DIR=./data/processed
RAG_STORAGE_DIR=./data/rag_storage
MAX_FILE_SIZE=104857600

# MinerU Configuration (for advanced document processing)
MINERU_DEVICE=cpu  # or 'cuda' if you have a compatible GPU
MINERU_BACKEND=pipeline
MINERU_LANG=en
```

### CUDA Configuration (Optional)

For GPU acceleration with MinerU document processing:

1. Install CUDA toolkit (11.8 or 12.1)
2. Install PyTorch with CUDA support:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```
3. Set environment variable:
   ```bash
   MINERU_DEVICE=cuda
   ```

## Running the Application

### Development Mode

Start all services for development:

```bash
# Using automation script (recommended)
python scripts/start-dev.py

# Or manually start each service:
# Terminal 1: Redis (if not running)
redis-server

# Terminal 2: Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3: Celery Worker
cd backend
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info

# Terminal 4: Frontend
cd frontend
npm run dev
```

### Production Mode

For production deployment:

```bash
# Using Docker (recommended)
python scripts/start-docker.py --mode prod --build

# Or manually with production settings
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# In separate terminal
celery -A app.core.celery_app worker --loglevel=info --concurrency=4
```

### Stopping Services

```bash
# Stop development services
python scripts/stop-dev.py

# Stop Docker services
python scripts/stop-docker.py

# Stop with cleanup
python scripts/stop-dev.py --cleanup
```

## Accessing the Application

Once running, access the application at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Checks**: http://localhost:8000/health

## Troubleshooting

### Common Issues

#### Redis Connection Failed
```bash
# Check if Redis is running
redis-cli ping

# Start Redis manually
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

#### Celery Worker Not Starting
```bash
# Check Redis connection
python -c "import redis; redis.Redis().ping()"

# Check Celery configuration
cd backend
python -c "from app.core.celery_app import celery_app; print(celery_app.conf)"
```

#### Import Errors
```bash
# Reinstall dependencies
cd backend
pip install --upgrade -r requirements.txt

# Check virtual environment
which python  # Should point to venv/bin/python
```

#### CUDA Issues
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Reinstall PyTorch with CUDA
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Health Checks

The application provides health check endpoints:

```bash
# Overall health
curl http://localhost:8000/health

# Service-specific health checks
curl http://localhost:8000/health/redis
curl http://localhost:8000/health/celery
curl http://localhost:8000/health/lightrag
curl http://localhost:8000/health/openai
```

### Log Files

Check logs for debugging:

```bash
# Backend logs (if running manually)
tail -f backend/logs/app.log

# Docker logs
docker-compose logs -f backend
docker-compose logs -f celery

# Celery logs
tail -f backend/logs/celery.log
```

## Development Workflow

### Making Changes

1. **Backend Changes**: The development server auto-reloads on file changes
2. **Frontend Changes**: Vite provides hot module replacement
3. **Database Changes**: Use Alembic for migrations
4. **Dependencies**: Update requirements.txt and package.json as needed

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
python scripts/test-integration.py
```

### Building for Production

```bash
# Build Docker images
docker-compose build

# Build frontend for production
cd frontend
npm run build
```

## Advanced Configuration

### Custom AI Models

Configure different AI models in `.env`:

```bash
# Use different OpenAI models
LLM_MODEL=gpt-4
VISION_MODEL=gpt-4-vision-preview
EMBEDDING_MODEL=text-embedding-ada-002

# Use custom OpenAI-compatible endpoint
OPENAI_BASE_URL=http://localhost:1234/v1
```

### Storage Configuration

Configure different storage backends:

```bash
# Local storage (default)
UPLOAD_DIR=./data/uploads
PROCESSED_DIR=./data/processed

# Network storage
UPLOAD_DIR=/mnt/shared/uploads
PROCESSED_DIR=/mnt/shared/processed
```

### Performance Tuning

Optimize for your hardware:

```bash
# Increase worker processes
CELERY_WORKERS=4
UVICORN_WORKERS=4

# Adjust memory limits
MAX_FILE_SIZE=209715200  # 200MB
CHROMA_BATCH_SIZE=1000

# GPU memory optimization
MINERU_BATCH_SIZE=8
TORCH_CUDA_MEMORY_FRACTION=0.8
```

## Support

For additional help:

1. Check the [troubleshooting section](#troubleshooting)
2. Review health check endpoints
3. Examine log files
4. Consult the API documentation at `/docs`

## Security Considerations

- Keep your OpenAI API key secure
- Use environment variables for sensitive configuration
- Consider using Docker secrets in production
- Regularly update dependencies for security patches
- Use HTTPS in production deployments