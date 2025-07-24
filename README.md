# AI-Focused Personal Knowledge Management Tool

A modern, self-hosted Personal Knowledge Management (PKM) system that combines the intuitive interface patterns of Obsidian and Logseq with advanced AI capabilities for multimodal document processing, semantic search, and knowledge graph visualization.

## Features

- **Obsidian-like Interface**: Familiar markdown editor with wiki-style linking
- **Multimodal Document Processing**: Support for text, images, PDFs, audio, and video using RAG-Anything with MinerU 2.0
- **AI-Powered Search**: Semantic search and RAG-based question answering
- **Knowledge Graph**: Interactive visualization of relationships between notes and documents
- **PDF Viewer**: Integrated PDF viewing with search and navigation
- **Easy Deployment**: Docker-based deployment for single-user or small team use
- **Privacy-Focused**: All processing occurs locally or through user-configured services

## Architecture

- **Backend**: Python FastAPI with RAG-Anything, LightRAG, and MinerU 2.0
- **Frontend**: React with ShadCN UI components and Tailwind CSS
- **Storage**: SQLite for metadata, ChromaDB for vectors, NetworkX for graphs
- **Processing**: Celery + Redis for asynchronous document processing

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for development)
- Node.js 18+ (for development)

### Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-pkm-tool
```

2. Start development environment:
```bash
docker-compose -f docker-compose.dev.yml up
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Production Deployment

```bash
docker-compose up -d
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
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── types/          # TypeScript types
│   ├── public/             # Static assets
│   ├── package.json        # Node dependencies
│   └── Dockerfile
├── docker-compose.yml      # Production compose
├── docker-compose.dev.yml  # Development compose
└── docs/                   # Documentation
```

## Development

See [Development Guide](docs/development.md) for detailed setup instructions.

## Documentation

- [User Guide](docs/user-guide.md)
- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing](docs/contributing.md)

## License

MIT License - see [LICENSE](LICENSE) file for details.