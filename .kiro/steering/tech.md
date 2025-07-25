# Technology Stack

## Backend Stack

- **Framework**: FastAPI (Python 3.9+)
- **Database**: SQLite with SQLAlchemy ORM
- **Vector Database**: ChromaDB for embeddings
- **Task Queue**: Celery with Redis
- **AI/ML Libraries**:
  - LightRAG for knowledge graph RAG
  - RAG-Anything for multimodal processing
  - MinerU 2.0 for document extraction
  - OpenAI API (user-configurable)
- **Graph Processing**: NetworkX
- **Document Processing**: PyMuPDF, pdfplumber, Pillow

## Frontend Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Components**: ShadCN UI with Tailwind CSS
- **State Management**: TanStack Query (React Query)
- **HTTP Client**: Axios
- **Visualization**: D3.js for knowledge graphs
- **Icons**: Lucide React
- **Markdown**: react-markdown with syntax highlighting

## Infrastructure

- **Containerization**: Docker with Docker Compose
- **Web Server**: Nginx (production)
- **Development Server**: Uvicorn with hot reload
- **Cache**: Redis for session and query caching

## Common Commands

### Development
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# Backend only (local)
cd backend && uvicorn app.main:app --reload
celery -A app.tasks.celery_app worker --loglevel=info

# Frontend only (local)
cd frontend && npm run dev

# Run tests
cd backend && pytest
cd frontend && npm test
```

### Production
```bash
# Deploy production stack
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Database Management
```bash
# Access SQLite database
sqlite3 data/pkm.db

# Reset database (development)
rm -rf data/pkm.db
```

## Code Quality Tools

- **Backend**: Black (formatting), isort (imports), flake8 (linting), mypy (type checking)
- **Frontend**: ESLint, TypeScript compiler
- **Testing**: pytest (backend), Vitest (frontend)

## Environment Configuration

Key environment variables:
- `OPENAI_API_KEY`: AI model access
- `DATABASE_URL`: SQLite database path
- `REDIS_URL`: Redis connection
- `CHROMA_DB_PATH`: Vector database storage
- `RAG_STORAGE_DIR`: Document processing storage