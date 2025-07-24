# Development Guide

This guide covers setting up the development environment for the AI PKM Tool.

## Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for local development)
- Node.js 18+ (for local development)
- Git

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ai-pkm-tool
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start development environment:**
   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Redis: localhost:6379

## Local Development (without Docker)

### Backend Setup

1. **Create virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Redis:**
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

4. **Run the backend:**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Start Celery worker (in another terminal):**
   ```bash
   celery -A app.tasks.celery_app worker --loglevel=info
   ```

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

## Project Structure

```
ai-pkm-tool/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   └── tasks/          # Celery tasks
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── types/          # TypeScript types
│   └── package.json        # Node dependencies
└── docs/                   # Documentation
```

## Development Workflow

### Git Workflow

1. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit regularly:**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Push and create pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

Use conventional commits:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `perf:` - Performance improvements
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### Testing

**Backend tests:**
```bash
cd backend
pytest
```

**Frontend tests:**
```bash
cd frontend
npm test
```

**End-to-end tests:**
```bash
npm run test:e2e
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example`):

- `OPENAI_API_KEY` - OpenAI API key for AI features
- `DATABASE_URL` - SQLite database path
- `REDIS_URL` - Redis connection URL
- `CHROMA_DB_PATH` - ChromaDB storage path
- `RAG_STORAGE_DIR` - RAG-Anything storage directory

### AI Model Configuration

The application supports various AI models:

- **LLM Models**: GPT-4, GPT-3.5, or local models
- **Vision Models**: GPT-4V for image processing
- **Embedding Models**: OpenAI embeddings or local alternatives

## Debugging

### Backend Debugging

1. **Enable debug mode:**
   ```bash
   export DEBUG=true
   ```

2. **View logs:**
   ```bash
   docker-compose -f docker-compose.dev.yml logs -f backend
   ```

3. **Access database:**
   ```bash
   sqlite3 data/pkm.db
   ```

### Frontend Debugging

1. **React DevTools**: Install browser extension
2. **TanStack Query DevTools**: Available in development mode
3. **Console logs**: Check browser developer tools

## Common Issues

### Port Conflicts

If ports are already in use:
```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# Kill the process
kill -9 <PID>
```

### Database Issues

Reset database:
```bash
rm -rf data/pkm.db
# Restart the application to recreate
```

### Redis Connection Issues

Restart Redis:
```bash
docker-compose -f docker-compose.dev.yml restart redis
```

## Performance Tips

1. **Use Docker volumes** for persistent data
2. **Enable hot reloading** in development
3. **Use Redis caching** for frequently accessed data
4. **Monitor memory usage** during document processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

See [Contributing Guidelines](contributing.md) for more details.