# Project Structure

## Root Directory Layout

```
ai-pkm-tool/
├── backend/                 # FastAPI backend application
├── frontend/               # React frontend application
├── data/                   # Persistent data storage
├── docs/                   # Project documentation
├── temp_lightrag/          # LightRAG integration (temporary)
├── rag_storage/            # RAG processing storage
├── docker-compose.yml      # Production deployment
├── docker-compose.dev.yml  # Development environment
└── README.md              # Project overview
```

## Backend Structure (`backend/`)

```
backend/
├── app/
│   ├── api/               # API route definitions
│   │   └── endpoints/     # Individual endpoint modules
│   ├── core/              # Core configuration and utilities
│   ├── models/            # Data models (SQLAlchemy & Pydantic)
│   ├── services/          # Business logic layer
│   └── tasks/             # Celery background tasks
├── tests/                 # Backend test suite
├── data/                  # Local data storage
├── requirements.txt       # Python dependencies
├── Dockerfile            # Production container
└── Dockerfile.dev       # Development container
```

## Frontend Structure (`frontend/`)

```
frontend/
├── src/
│   ├── components/        # Reusable React components
│   ├── hooks/            # Custom React hooks
│   ├── pages/            # Page-level components
│   ├── services/         # API service layer and mock data
│   ├── types/            # TypeScript type definitions
│   └── test/             # Test utilities and setup
├── public/               # Static assets
├── package.json          # Node.js dependencies
├── vite.config.ts        # Vite build configuration
├── tailwind.config.js    # Tailwind CSS configuration
└── tsconfig.json         # TypeScript configuration
```

## Architecture Patterns

### Backend Patterns

- **Layered Architecture**: API → Services → Models → Database
- **Dependency Injection**: Services injected into API endpoints
- **Repository Pattern**: Database access abstracted through services
- **Async/Await**: Consistent async patterns throughout
- **Error Handling**: Centralized exception handling with custom exceptions

### Frontend Patterns

- **Component Composition**: Small, reusable components
- **Custom Hooks**: Business logic extracted to hooks
- **Service Layer**: API calls abstracted to service modules
- **Type Safety**: Comprehensive TypeScript usage
- **State Management**: TanStack Query for server state, React state for UI

## File Naming Conventions

### Backend
- **Modules**: `snake_case.py` (e.g., `rag_service.py`)
- **Classes**: `PascalCase` (e.g., `RAGService`)
- **Functions**: `snake_case` (e.g., `process_rag_query`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_TOKENS`)

### Frontend
- **Components**: `PascalCase.tsx` (e.g., `SearchResults.tsx`)
- **Hooks**: `camelCase.ts` starting with `use` (e.g., `useSearch.ts`)
- **Services**: `camelCase.ts` (e.g., `apiService.ts`)
- **Types**: `camelCase.ts` (e.g., `searchTypes.ts`)

## Data Storage Organization

```
data/
├── pkm.db                # Main SQLite database
├── chroma_db/            # ChromaDB vector storage
├── rag_storage/          # LightRAG knowledge graph data
├── uploads/              # User uploaded files
└── processed/            # Processed document outputs
```

## Configuration Management

- **Environment Variables**: `.env` files for configuration
- **Settings**: Centralized in `backend/app/core/config.py`
- **Docker**: Environment-specific compose files
- **Frontend**: Vite proxy configuration for API routing

## Import Conventions

### Backend
```python
# Standard library imports first
import os
from typing import Dict, List

# Third-party imports
from fastapi import APIRouter
from sqlalchemy import Column

# Local imports
from app.services.rag_service import rag_service
from app.models.schemas import RAGResponse
```

### Frontend
```typescript
// React imports first
import React from 'react'
import { useState, useEffect } from 'react'

// Third-party imports
import { useQuery } from '@tanstack/react-query'

// Local imports
import { SearchResults } from '@/components/SearchResults'
import { useSearch } from '@/hooks/useSearch'
import type { SearchQuery } from '@/types/searchTypes'
```

## Testing Structure

- **Backend**: Tests mirror source structure in `tests/` directory
- **Frontend**: Tests co-located with components (`*.test.tsx`)
- **Integration**: End-to-end tests in separate directory
- **Fixtures**: Shared test data in dedicated fixtures modules
- **Mock Data**: Development mock data in `frontend/src/services/mock-data.ts`