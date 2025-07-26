# Deployment Guide

This comprehensive guide covers deployment options for the AI PKM Tool across different environments, from local development to production cloud deployments.

## Deployment Overview

The AI PKM Tool supports multiple deployment strategies:

1. **Local Development**: Quick setup for development and testing
2. **Docker Compose**: Containerized deployment for consistency
3. **Cloud Deployment**: Scalable production deployment
4. **Kubernetes**: Container orchestration for large-scale deployments
5. **Hybrid Deployment**: Mix of local and cloud services

## Prerequisites

### System Requirements

**Minimum Requirements:**
- 4GB RAM, 8GB recommended
- 2 CPU cores, 4+ recommended
- 20GB disk space, 100GB+ for production
- Network connectivity for AI services

**Software Requirements:**
- Docker 20.10+ and Docker Compose 2.0+
- Python 3.9+ (for local development)
- Git for version control

### Environment Preparation

```bash
# Clone the repository
git clone <repository-url>
cd ai-pkm-tool

# Copy environment template
cp .env.example .env

# Edit configuration (see Environment Variables section)
nano .env
```

## Deployment Methods

### 1. Local Development Deployment

Best for: Development, testing, single-user scenarios

#### Quick Start

```bash
# Automated setup
python scripts/install-deps.py
python setup.py
python scripts/start-dev.py
```

#### Manual Setup

```bash
# Install system dependencies
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install -y python3-dev python3-venv redis-server

# macOS:
brew install python@3.9 redis
brew services start redis

# Set up Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# Initialize database
cd backend
python -c "from app.database import create_tables; create_tables()"

# Start services
# Terminal 1: Backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# Terminal 3: Frontend (optional)
cd frontend
npm install
npm run dev
```

#### Service Management

```bash
# Start all services
python scripts/start-dev.py

# Stop all services
python scripts/stop-dev.py

# Check service status
python scripts/health-check.py
```

### 2. Docker Compose Deployment

Best for: Production, consistent environments, easy scaling

#### Development Mode

```bash
# Start development environment
python scripts/start-docker.py --mode dev --build

# Or manually:
docker-compose -f docker-compose.dev.yml up --build
```

#### Production Mode

```bash
# Start production environment
python scripts/start-docker.py --mode prod --build

# Or manually:
docker-compose up -d --build
```

#### Configuration

**docker-compose.yml** (Production):
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  backend:
    build: ./backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=false
    volumes:
      - backend_data:/app/data
    depends_on:
      - redis

  celery:
    build: ./backend
    restart: unless-stopped
    command: celery -A app.core.celery_app worker --loglevel=info --concurrency=4
    env_file:
      - .env
    environment:
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - backend_data:/app/data
    depends_on:
      - redis
      - backend

  frontend:
    build: ./frontend
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  redis_data:
  backend_data:
```

#### Scaling Services

```bash
# Scale Celery workers
docker-compose up -d --scale celery=3

# Scale backend instances (with load balancer)
docker-compose up -d --scale backend=2
```

### 3. Cloud Deployment

#### AWS Deployment

**Using AWS ECS with Fargate:**

1. **Prepare Infrastructure:**
```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name pkm-cluster

# Create task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

2. **ECS Task Definition** (ecs-task-definition.json):
```json
{
  "family": "pkm-tool",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-registry/pkm-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "REDIS_URL",
          "value": "redis://redis-cluster.cache.amazonaws.com:6379/0"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/pkm"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-key"
        }
      ]
    }
  ]
}
```

3. **Deploy Service:**
```bash
# Create service
aws ecs create-service \
  --cluster pkm-cluster \
  --service-name pkm-service \
  --task-definition pkm-tool:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

#### Google Cloud Platform

**Using Cloud Run:**

1. **Build and Push Container:**
```bash
# Build container
docker build -t gcr.io/your-project/pkm-backend ./backend

# Push to Container Registry
docker push gcr.io/your-project/pkm-backend
```

2. **Deploy to Cloud Run:**
```bash
gcloud run deploy pkm-backend \
  --image gcr.io/your-project/pkm-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars REDIS_URL=redis://redis-instance:6379/0 \
  --set-secrets OPENAI_API_KEY=openai-key:latest
```

#### Azure Deployment

**Using Container Instances:**

```bash
# Create resource group
az group create --name pkm-rg --location eastus

# Deploy container
az container create \
  --resource-group pkm-rg \
  --name pkm-backend \
  --image your-registry/pkm-backend:latest \
  --ports 8000 \
  --environment-variables REDIS_URL=redis://redis-cache:6379/0 \
  --secure-environment-variables OPENAI_API_KEY=your-api-key
```

### 4. Kubernetes Deployment

Best for: Large-scale deployments, microservices architecture

#### Kubernetes Manifests

**namespace.yaml:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: pkm-tool
```

**configmap.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pkm-config
  namespace: pkm-tool
data:
  REDIS_URL: "redis://redis-service:6379/0"
  DATABASE_URL: "postgresql://postgres:5432/pkm"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
```

**secret.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: pkm-secrets
  namespace: pkm-tool
type: Opaque
data:
  OPENAI_API_KEY: <base64-encoded-api-key>
```

**redis-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: pkm-tool
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: pkm-tool
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

**backend-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: pkm-tool
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/pkm-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: pkm-config
        - secretRef:
            name: pkm-secrets
        livenessProbe:
          httpGet:
            path: /api/v1/health/comprehensive
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health/comprehensive
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: pkm-tool
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

**celery-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery
  namespace: pkm-tool
spec:
  replicas: 2
  selector:
    matchLabels:
      app: celery
  template:
    metadata:
      labels:
        app: celery
    spec:
      containers:
      - name: celery
        image: your-registry/pkm-backend:latest
        command: ["celery", "-A", "app.core.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
        envFrom:
        - configMapRef:
            name: pkm-config
        - secretRef:
            name: pkm-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

#### Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n pkm-tool

# Check services
kubectl get services -n pkm-tool

# View logs
kubectl logs -f deployment/backend -n pkm-tool
```

### 5. Hybrid Deployment

Best for: Gradual migration, specific compliance requirements

#### Example: Local Processing with Cloud Storage

```yaml
# docker-compose.hybrid.yml
version: '3.8'

services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://user:pass@cloud-db:5432/pkm
      - REDIS_URL=redis://cloud-redis:6379/0
      - UPLOAD_DIR=/mnt/cloud-storage/uploads
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - /mnt/cloud-storage:/mnt/cloud-storage
```

## Environment-Specific Configurations

### Development Environment

```bash
# .env.development
DEBUG=true
LOG_LEVEL=DEBUG
OPENAI_API_KEY=sk-test-key
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///./data/pkm_dev.db
MAX_FILE_SIZE=52428800  # 50MB
CELERY_WORKERS=1
```

### Staging Environment

```bash
# .env.staging
DEBUG=false
LOG_LEVEL=INFO
OPENAI_API_KEY=sk-staging-key
REDIS_URL=redis://staging-redis:6379/0
DATABASE_URL=postgresql://user:pass@staging-db:5432/pkm_staging
MAX_FILE_SIZE=104857600  # 100MB
CELERY_WORKERS=2
```

### Production Environment

```bash
# .env.production
DEBUG=false
LOG_LEVEL=WARNING
OPENAI_API_KEY=sk-prod-key
REDIS_URL=redis://prod-redis-cluster:6379/0
DATABASE_URL=postgresql://user:pass@prod-db:5432/pkm_prod
MAX_FILE_SIZE=524288000  # 500MB
CELERY_WORKERS=8
UVICORN_WORKERS=4
```

## Load Balancing and High Availability

### Nginx Load Balancer

**nginx.conf:**
```nginx
upstream pkm_backend {
    least_conn;
    server backend1:8000 max_fails=3 fail_timeout=30s;
    server backend2:8000 max_fails=3 fail_timeout=30s;
    server backend3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name your-domain.com;

    # Health check endpoint
    location /health {
        proxy_pass http://pkm_backend/api/v1/health/comprehensive;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Main application
    location / {
        proxy_pass http://pkm_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # File upload size
        client_max_body_size 500M;
    }
}
```

### HAProxy Configuration

**haproxy.cfg:**
```
global
    daemon
    maxconn 4096

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend pkm_frontend
    bind *:80
    default_backend pkm_backend

backend pkm_backend
    balance roundrobin
    option httpchk GET /api/v1/health/comprehensive
    http-check expect status 200
    server backend1 backend1:8000 check
    server backend2 backend2:8000 check
    server backend3 backend3:8000 check
```

## Database Considerations

### SQLite (Development/Small Scale)

```bash
# Configuration
DATABASE_URL=sqlite:///./data/pkm.db

# Backup
cp ./data/pkm.db ./backups/pkm_$(date +%Y%m%d_%H%M%S).db

# Optimization
sqlite3 ./data/pkm.db "VACUUM; ANALYZE;"
```

### PostgreSQL (Production)

```bash
# Configuration
DATABASE_URL=postgresql://user:password@host:5432/database

# Connection pooling
pip install psycopg2-binary sqlalchemy[postgresql]

# Backup
pg_dump -h host -U user database > backup.sql

# Restore
psql -h host -U user database < backup.sql
```

### Database Migration

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Monitoring and Logging

### Centralized Logging

**docker-compose.logging.yml:**
```yaml
version: '3.8'

services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    # Or use external logging
    logging:
      driver: syslog
      options:
        syslog-address: "tcp://log-server:514"
```

### Monitoring Stack

**docker-compose.monitoring.yml:**
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  grafana_data:
```

## Security Considerations

### SSL/TLS Configuration

**nginx-ssl.conf:**
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://pkm_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Secrets Management

**Using Docker Secrets:**
```yaml
services:
  backend:
    secrets:
      - openai_api_key
      - database_password
    environment:
      - OPENAI_API_KEY_FILE=/run/secrets/openai_api_key
      - DATABASE_PASSWORD_FILE=/run/secrets/database_password

secrets:
  openai_api_key:
    external: true
  database_password:
    external: true
```

**Using Kubernetes Secrets:**
```bash
# Create secret
kubectl create secret generic pkm-secrets \
  --from-literal=openai-api-key=your-key \
  --from-literal=database-password=your-password
```

## Backup and Recovery

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
if [ "$DATABASE_TYPE" = "sqlite" ]; then
    cp ./data/pkm.db "$BACKUP_DIR/pkm_${DATE}.db"
elif [ "$DATABASE_TYPE" = "postgresql" ]; then
    pg_dump "$DATABASE_URL" > "$BACKUP_DIR/pkm_${DATE}.sql"
fi

# Backup data directory
tar -czf "$BACKUP_DIR/data_${DATE}.tar.gz" ./data/

# Backup configuration
cp .env "$BACKUP_DIR/env_${DATE}"

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Recovery Procedure

```bash
#!/bin/bash
# restore.sh

BACKUP_DATE=$1

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    exit 1
fi

# Stop services
python scripts/stop-dev.py

# Restore database
if [ -f "/backups/pkm_${BACKUP_DATE}.db" ]; then
    cp "/backups/pkm_${BACKUP_DATE}.db" ./data/pkm.db
elif [ -f "/backups/pkm_${BACKUP_DATE}.sql" ]; then
    psql "$DATABASE_URL" < "/backups/pkm_${BACKUP_DATE}.sql"
fi

# Restore data
tar -xzf "/backups/data_${BACKUP_DATE}.tar.gz"

# Restore configuration
cp "/backups/env_${BACKUP_DATE}" .env

# Start services
python scripts/start-dev.py

echo "Recovery completed from backup: $BACKUP_DATE"
```

## Performance Optimization

### Production Optimizations

```bash
# .env.production optimizations
CELERY_WORKERS=8
UVICORN_WORKERS=4
CHROMA_BATCH_SIZE=2000
MINERU_BATCH_SIZE=16
TORCH_CUDA_MEMORY_FRACTION=0.8

# Redis optimizations
REDIS_MAXMEMORY=2gb
REDIS_MAXMEMORY_POLICY=allkeys-lru

# Database optimizations
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
```

### Resource Limits

**docker-compose.production.yml:**
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
  
  celery:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
```

## Troubleshooting Deployment Issues

### Common Problems

1. **Container Won't Start:**
   ```bash
   # Check logs
   docker-compose logs backend
   
   # Check configuration
   docker-compose config
   ```

2. **Service Discovery Issues:**
   ```bash
   # Test network connectivity
   docker-compose exec backend ping redis
   
   # Check DNS resolution
   docker-compose exec backend nslookup redis
   ```

3. **Performance Issues:**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Check health endpoints
   curl http://localhost:8000/api/v1/health/comprehensive
   ```

### Deployment Checklist

- [ ] Environment variables configured
- [ ] Secrets properly managed
- [ ] Database initialized and migrated
- [ ] Redis accessible
- [ ] Health checks passing
- [ ] SSL/TLS configured (production)
- [ ] Monitoring and logging set up
- [ ] Backup procedures in place
- [ ] Load balancer configured (if applicable)
- [ ] DNS records updated
- [ ] Firewall rules configured

This comprehensive deployment guide provides multiple options for deploying the AI PKM Tool across different environments and scales. Choose the deployment method that best fits your requirements and infrastructure.