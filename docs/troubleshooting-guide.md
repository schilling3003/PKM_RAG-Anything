# Troubleshooting Guide

This comprehensive guide helps you diagnose and resolve common issues with the AI PKM Tool.

## Quick Diagnosis

Start with these commands to get an overview of system health:

```bash
# Check overall system status
curl http://localhost:8000/health/comprehensive

# Run automated health check
python scripts/health-check.py

# Check service logs
docker-compose logs -f backend  # If using Docker
tail -f backend/logs/app.log    # If running locally
```

## Common Issues and Solutions

### 1. Document Upload Failures

#### Symptom: 500 Internal Server Error on Upload

**Possible Causes:**
- Redis not running
- Celery worker not started
- File permissions issues
- Disk space full

**Diagnosis:**
```bash
# Check Redis connectivity
redis-cli ping

# Check Celery worker status
curl http://localhost:8000/health/celery

# Check storage health
curl http://localhost:8000/health/storage

# Check disk space
df -h
```

**Solutions:**

1. **Start Redis:**
   ```bash
   # Local installation
   redis-server
   
   # Docker
   docker run -d -p 6379:6379 redis:7-alpine
   ```

2. **Start Celery Worker:**
   ```bash
   cd backend
   celery -A app.core.celery_app worker --loglevel=info
   ```

3. **Fix File Permissions:**
   ```bash
   sudo chown -R $USER:$USER ./data
   chmod -R 755 ./data
   ```

4. **Free Disk Space:**
   ```bash
   # Clean up processed files
   rm -rf ./data/processed/*
   
   # Clean up temporary files
   rm -rf /tmp/pkm_*
   ```

#### Symptom: File Too Large Error

**Solution:**
```bash
# Increase file size limit in .env
MAX_FILE_SIZE=209715200  # 200MB

# Restart services
python scripts/stop-dev.py
python scripts/start-dev.py
```

#### Symptom: Unsupported File Type

**Solution:**
```bash
# Check allowed file types
curl http://localhost:8000/api/v1/files/supported-types

# Add file type to configuration (if needed)
# Edit backend/app/core/config.py
```

### 2. Service Connection Issues

#### Symptom: Redis Connection Failed

**Diagnosis:**
```bash
# Test Redis connectivity
redis-cli ping

# Check Redis process
ps aux | grep redis

# Check Redis logs
tail -f /var/log/redis/redis-server.log
```

**Solutions:**

1. **Install Redis:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   brew services start redis
   
   # Windows (via Docker)
   docker run -d -p 6379:6379 redis:7-alpine
   ```

2. **Configure Redis URL:**
   ```bash
   # In .env file
   REDIS_URL=redis://localhost:6379/0
   ```

3. **Check Redis Configuration:**
   ```bash
   # Edit Redis config if needed
   sudo nano /etc/redis/redis.conf
   
   # Restart Redis
   sudo systemctl restart redis
   ```

#### Symptom: Database Connection Failed

**Diagnosis:**
```bash
# Check database file
ls -la ./data/pkm.db

# Test database connection
python -c "
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection successful')
"
```

**Solutions:**

1. **Create Database Directory:**
   ```bash
   mkdir -p ./data
   chmod 755 ./data
   ```

2. **Initialize Database:**
   ```bash
   cd backend
   python -c "
   from app.database import create_tables
   create_tables()
   print('Database initialized')
   "
   ```

3. **Fix Database Permissions:**
   ```bash
   chmod 644 ./data/pkm.db
   ```

### 3. AI Service Issues

#### Symptom: OpenAI API Not Working

**Diagnosis:**
```bash
# Check API key configuration
curl http://localhost:8000/health/openai

# Test API key manually
python -c "
import openai
import os
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
response = client.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{'role': 'user', 'content': 'Hello'}]
)
print('API key works')
"
```

**Solutions:**

1. **Set API Key:**
   ```bash
   # In .env file
   OPENAI_API_KEY=your_actual_api_key_here
   
   # Or as environment variable
   export OPENAI_API_KEY=your_actual_api_key_here
   ```

2. **Verify API Key Format:**
   - Should start with `sk-`
   - Should be 51+ characters long
   - Check for extra spaces or characters

3. **Check API Quota:**
   - Log into OpenAI dashboard
   - Check usage and billing
   - Verify account is in good standing

#### Symptom: LightRAG Not Working

**Diagnosis:**
```bash
# Check LightRAG health
curl http://localhost:8000/health/lightrag

# Test LightRAG import
python -c "
import lightrag
print('LightRAG imported successfully')
"
```

**Solutions:**

1. **Install LightRAG:**
   ```bash
   pip install lightrag
   ```

2. **Check Working Directory:**
   ```bash
   # Ensure RAG storage directory exists
   mkdir -p ./data/rag_storage
   chmod 755 ./data/rag_storage
   ```

3. **Verify OpenAI Integration:**
   ```bash
   # LightRAG requires OpenAI API key
   # Ensure OPENAI_API_KEY is set
   ```

#### Symptom: MinerU/RAG-Anything Issues

**Diagnosis:**
```bash
# Check RAG-Anything health
curl http://localhost:8000/health/raganything

# Test MinerU import
python -c "
from raganything.mineru_parser import MinerUParser
print('MinerU available')
"
```

**Solutions:**

1. **Install RAG-Anything:**
   ```bash
   pip install raganything
   ```

2. **Configure CUDA (if available):**
   ```bash
   # Check CUDA availability
   python -c "import torch; print(torch.cuda.is_available())"
   
   # Install CUDA PyTorch
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   
   # Set device in .env
   MINERU_DEVICE=cuda
   ```

3. **CPU Fallback:**
   ```bash
   # Use CPU processing
   MINERU_DEVICE=cpu
   ```

### 4. Performance Issues

#### Symptom: Slow Document Processing

**Diagnosis:**
```bash
# Check system resources
top
htop
free -h
df -h

# Check Celery worker status
celery -A app.core.celery_app inspect active
```

**Solutions:**

1. **Increase Worker Count:**
   ```bash
   # Start more Celery workers
   celery -A app.core.celery_app worker --loglevel=info --concurrency=4
   ```

2. **Enable GPU Acceleration:**
   ```bash
   # In .env file
   MINERU_DEVICE=cuda
   ```

3. **Optimize Memory Usage:**
   ```bash
   # Reduce batch sizes
   CHROMA_BATCH_SIZE=500
   MINERU_BATCH_SIZE=4
   ```

#### Symptom: High Memory Usage

**Solutions:**

1. **Limit Worker Memory:**
   ```bash
   # Add to Celery command
   celery -A app.core.celery_app worker --loglevel=info --max-memory-per-child=1000000
   ```

2. **Reduce Concurrent Processing:**
   ```bash
   # Lower concurrency
   celery -A app.core.celery_app worker --loglevel=info --concurrency=1
   ```

3. **Clear Processed Files:**
   ```bash
   # Clean up old processed files
   find ./data/processed -type f -mtime +7 -delete
   ```

### 5. Docker Issues

#### Symptom: Docker Services Won't Start

**Diagnosis:**
```bash
# Check Docker status
docker --version
docker-compose --version

# Check service logs
docker-compose logs backend
docker-compose logs redis
docker-compose logs celery
```

**Solutions:**

1. **Rebuild Containers:**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **Check Port Conflicts:**
   ```bash
   # Check what's using ports
   lsof -i :8000
   lsof -i :6379
   
   # Change ports in docker-compose.yml if needed
   ```

3. **Fix Volume Permissions:**
   ```bash
   # Fix data directory permissions
   sudo chown -R $USER:$USER ./data
   ```

#### Symptom: Environment Variables Not Loading

**Solutions:**

1. **Check .env File:**
   ```bash
   # Ensure .env file exists
   ls -la .env
   
   # Check file contents
   cat .env
   ```

2. **Verify Docker Compose Configuration:**
   ```bash
   # Check env_file directive in docker-compose.yml
   grep -A 5 "env_file" docker-compose.yml
   ```

3. **Use Environment Section:**
   ```yaml
   # In docker-compose.yml
   services:
     backend:
       environment:
         - OPENAI_API_KEY=${OPENAI_API_KEY}
   ```

### 6. Frontend Issues

#### Symptom: Frontend Not Loading

**Diagnosis:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check frontend build
cd frontend
npm run build
```

**Solutions:**

1. **Start Frontend Development Server:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. **Check API Connection:**
   ```bash
   # Verify API proxy configuration in vite.config.ts
   ```

3. **Clear Browser Cache:**
   - Hard refresh (Ctrl+F5)
   - Clear browser cache and cookies

### 7. Network and Connectivity Issues

#### Symptom: API Requests Failing

**Diagnosis:**
```bash
# Test API connectivity
curl -v http://localhost:8000/health

# Check CORS configuration
curl -H "Origin: http://localhost:3000" http://localhost:8000/health
```

**Solutions:**

1. **Configure CORS:**
   ```bash
   # In .env file
   ALLOWED_HOSTS=["http://localhost:3000", "https://yourdomain.com"]
   ```

2. **Check Firewall:**
   ```bash
   # Ubuntu/Debian
   sudo ufw status
   sudo ufw allow 8000
   
   # macOS
   # Check System Preferences > Security & Privacy > Firewall
   ```

3. **Verify Network Configuration:**
   ```bash
   # Check if service is binding to correct interface
   netstat -tlnp | grep 8000
   ```

## Advanced Troubleshooting

### Debug Mode

Enable debug mode for detailed error information:

```bash
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG

# Restart services
python scripts/stop-dev.py
python scripts/start-dev.py
```

### Log Analysis

Check different log sources:

```bash
# Application logs
tail -f backend/logs/app.log

# Celery logs
tail -f backend/logs/celery.log

# System logs (Linux)
journalctl -u redis
journalctl -f

# Docker logs
docker-compose logs -f --tail=100 backend
```

### Database Debugging

```bash
# Connect to SQLite database
sqlite3 ./data/pkm.db

# Check tables
.tables

# Check recent uploads
SELECT * FROM documents ORDER BY created_at DESC LIMIT 10;

# Check processing status
SELECT id, filename, processing_status FROM documents WHERE processing_status != 'completed';
```

### Performance Profiling

```bash
# Monitor system resources
htop
iotop
nethogs

# Profile Python application
pip install py-spy
py-spy top --pid $(pgrep -f "uvicorn")

# Monitor Redis
redis-cli monitor
```

## Getting Help

### Health Check Script

Use the comprehensive health check script:

```bash
python scripts/health-check.py --verbose
```

### Collect System Information

```bash
# System info script
python -c "
import sys, platform, os
print(f'Python: {sys.version}')
print(f'Platform: {platform.platform()}')
print(f'Architecture: {platform.architecture()}')
print(f'CPU Count: {os.cpu_count()}')
print(f'Working Directory: {os.getcwd()}')
"
```

### Create Support Bundle

```bash
# Create diagnostic bundle
mkdir -p support_bundle
cp .env.example support_bundle/
cp docker-compose.yml support_bundle/
curl http://localhost:8000/health/comprehensive > support_bundle/health.json
python scripts/health-check.py > support_bundle/health_check.txt
tail -100 backend/logs/app.log > support_bundle/app.log
tail -100 backend/logs/celery.log > support_bundle/celery.log
tar -czf support_bundle.tar.gz support_bundle/
```

## Prevention and Monitoring

### Regular Maintenance

```bash
# Weekly maintenance script
#!/bin/bash
# Clean up old processed files
find ./data/processed -type f -mtime +30 -delete

# Vacuum SQLite database
sqlite3 ./data/pkm.db "VACUUM;"

# Check disk space
df -h

# Update dependencies
pip list --outdated
```

### Monitoring Setup

```bash
# Set up basic monitoring
# Add to crontab (crontab -e):
*/5 * * * * curl -f http://localhost:8000/health || echo "Service down" | mail -s "PKM Tool Alert" admin@example.com
```

### Backup Strategy

```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backup_${DATE}.tar.gz ./data/
# Upload to cloud storage or remote location
```

This troubleshooting guide covers the most common issues you might encounter. For specific problems not covered here, check the application logs and use the health check endpoints to identify the root cause.