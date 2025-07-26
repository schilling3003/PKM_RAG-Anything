# OpenAI API Integration

This document describes the OpenAI API integration implemented for the AI PKM Tool.

## Overview

The OpenAI integration provides:
- Centralized API key and configuration management
- Connectivity testing and health checks
- Graceful fallback behavior when API is unavailable
- Integration with LightRAG and other AI services

## Configuration

### Environment Variables

Set the OpenAI API key in one of these ways:

1. **Environment variable** (recommended):
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. **In .env file**:
   ```bash
   echo "OPENAI_API_KEY=your-api-key-here" >> .env
   ```

3. **Custom base URL** (optional):
   ```bash
   export OPENAI_BASE_URL="https://your-custom-endpoint.com/v1"
   ```

### Model Configuration

Configure AI models in `.env`:
```bash
LLM_MODEL=gpt-4o-mini
VISION_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-large
```

## Usage

### Basic Service Usage

```python
from app.services.openai_service import get_openai_service

# Get the global service instance
service = get_openai_service()

# Check if service is available
if service.is_available():
    # Use OpenAI API
    response = await service.chat_completion([
        {"role": "user", "content": "Hello!"}
    ])
else:
    # Service will automatically use fallback behavior
    response = await service.chat_completion([
        {"role": "user", "content": "Hello!"}
    ])
```

### Health Checks

The integration provides several health check endpoints:

1. **Basic OpenAI health check**:
   ```
   GET /api/v1/monitoring/health/openai
   ```

2. **Connectivity test**:
   ```
   GET /api/v1/monitoring/health/openai/test
   ```

3. **System status**:
   ```
   GET /api/v1/monitoring/system/status
   ```

## Testing

### Run Integration Tests

```bash
cd backend

# Test basic OpenAI service
python test_openai_integration.py

# Test complete integration
python test_openai_complete_integration.py

# Test API endpoints (requires running server)
python test_openai_endpoints.py
```

### Start Development Server

```bash
cd backend
uvicorn app.main:app --reload
```

Then test endpoints:
```bash
curl http://localhost:8000/api/v1/monitoring/health/openai
```

## Fallback Behavior

When OpenAI API is unavailable, the service provides:

1. **Chat Completions**: Returns informative message about service unavailability
2. **Embeddings**: Returns random vectors with correct dimensions
3. **Health Checks**: Reports service status accurately
4. **Error Logging**: Detailed error information for debugging

## Integration with Other Services

### LightRAG Integration

The LightRAG service automatically uses the centralized OpenAI service:

```python
from app.services.lightrag_service import get_lightrag_service

# LightRAG will use OpenAI if available, fallback to mocks otherwise
lightrag = await get_lightrag_service()
```

### Document Processing

Document processing services can use the OpenAI service for:
- Text analysis and extraction
- Image processing with vision models
- Embedding generation for semantic search

## Troubleshooting

### Common Issues

1. **"No OpenAI API key provided"**
   - Set the `OPENAI_API_KEY` environment variable
   - Check that the key starts with `sk-`

2. **"OpenAI API connectivity test failed"**
   - Verify API key is valid
   - Check internet connectivity
   - Verify custom base URL if using one

3. **"Service unavailable"**
   - The service will use fallback behavior
   - Check logs for specific error details
   - Verify API quota and billing status

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
```

### Health Check Commands

```bash
# Check service status
curl http://localhost:8000/api/v1/monitoring/health/openai

# Test connectivity
curl http://localhost:8000/api/v1/monitoring/health/openai/test

# System overview
curl http://localhost:8000/api/v1/monitoring/system/status
```

## Security Notes

- Never commit API keys to version control
- Use environment variables or secure secret management
- Rotate API keys regularly
- Monitor API usage and costs
- Consider rate limiting for production deployments

## Requirements Fulfilled

This implementation fulfills all task requirements:

✅ **Set up OPENAI_API_KEY environment variable**
- Supports environment variables and .env file
- Clear setup instructions and validation

✅ **Configure OpenAI base URL if using custom endpoint**
- Supports custom base URLs
- Falls back to default OpenAI endpoint

✅ **Test OpenAI API connectivity and model access**
- Comprehensive connectivity testing
- Model access validation (LLM, Vision, Embedding)
- Response time measurement

✅ **Implement fallback behavior when API is unavailable**
- Graceful degradation for all API calls
- Informative error messages
- Automatic fallback to mock responses