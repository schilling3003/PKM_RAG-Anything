# Health Check Endpoints Documentation

This document describes the comprehensive health check endpoints implemented for the AI PKM Tool backend.

## Overview

The health check system provides detailed monitoring of all critical services and dependencies required for the AI PKM Tool to function properly. Each endpoint returns structured information about service status, performance metrics, and diagnostic details.

## Available Endpoints

### Individual Service Health Checks

#### 1. Redis Health Check
**Endpoint:** `GET /api/v1/health/redis`

Checks Redis connectivity and basic operations.

**Response Fields:**
- `service`: "redis"
- `status`: "healthy" | "degraded" | "unhealthy"
- `details`: Redis connection info, version, memory usage, test operations
- `response_time_ms`: Response time in milliseconds

**Healthy Status Criteria:**
- Redis server is accessible
- Basic ping operation succeeds
- Set/get operations work correctly

#### 2. Celery Health Check
**Endpoint:** `GET /api/v1/health/celery`

Checks Celery worker status and task processing capability.

**Response Fields:**
- `service`: "celery"
- `status`: "healthy" | "degraded" | "unhealthy"
- `details`: Active workers, registered tasks, task test results
- `response_time_ms`: Response time in milliseconds

**Healthy Status Criteria:**
- At least one active Celery worker
- Workers can process test tasks successfully
- Task queue is operational

#### 3. LightRAG Health Check
**Endpoint:** `GET /api/v1/health/lightrag`

Checks LightRAG knowledge graph functionality.

**Response Fields:**
- `service`: "lightrag"
- `status`: "healthy" | "degraded" | "unhealthy"
- `details`: Initialization status, working directory, storage info, OpenAI service status
- `response_time_ms`: Response time in milliseconds

**Healthy Status Criteria:**
- LightRAG service is initialized
- Working directory exists and is accessible
- Storage components are functional

#### 4. RAG-Anything/MinerU Health Check
**Endpoint:** `GET /api/v1/health/raganything`

Checks RAG-Anything multimodal processing and MinerU availability.

**Response Fields:**
- `service`: "raganything_mineru"
- `status`: "healthy" | "degraded" | "unhealthy"
- `details`: RAG-Anything version, MinerU availability, CUDA status, configuration
- `response_time_ms`: Response time in milliseconds

**Healthy Status Criteria:**
- RAG-Anything package is installed
- MinerU parser is available and functional
- Configuration files are accessible

#### 5. OpenAI Health Check
**Endpoint:** `GET /api/v1/health/openai`

Checks OpenAI API configuration and connectivity.

**Response Fields:**
- `service`: "openai"
- `status`: "healthy" | "degraded" | "unhealthy"
- `details`: Configuration status, API connectivity, model access
- `response_time_ms`: Response time in milliseconds

**Status Criteria:**
- **Healthy**: API key configured and connectivity test passes
- **Degraded**: API key not configured (system can work with fallbacks)
- **Unhealthy**: API key configured but connectivity fails

#### 6. Storage Health Check
**Endpoint:** `GET /api/v1/health/storage`

Checks file system accessibility for all required directories.

**Response Fields:**
- `service`: "storage"
- `status`: "healthy" | "degraded" | "unhealthy"
- `details`: Directory status for uploads, processed files, RAG storage, ChromaDB, database
- `response_time_ms`: Response time in milliseconds

**Healthy Status Criteria:**
- All required directories exist
- Directories are writable
- Write/read test operations succeed

### Comprehensive Health Check

#### Comprehensive Health Check
**Endpoint:** `GET /api/v1/health/comprehensive`

Runs all individual health checks concurrently and provides an overall system status.

**Response Fields:**
- `overall_status`: "healthy" | "degraded" | "unhealthy"
- `services`: Object containing all individual service health responses
- `summary`: Count of services by status (healthy, degraded, unhealthy)
- `timestamp`: When the check was performed

**Overall Status Logic:**
- **Healthy**: All services are healthy
- **Degraded**: Some services are degraded but none are unhealthy
- **Unhealthy**: One or more services are unhealthy

## Response Format

All health check endpoints return responses in this format:

```json
{
  "service": "service_name",
  "status": "healthy|degraded|unhealthy",
  "details": {
    // Service-specific diagnostic information
  },
  "timestamp": "2024-01-01T12:00:00.000Z",
  "response_time_ms": 123.45
}
```

## Status Definitions

- **Healthy**: Service is fully operational and all checks pass
- **Degraded**: Service is operational but with limitations or warnings
- **Unhealthy**: Service is not operational or critical checks fail

## Usage Examples

### Check Overall System Health
```bash
curl http://localhost:8000/api/v1/health/comprehensive
```

### Check Specific Service
```bash
curl http://localhost:8000/api/v1/health/redis
curl http://localhost:8000/api/v1/health/storage
```

### Monitor Service Performance
```bash
# Check response times for all services
for service in redis celery lightrag raganything openai storage; do
  echo "Checking $service..."
  curl -s http://localhost:8000/api/v1/health/$service | jq '.response_time_ms'
done
```

## Integration with Monitoring

These endpoints are designed to be used with monitoring systems:

1. **Uptime Monitoring**: Use `/health/comprehensive` for overall status
2. **Service-Specific Alerts**: Monitor individual endpoints for specific services
3. **Performance Monitoring**: Track `response_time_ms` for performance metrics
4. **Dependency Tracking**: Use detailed information for troubleshooting

## Troubleshooting

### Common Issues

1. **Redis Unhealthy**: 
   - Check if Redis server is running
   - Verify Redis URL configuration
   - Check network connectivity

2. **Celery Unhealthy**:
   - Start Celery worker: `celery -A app.core.celery_app worker --loglevel=info`
   - Check Redis connectivity (Celery depends on Redis)
   - Verify Celery configuration

3. **Storage Unhealthy**:
   - Check directory permissions
   - Verify disk space availability
   - Check if directories exist and are writable

4. **OpenAI Degraded**:
   - Set `OPENAI_API_KEY` environment variable
   - Verify API key validity
   - Check network connectivity to OpenAI API

## Implementation Details

The health check system is implemented in `app/api/endpoints/health.py` and includes:

- Async health check functions for each service
- Concurrent execution for comprehensive checks
- Detailed error handling and reporting
- Performance timing for all checks
- Structured response format for easy parsing

All health checks are designed to be fast (typically < 1 second) and safe to run frequently without impacting system performance.