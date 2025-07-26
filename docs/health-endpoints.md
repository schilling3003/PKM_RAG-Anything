# Health Check Endpoints Documentation

This document provides comprehensive documentation for the health check endpoints in the AI PKM Tool, including usage examples, response formats, and integration guidance.

## Overview

The AI PKM Tool provides a comprehensive health monitoring system that checks all critical services and dependencies. These endpoints are designed for:

- **System Monitoring**: Automated health checks for production systems
- **Troubleshooting**: Quick diagnosis of service issues
- **Load Balancer Integration**: Health checks for load balancer configuration
- **CI/CD Pipelines**: Verification of deployment success
- **Development**: Quick status checks during development

## Base URL

All health check endpoints are available under:
```
http://localhost:8000/api/v1/health/
```

## Individual Service Health Checks

### 1. Redis Health Check

**Endpoint:** `GET /api/v1/health/redis`

Monitors Redis connectivity and basic operations.

**Response Example:**
```json
{
  "service": "redis",
  "status": "healthy",
  "details": {
    "connection_status": "connected",
    "redis_version": "7.0.11",
    "memory_usage": "2.1MB",
    "connected_clients": 3,
    "test_operations": {
      "ping": "success",
      "set_test": "success",
      "get_test": "success"
    }
  },
  "timestamp": "2024-01-15T10:30:00.000Z",
  "response_time_ms": 12.5
}
```

**Status Criteria:**
- **Healthy**: Redis is accessible and all test operations succeed
- **Unhealthy**: Redis is not accessible or test operations fail

**Common Issues:**
- Redis server not running
- Network connectivity problems
- Redis configuration issues

### 2. Celery Health Check

**Endpoint:** `GET /api/v1/health/celery`

Monitors Celery worker status and task processing capability.

**Response Example:**
```json
{
  "service": "celery",
  "status": "healthy",
  "details": {
    "active_workers": 2,
    "registered_tasks": [
      "app.tasks.process_document",
      "app.tasks.generate_embeddings",
      "app.tasks.build_knowledge_graph"
    ],
    "worker_info": {
      "celery@worker1": {
        "status": "online",
        "active_tasks": 1,
        "processed_tasks": 45
      }
    },
    "test_task": {
      "status": "success",
      "execution_time_ms": 150
    }
  },
  "timestamp": "2024-01-15T10:30:00.000Z",
  "response_time_ms": 200.3
}
```

**Status Criteria:**
- **Healthy**: At least one active worker and test task succeeds
- **Degraded**: Workers available but test task fails
- **Unhealthy**: No active workers or critical failures

### 3. LightRAG Health Check

**Endpoint:** `GET /api/v1/health/lightrag`

Monitors LightRAG knowledge graph functionality.

**Response Example:**
```json
{
  "service": "lightrag",
  "status": "healthy",
  "details": {
    "initialization_status": "initialized",
    "working_directory": "./data/rag_storage",
    "directory_exists": true,
    "directory_writable": true,
    "storage_components": {
      "graph_storage": "available",
      "vector_storage": "available",
      "text_storage": "available"
    },
    "openai_service_status": "available",
    "knowledge_graph_stats": {
      "total_entities": 1250,
      "total_relationships": 3400,
      "last_updated": "2024-01-15T09:45:00.000Z"
    }
  },
  "timestamp": "2024-01-15T10:30:00.000Z",
  "response_time_ms": 85.7
}
```

**Status Criteria:**
- **Healthy**: LightRAG initialized and all storage components available
- **Degraded**: Initialized but some components have issues
- **Unhealthy**: Not initialized or critical storage failures

### 4. RAG-Anything/MinerU Health Check

**Endpoint:** `GET /api/v1/health/raganything`

Monitors RAG-Anything multimodal processing and MinerU availability.

**Response Example:**
```json
{
  "service": "raganything_mineru",
  "status": "healthy",
  "details": {
    "raganything_version": "0.1.0",
    "mineru_available": true,
    "mineru_version": "2.0.1",
    "device_info": {
      "configured_device": "cuda",
      "cuda_available": true,
      "gpu_count": 1,
      "gpu_memory": "8GB"
    },
    "supported_formats": [
      "pdf", "docx", "txt", "md", "jpg", "png", "mp3", "mp4"
    ],
    "configuration": {
      "backend": "pipeline",
      "language": "en",
      "batch_size": 8
    },
    "test_processing": {
      "status": "success",
      "test_file": "sample.pdf",
      "processing_time_ms": 450
    }
  },
  "timestamp": "2024-01-15T10:30:00.000Z",
  "response_time_ms": 500.2
}
```

**Status Criteria:**
- **Healthy**: RAG-Anything and MinerU available, test processing succeeds
- **Degraded**: Available but running on CPU instead of GPU
- **Unhealthy**: Not available or test processing fails

### 5. OpenAI Health Check

**Endpoint:** `GET /api/v1/health/openai`

Monitors OpenAI API configuration and connectivity.

**Response Example:**
```json
{
  "service": "openai",
  "status": "healthy",
  "details": {
    "api_key_configured": true,
    "api_key_format_valid": true,
    "base_url": "https://api.openai.com/v1",
    "connectivity_test": {
      "status": "success",
      "response_time_ms": 250,
      "model_tested": "gpt-4o-mini"
    },
    "configured_models": {
      "llm_model": "gpt-4o-mini",
      "vision_model": "gpt-4o",
      "embedding_model": "text-embedding-3-large"
    },
    "rate_limit_info": {
      "requests_remaining": 4950,
      "tokens_remaining": 995000
    }
  },
  "timestamp": "2024-01-15T10:30:00.000Z",
  "response_time_ms": 300.1
}
```

**Status Criteria:**
- **Healthy**: API key configured and connectivity test passes
- **Degraded**: API key not configured (fallback mode available)
- **Unhealthy**: API key configured but connectivity fails

### 6. Storage Health Check

**Endpoint:** `GET /api/v1/health/storage`

Monitors file system accessibility for all required directories.

**Response Example:**
```json
{
  "service": "storage",
  "status": "healthy",
  "details": {
    "directories": {
      "upload_dir": {
        "path": "./data/uploads",
        "exists": true,
        "writable": true,
        "free_space_gb": 45.2
      },
      "processed_dir": {
        "path": "./data/processed",
        "exists": true,
        "writable": true,
        "free_space_gb": 45.2
      },
      "rag_storage_dir": {
        "path": "./data/rag_storage",
        "exists": true,
        "writable": true,
        "free_space_gb": 45.2
      },
      "chroma_db_path": {
        "path": "./data/chroma_db",
        "exists": true,
        "writable": true,
        "free_space_gb": 45.2
      },
      "database_dir": {
        "path": "./data",
        "exists": true,
        "writable": true,
        "free_space_gb": 45.2
      }
    },
    "test_operations": {
      "write_test": "success",
      "read_test": "success",
      "delete_test": "success"
    }
  },
  "timestamp": "2024-01-15T10:30:00.000Z",
  "response_time_ms": 25.8
}
```

**Status Criteria:**
- **Healthy**: All directories exist, are writable, and have sufficient space
- **Degraded**: Some directories have warnings (low space, permissions)
- **Unhealthy**: Critical directories missing or not writable

## Comprehensive Health Check

### Overall System Health

**Endpoint:** `GET /api/v1/health/comprehensive`

Runs all individual health checks concurrently and provides system overview.

**Response Example:**
```json
{
  "overall_status": "healthy",
  "services": {
    "redis": {
      "service": "redis",
      "status": "healthy",
      "response_time_ms": 12.5
    },
    "celery": {
      "service": "celery",
      "status": "healthy",
      "response_time_ms": 200.3
    },
    "lightrag": {
      "service": "lightrag",
      "status": "healthy",
      "response_time_ms": 85.7
    },
    "raganything": {
      "service": "raganything_mineru",
      "status": "degraded",
      "response_time_ms": 500.2
    },
    "openai": {
      "service": "openai",
      "status": "degraded",
      "response_time_ms": 300.1
    },
    "storage": {
      "service": "storage",
      "status": "healthy",
      "response_time_ms": 25.8
    }
  },
  "summary": {
    "total_services": 6,
    "healthy": 4,
    "degraded": 2,
    "unhealthy": 0
  },
  "timestamp": "2024-01-15T10:30:00.000Z",
  "total_response_time_ms": 1124.6
}
```

**Overall Status Logic:**
- **Healthy**: All services are healthy
- **Degraded**: Some services degraded, none unhealthy
- **Unhealthy**: One or more services are unhealthy

## Usage Examples

### Basic Health Monitoring

```bash
# Check overall system health
curl http://localhost:8000/api/v1/health/comprehensive

# Check specific service
curl http://localhost:8000/api/v1/health/redis

# Check with verbose output
curl -s http://localhost:8000/api/v1/health/comprehensive | jq '.'
```

### Automated Monitoring Script

```bash
#!/bin/bash
# health_monitor.sh

ENDPOINT="http://localhost:8000/api/v1/health/comprehensive"
ALERT_EMAIL="admin@example.com"

# Check health status
RESPONSE=$(curl -s "$ENDPOINT")
STATUS=$(echo "$RESPONSE" | jq -r '.overall_status')

if [ "$STATUS" != "healthy" ]; then
    echo "System health issue detected: $STATUS"
    echo "$RESPONSE" | jq '.' | mail -s "PKM Tool Health Alert" "$ALERT_EMAIL"
    exit 1
fi

echo "System is healthy"
exit 0
```

### Load Balancer Configuration

**Nginx Example:**
```nginx
upstream pkm_backend {
    server backend1:8000;
    server backend2:8000;
}

server {
    location /health {
        proxy_pass http://pkm_backend/api/v1/health/comprehensive;
        proxy_set_header Host $host;
    }
    
    location / {
        proxy_pass http://pkm_backend;
        # Health check for load balancing
        health_check uri=/api/v1/health/comprehensive;
    }
}
```

**HAProxy Example:**
```
backend pkm_servers
    balance roundrobin
    option httpchk GET /api/v1/health/comprehensive
    http-check expect status 200
    server backend1 backend1:8000 check
    server backend2 backend2:8000 check
```

### Docker Health Checks

**docker-compose.yml:**
```yaml
services:
  backend:
    build: ./backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/comprehensive"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Kubernetes Health Checks

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pkm-backend
spec:
  template:
    spec:
      containers:
      - name: backend
        image: pkm-backend:latest
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
```

## Monitoring Integration

### Prometheus Metrics

The health endpoints can be integrated with Prometheus for metrics collection:

```python
# Example metrics exporter
from prometheus_client import Gauge, Counter
import requests

health_status = Gauge('pkm_service_health', 'Service health status', ['service'])
response_time = Gauge('pkm_service_response_time', 'Service response time', ['service'])

def collect_metrics():
    response = requests.get('http://localhost:8000/api/v1/health/comprehensive')
    data = response.json()
    
    for service_name, service_data in data['services'].items():
        status_value = {'healthy': 1, 'degraded': 0.5, 'unhealthy': 0}[service_data['status']]
        health_status.labels(service=service_name).set(status_value)
        response_time.labels(service=service_name).set(service_data['response_time_ms'])
```

### Grafana Dashboard

Example Grafana queries for health monitoring:

```promql
# Service health status
pkm_service_health

# Average response time
avg(pkm_service_response_time)

# Services with issues
pkm_service_health < 1
```

### Alerting Rules

**Prometheus Alerting Rules:**
```yaml
groups:
- name: pkm_health
  rules:
  - alert: PKMServiceUnhealthy
    expr: pkm_service_health == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "PKM service {{ $labels.service }} is unhealthy"
      
  - alert: PKMServiceDegraded
    expr: pkm_service_health == 0.5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "PKM service {{ $labels.service }} is degraded"
```

## Response Format Specification

All health check endpoints follow this standard format:

```typescript
interface HealthResponse {
  service: string;                    // Service identifier
  status: 'healthy' | 'degraded' | 'unhealthy';
  details: Record<string, any>;       // Service-specific details
  timestamp: string;                  // ISO 8601 timestamp
  response_time_ms: number;           // Response time in milliseconds
}

interface ComprehensiveHealthResponse {
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
  services: Record<string, HealthResponse>;
  summary: {
    total_services: number;
    healthy: number;
    degraded: number;
    unhealthy: number;
  };
  timestamp: string;
  total_response_time_ms: number;
}
```

## Error Handling

Health check endpoints handle errors gracefully:

```json
{
  "service": "redis",
  "status": "unhealthy",
  "details": {
    "error": "Connection refused",
    "error_code": "CONNECTION_ERROR",
    "last_successful_check": "2024-01-15T10:25:00.000Z",
    "retry_count": 3
  },
  "timestamp": "2024-01-15T10:30:00.000Z",
  "response_time_ms": 5000.0
}
```

## Security Considerations

- Health endpoints don't expose sensitive information
- No authentication required for basic health status
- Detailed error information only in development mode
- Rate limiting applied to prevent abuse
- CORS configured for cross-origin requests

## Performance Considerations

- Health checks are designed to be fast (< 1 second typically)
- Concurrent execution for comprehensive checks
- Caching of expensive operations
- Timeout protection for external service checks
- Minimal resource usage during checks

## Best Practices

### For Monitoring Systems
1. Use comprehensive endpoint for overall status
2. Monitor individual services for specific alerts
3. Set appropriate timeout values (10-30 seconds)
4. Implement exponential backoff for retries
5. Cache results for high-frequency checks

### For Development
1. Check health endpoints after code changes
2. Use health checks in CI/CD pipelines
3. Monitor response times during load testing
4. Verify all services before deployment

### For Production
1. Set up automated monitoring and alerting
2. Use health checks for load balancer configuration
3. Monitor trends in response times
4. Set up log aggregation for health check failures
5. Implement escalation procedures for critical failures

This comprehensive health monitoring system ensures reliable operation and quick issue resolution for the AI PKM Tool.