# Qdrant CMS Development Guide

## Architecture Overview

**Qdrant CMS** is a document management system with vector search capabilities. The system follows a three-tier architecture:

- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS (port 3000)
- **Backend**: FastAPI + SQLAlchemy + Qdrant integration (port 8000)  
- **Vector DB**: Qdrant for semantic search (port 6333)
- **Metadata DB**: SQLite with async SQLAlchemy

### Core Data Flow
1. **Document Upload** → Text extraction (PDF/DOCX) → Recursive chunking (1000 chars, 200 overlap)
2. **Embedding Generation** → Local Sentence Transformers or OpenAI API
3. **Vector Storage** → Qdrant with cosine similarity search
4. **Metadata Storage** → SQLite with relationships (users, documents, versions, shares, analytics)

### Key Services (`backend/app/services/`)
- `qdrant_service.py`: Vector operations and embeddings
- `document_processor.py`: Text extraction and chunking  
- `auth_service.py`: JWT authentication with remember-me (7 days)
- `version_service.py`: Document versioning with rollback
- `share_service.py`: Granular permissions (view/edit/admin)
- `analytics_service.py`: Usage tracking and reporting

## Development Workflow

### Local Development Setup
```bash
# Start all services
docker compose up -d --build

# Create admin user (first time only)
docker compose exec backend python create_admin.py

# Run database migrations (after updates)
docker compose exec backend python migrate_database.py

# Access points
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs  
# Qdrant UI: http://localhost:6333/dashboard
```

### Testing Commands
```bash
# Backend syntax/import tests
cd backend && python test_backend.py

# Frontend E2E tests (Playwright)
cd frontend && npm test

# Run specific test file
npx playwright test tests/login.spec.ts --headed
```

### Configuration Patterns
- **Environment variables** via `pydantic-settings` (see `backend/config.py`)
- **Embedding models**: `all-MiniLM-L6-v2` (default), `paraphrase-MiniLM-L3-v2`, or OpenAI
- **JWT tokens**: 30min standard, 7-day remember-me configurable
- **File limits**: 50MB max, PDF/DOCX only
- **Chunking**: Custom recursive splitter (not LangChain) for lighter dependencies

## Code Patterns & Conventions

### Backend Patterns
- **Service singletons**: Import `qdrant_service`, `document_processor` from services
- **Async database**: Use `AsyncSession` with `async_sessionmaker`
- **Pydantic schemas**: Separate request/response models in `schemas/`
- **Document access control**: Check `is_public` field + user permissions
- **Version snapshots**: Store `tags_snapshot`, `is_public_snapshot` on changes

### Frontend Patterns  
- **API client**: Centralized in `lib/api.ts` with Axios interceptors
- **TypeScript interfaces**: Match backend Pydantic schemas exactly
- **JWT storage**: `localStorage` with automatic header injection
- **Search results**: Grouped by document (no duplicates) with chunk highlighting
- **Document preview**: `<mark>` elements for yellow highlights (`bg-yellow-200`)

### Database Relationships
```python
# Core document model with all relationships
Document:
  - chunks: DocumentChunk[] (cascade delete)
  - versions: DocumentVersion[] (cascade delete) 
  - shares: DocumentShare[] (cascade delete)
  - analytics: DocumentAnalytics[] (cascade delete)
  - favorites: DocumentFavorite[] (cascade delete)
```

### Common Tasks

#### Adding New Document Feature
1. Add fields to `models.py` Document model
2. Update `schemas.py` with request/response types
3. Create service method in appropriate service file
4. Add API endpoint in `api/documents.py`
5. Update frontend `api.ts` types and functions
6. Add UI components in dashboard page

#### Modifying Search Behavior
- Update `qdrant_service.py` for vector operations
- Modify `search.py` API for result formatting  
- Change frontend search UI in `dashboard/page.tsx`
- Test with `test_search_integration.py`

#### Database Schema Changes
1. Update models in `models.py`
2. Create migration script in `migrate_database.py`
3. Run migration: `docker compose exec backend python migrate_database.py`
4. Update TypeScript types to match

### File Organization Examples
```
# Document upload flow
frontend/app/dashboard/page.tsx → api.ts → 
backend/app/api/documents.py → document_processor.py → qdrant_service.py →
models.py (Document/DocumentChunk) → database.py

# Search flow  
frontend → api/search/semantic → backend/api/search.py → qdrant_service.py
```

### Error Handling
- **Backend**: FastAPI automatic validation, custom HTTPExceptions
- **Frontend**: Try/catch blocks, user-friendly error messages
- **Database**: Async context managers, transaction rollbacks

### Security Notes
- **JWT authentication** with bcrypt password hashing
- **Document permissions**: Owner-only by default, explicit sharing required
- **File validation**: Type checking, size limits, content scanning
- **CORS**: Configured for localhost development

### Performance Considerations
- **Vector search**: Batched embedding generation, configurable top-k
- **Database**: Async queries, indexed fields (user_id, document_id, timestamps)
- **Chunking**: 1000-char chunks with 200-char overlap for context preservation
- **Caching**: None implemented (SQLite limitation)

### Deployment Notes
- **Docker production**: Use `docker-compose.prod.yml` 
- **Environment variables**: Set `SECRET_KEY`, database URLs for production
- **Qdrant persistence**: Named volumes for data retention
- **Static files**: Nginx proxy recommended for production frontend</content>
<parameter name="filePath">d:\qdrant-cms\.github\copilot-instructions.md