# Setting OpenAI API Key for Docker Deployment

## Quick Setup

There are several ways to set your OpenAI API key for Docker deployment:

### Method 1: Using .env File (Recommended)

1. **Edit the `.env` file** in the root directory:
   ```bash
   # Edit .env file
   OPENAI_API_KEY=your_actual_api_key_here
   OPENAI_BASE_URL=https://api.openai.com/v1
   LLM_MODEL=gpt-4o-mini
   VISION_MODEL=gpt-4o
   EMBEDDING_MODEL=text-embedding-3-large
   ```

2. **Start Docker services**:
   ```bash
   # Development
   python scripts/start-docker.py --mode dev --build
   
   # Production
   python scripts/start-docker.py --mode prod --build
   ```

### Method 2: Environment Variables

Set the environment variable before running Docker:

```bash
# Windows (Command Prompt)
set OPENAI_API_KEY=your_actual_api_key_here
python scripts/start-docker.py --mode dev --build

# Windows (PowerShell)
$env:OPENAI_API_KEY="your_actual_api_key_here"
python scripts/start-docker.py --mode dev --build

# macOS/Linux
export OPENAI_API_KEY=your_actual_api_key_here
python scripts/start-docker.py --mode dev --build
```

### Method 3: Docker Compose Override

Create a `docker-compose.override.yml` file:

```yaml
version: '3.8'

services:
  backend:
    environment:
      - OPENAI_API_KEY=your_actual_api_key_here
      
  celery:
    environment:
      - OPENAI_API_KEY=your_actual_api_key_here
```

### Method 4: Docker Secrets (Production)

For production deployments, use Docker secrets:

1. **Create a secret file**:
   ```bash
   echo "your_actual_api_key_here" | docker secret create openai_api_key -
   ```

2. **Update docker-compose.yml**:
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

## Verification

After setting up, verify the API key is working:

1. **Check health endpoint**:
   ```bash
   curl http://localhost:8000/health/openai
   ```

2. **Check logs**:
   ```bash
   # View backend logs
   docker-compose logs backend
   
   # View celery logs
   docker-compose logs celery
   ```

3. **Use health check script**:
   ```bash
   python scripts/health-check.py --service ai
   ```

## Troubleshooting

### API Key Not Found
- Ensure the `.env` file exists and contains `OPENAI_API_KEY=your_key`
- Restart Docker services after changing environment variables
- Check that the `.env` file is in the same directory as `docker-compose.yml`

### Invalid API Key
- Verify your API key is correct and active
- Check OpenAI account billing and usage limits
- Ensure the API key has the necessary permissions

### Services Not Starting
- Check Docker logs: `docker-compose logs backend`
- Verify all environment variables are set correctly
- Ensure Docker has access to the `.env` file

## Security Best Practices

1. **Never commit API keys to version control**
2. **Use different API keys for development and production**
3. **Regularly rotate API keys**
4. **Monitor API usage and set billing alerts**
5. **Use Docker secrets in production environments**

## Example Complete Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd ai-pkm-tool

# 2. Set up environment file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Start Docker development environment
python scripts/start-docker.py --mode dev --build

# 4. Verify setup
python scripts/health-check.py

# 5. Access application
# Frontend: http://localhost:3000 (if available)
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

The Docker Compose files now automatically load environment variables from the `.env` file, making it easy to configure your OpenAI API key and other settings.