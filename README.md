# AI-Focused Personal Knowledge Management Tool

A modern, self-hosted Personal Knowledge Management (PKM) system that combines the intuitive interface patterns of Obsidian and Logseq with advanced AI capabilities for multimodal document processing, semantic search, and knowledge graph visualization.

## Features

### ✅ Implemented
- **Document Management**: Complete upload, processing, and metadata management interface
- **Multimodal Document Processing**: Support for text, images, PDFs, audio, and video using RAG-Anything with MinerU 2.0
- **AI-Powered Search**: Semantic search and RAG-based question answering with multiple modes
- **Notes System**: Markdown editor with wiki-style linking and CRUD operations
- **Knowledge Graph Backend**: LightRAG-powered graph construction and querying
- **PDF Viewer**: Integrated PDF viewing with navigation, search, zoom, and annotation capabilities
- **Real-time Processing**: Background document processing with live status updates
- **Health Monitoring**: Comprehensive health check endpoints for all services
- **OpenAI Integration**: Complete integration with OpenAI API for embeddings and chat completions
- **Error Handling**: Robust error handling and recovery mechanisms
- **Testing Suite**: Comprehensive backend testing with unit, integration, and load tests
- **Easy Deployment**: Docker-based deployment for single-user or small team use
- **Privacy-Focused**: All processing occurs locally or through user-configured services

### 🚧 In Development
- **Knowledge Graph Visualization**: Interactive D3.js-based graph visualization (backend ready)
- **Advanced Search Interface**: Unified search with filtering and result display

### 📋 Planned
- **WebSocket Integration**: Real-time collaborative features
- **Performance Optimizations**: Caching and query optimization
- **Frontend Testing**: Complete test coverage for React components

## Architecture

- **Backend**: Python FastAPI with RAG-Anything, LightRAG, and MinerU 2.0
- **Frontend**: React with ShadCN UI components and Tailwind CSS
- **Storage**: SQLite for metadata, ChromaDB for vectors, NetworkX for graphs
- **Database**: Automated migration system for schema updates
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

The application includes an automated database migration system that handles schema updates automatically on startup. See [Development Guide](docs/development.md) for detailed setup instructions.

## Documentation

### Setup and Installation
- [Installation Guide](docs/installation-guide.md) - Comprehensive setup instructions for all environments
- [Environment Variables](docs/environment-variables.md) - Complete configuration reference
- [Deployment Guide](docs/deployment-guide.md) - Production deployment across different platforms

### Operations and Maintenance
- [Health Endpoints](docs/health-endpoints.md) - Monitoring and health check documentation
- [Troubleshooting Guide](docs/troubleshooting-guide.md) - Common issues and solutions

### Development and Features
- [Development Guide](docs/development.md) - Setup and development workflow
- [Implementation Status](docs/implementation-status.md) - Current feature status and roadmap
- [PDF Viewer Guide](docs/pdf-viewer.md) - PDF viewing and annotation features

## License

MIT License - see [LICENSE](LICENSE) file for details.