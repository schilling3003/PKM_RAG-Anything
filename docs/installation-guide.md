# AI PKM Tool - Installation Guide

This comprehensive guide covers all installation methods for the AI Personal Knowledge Management Tool, from quick automated setup to detailed manual configuration.

## Quick Start (Recommended)

For the fastest setup experience:

```bash
# 1. Clone the repository
git clone <repository-url>
cd ai-pkm-tool

# 2. Install dependencies automatically
python scripts/install-deps.py

# 3. Run initial setup
python setup.py

# 4. Start development environment
python scripts/start-dev.py
```

Access the application at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: 3.9 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 10GB free disk space
- **Network**: Internet connection for AI features and package installation

### Recommended Requirements
- **Memory**: 16GB RAM for optimal performance
- **Storage**: 50GB+ for large document collections
- **GPU**: CUDA-compatible GPU for accelerated document processing
- **CPU**: Multi-core processor for concurrent processing

### Software Dependencies
- **Git**: For version control and repository cloning
- **Python 3.9+**: Core runtime environment
- **Node.js 18+**: Frontend development (if building from source)
- **Docker & Docker Compose**: For containerized deployment (optional)
- **Redis**: Message broker for background tasks

## Installation Methods

### Method 1: Automated Setup (Recommended)

The automated setup handles all dependencies and configuration:

```bash
# Step 1: Clone repository
git clone <repository-url>
cd ai-pkm-tool

# Step 2: Run automated installation
python scripts/install-deps.py

# Step 3: Configure environment
python setup.py

# Step 4: Start services
python scripts/start-dev.py
```

**What the automated setup does:**
- Installs Python dependencies
- Sets up virtual environment
- Installs and configures Redis
- Creates necessary directories
- Configures environment variables
- Starts all required services

### Method 2: Docker Setup

Use Docker for consistent deployment across platforms:

```bash
# Step 1: Clone repository
git clone <repository-url>
cd ai-pkm-tool

# Step 2: Configure environment
cp .env.example .env
# Edit .env with your settings (especially OPENAI_API_KEY)

# Step 3: Start with Docker Compose
# Development mode:
python scripts/start-docker.py --mode dev --build

# Production mode:
python scripts/start-docker.py --mode prod --build
```

**Docker benefits:**
- Consistent environment across platforms
- Automatic dependency management
- Easy scaling and deployment
- Isolated from host system

### Method 3: Manual Installation

For advanced users who want full control:

#### Step 1: System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    python3-dev \
    python3-venv \
    python3-pip \
    nodejs \
    npm \
    redis-server \
    git \
    curl \
    wget
```

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.9 node redis git
brew services start redis
```

**Windows:**
1. Install Python 3.9+ from [python.org](https://python.org)
2. Install Node.js from [nodejs.org](https://nodejs.org)
3. Install Git from [git-scm.com](https://git-scm.com)
4. Install Redis via Docker or WSL2

#### Step 2: Python Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

#### Step 3: Backend Dependencies

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Install additional AI dependencies
pip install lightrag raganything
```

#### Step 4: Frontend Dependencies (Optional)

If you plan to modify the frontend:

```bash
cd frontend
npm install
```

#### Step 5: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

#### Step 6: Database Initialization

```bash
cd backend
python -c "
from app.database import create_tables
create_tables()
print('Database initialized successfully')
"
```

#### Step 7: Service Startup

```bash
# Terminal 1: Redis (if not running as service)
redis-server

# Terminal 2: Backend API
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3: Celery Worker
cd backend
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info

# Terminal 4: Frontend (optional, for development)
cd frontend
npm run dev
```

## GPU Acceleration Setup (Optional)

For enhanced document processing performance:

### CUDA Setup

1. **Install CUDA Toolkit** (version 11.8 or 12.1):
   - Download from [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)
   - Follow installation instructions for your platform

2. **Install PyTorch with CUDA support**:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Configure MinerU for GPU**:
   ```bash
   # In .env file
   MINERU_DEVICE=cuda
   ```

4. **Verify GPU setup**:
   ```bash
   python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
   ```

### Performance Benefits
- **PDF Processing**: 3-5x faster text extraction
- **Image Analysis**: 10x faster OCR and vision processing
- **Large Documents**: Significantly reduced processing time

## Verification

After installation, verify everything is working:

### Health Checks

```bash
# Check overall system health
curl http://localhost:8000/health/comprehensive

# Check individual services
curl http://localhost:8000/health/redis
curl http://localhost:8000/health/celery
curl http://localhost:8000/health/storage
```

### Automated Health Check

```bash
python scripts/health-check.py
```

### Test Document Upload

1. Open http://localhost:3000 (if frontend is running)
2. Upload a test document
3. Check processing status
4. Verify document appears in the system

## Troubleshooting Installation

### Common Issues

#### Python Version Issues
```bash
# Check Python version
python --version

# If version is < 3.9, install newer Python
# Ubuntu:
sudo apt-get install python3.9 python3.9-venv
# macOS:
brew install python@3.9
```

#### Permission Issues (Linux/macOS)
```bash
# Fix directory permissions
sudo chown -R $USER:$USER ./data
chmod -R 755 ./data
```

#### Redis Connection Issues
```bash
# Check if Redis is running
redis-cli ping

# Start Redis manually
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

#### Virtual Environment Issues
```bash
# Remove and recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### Port Conflicts
```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Use different port
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Getting Help

If you encounter issues:

1. **Check logs**: Look in `backend/logs/` directory
2. **Run health checks**: Use `python scripts/health-check.py`
3. **Check documentation**: Review troubleshooting guides
4. **Verify environment**: Ensure all environment variables are set
5. **Check dependencies**: Verify all packages are installed correctly

## Next Steps

After successful installation:

1. **Configure AI Services**: Set up OpenAI API key for full functionality
2. **Upload Test Documents**: Try uploading various document types
3. **Explore Features**: Test search, knowledge graphs, and AI capabilities
4. **Read User Guide**: Learn about advanced features and workflows
5. **Set Up Monitoring**: Configure health checks and logging for production

## Security Considerations

- **API Keys**: Never commit API keys to version control
- **File Permissions**: Ensure proper directory permissions
- **Network Security**: Use HTTPS in production
- **Updates**: Regularly update dependencies for security patches
- **Backups**: Set up regular backups of your data directory

## Performance Optimization

For production deployments:

- **Resource Allocation**: Allocate sufficient RAM and CPU
- **Concurrent Workers**: Adjust Celery worker count based on hardware
- **Database Optimization**: Consider PostgreSQL for large datasets
- **Caching**: Configure Redis for optimal performance
- **Monitoring**: Set up performance monitoring and alerting