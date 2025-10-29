# Architecture Overview

## System Architecture

The Qdrant CMS/DMS follows a modern three-tier architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                    (Next.js + React)                         │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Login   │  │ Register │  │Dashboard │  │  Search  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                         ↓                                    │
│                    Axios HTTP Client                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                         Backend                              │
│                      (FastAPI + Python)                      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Layer (FastAPI)                      │  │
│  │  ┌─────────┐  ┌──────────┐  ┌────────┐              │  │
│  │  │  Auth   │  │Documents │  │ Search │              │  │
│  │  └─────────┘  └──────────┘  └────────┘              │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Service Layer                              │  │
│  │  ┌──────────┐  ┌─────────┐  ┌──────────────────┐   │  │
│  │  │   Auth   │  │Document │  │     Qdrant       │   │  │
│  │  │ Service  │  │Processor│  │     Service      │   │  │
│  │  └──────────┘  └─────────┘  └──────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Data Layer                               │  │
│  │  ┌─────────────┐                 ┌────────────────┐ │  │
│  │  │  SQLAlchemy │                 │   Qdrant       │ │  │
│  │  │    (ORM)    │                 │    Client      │ │  │
│  │  └─────────────┘                 └────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────┬──────────────────────────────────┬──────────────┘
           │                                   │
           ↓                                   ↓
    ┌─────────────┐                    ┌──────────────┐
    │   SQLite    │                    │   Qdrant     │
    │  Database   │                    │Vector Store  │
    │ (Metadata)  │                    │(Embeddings)  │
    └─────────────┘                    └──────────────┘
```

## Component Details

### Frontend Components

#### 1. Pages
- **Login Page** (`/login`): User authentication
- **Register Page** (`/register`): New user registration
- **Dashboard** (`/dashboard`): Main application interface with tabs:
  - Documents: List and manage documents
  - Upload: Upload new documents
  - Search: Semantic search interface
  - RAG: Question answering interface

#### 2. API Client (`lib/api.ts`)
- Axios-based HTTP client
- Automatic token injection
- Type-safe API calls
- Error handling

### Backend Components

#### 1. API Layer (`app/api/`)
- **auth.py**: Authentication endpoints (register, login, get user)
- **documents.py**: Document CRUD operations
- **search.py**: Search and RAG endpoints

#### 2. Service Layer (`app/services/`)
- **auth_service.py**: JWT token management, password hashing
- **document_processor.py**: Text extraction, chunking (LangChain)
- **qdrant_service.py**: Vector operations, embedding generation

#### 3. Data Models (`app/models/`)
- **Document**: File metadata, ownership, access control
- **DocumentChunk**: Individual text chunks with Qdrant references
- **Tag**: Document categorization
- **User**: User accounts and authentication

#### 4. Schemas (`app/schemas/`)
- Pydantic models for request/response validation
- Type safety and documentation

## Data Flow

### Document Upload Flow

```
1. User selects file → Frontend
2. FormData created → API Request
3. FastAPI receives file → Validation
4. File saved to disk → Storage
5. Text extracted (PDF/DOCX) → Document Processor
6. Text chunked → LangChain
7. For each chunk:
   a. Generate embedding → Sentence Transformers
   b. Store in Qdrant → Vector DB
   c. Save metadata → SQLite
8. Return document info → Frontend
9. Display success → User
```

### Search Flow

```
1. User enters query → Frontend
2. API Request → Backend
3. Query embedding → Sentence Transformers
4. Vector search → Qdrant
5. Filter by permissions → Access Control
6. Fetch metadata → SQLite
7. Return results → Frontend
8. Display ranked results → User
```

### RAG Flow

```
1. User asks question → Frontend
2. API Request → Backend
3. Query embedding → Sentence Transformers
4. Vector search → Qdrant (top K chunks)
5. Filter by permissions → Access Control
6. Aggregate context → Service Layer
7. Generate answer → RAG Service
8. Return answer + sources → Frontend
9. Display answer → User
```

## Technology Choices

### Why Qdrant?
- Open-source vector database
- High performance similarity search
- Easy to self-host
- Good Python SDK
- Active development

### Why FastAPI?
- Modern Python framework
- Automatic API documentation
- Type hints and validation
- Async support
- Fast performance

### Why LangChain?
- Document processing utilities
- Text splitting/chunking
- Integration with embeddings
- RAG patterns

### Why Sentence Transformers?
- No API costs
- Fast inference
- Good quality embeddings
- Self-hosted
- Multiple model options

### Why Next.js?
- React framework with SSR
- File-based routing
- TypeScript support
- Great developer experience
- Production-ready

## Security Features

### Authentication
- JWT tokens with expiration
- Password hashing (bcrypt)
- Secure token storage (localStorage)
- Protected API endpoints

### Access Control
- Document ownership
- Public/private documents
- User-based filtering
- Permission checks on all operations

### Input Validation
- File type restrictions
- File size limits
- Request validation (Pydantic)
- SQL injection prevention (ORM)

### Data Protection
- Passwords never stored in plain text
- Tokens expire automatically
- CORS configuration
- Environment-based secrets

## Scalability Considerations

### Current Architecture
- Single server deployment
- SQLite for metadata
- Local file storage
- In-process embeddings

### Scaling Options

#### Horizontal Scaling
- Add load balancer
- Multiple backend instances
- Shared database (PostgreSQL)
- Shared file storage (S3/MinIO)

#### Vertical Scaling
- Increase server resources
- GPU for embeddings
- More RAM for Qdrant
- Faster disk for database

#### Service Separation
- Separate embedding service
- Dedicated Qdrant cluster
- Separate auth service
- Message queue for async processing

### Performance Optimization

1. **Caching**
   - Cache embeddings
   - Cache search results
   - Redis for session storage

2. **Database**
   - PostgreSQL for production
   - Connection pooling
   - Indexed queries

3. **File Storage**
   - CDN for document delivery
   - S3 or similar object storage
   - Compression

4. **Search**
   - Qdrant cluster
   - Optimized vector dimensions
   - Batch processing

## Deployment Strategies

### Development
- Docker Compose
- Local development servers
- SQLite database
- Volume mounts for live reload

### Staging
- Docker Compose or Kubernetes
- PostgreSQL database
- Persistent volumes
- Backup strategy

### Production
- Kubernetes cluster
- Managed PostgreSQL (RDS/CloudSQL)
- S3 for file storage
- Managed Qdrant or self-hosted cluster
- Load balancer
- HTTPS/SSL
- Monitoring and logging
- Backup and disaster recovery

## Monitoring and Observability

### Metrics to Track
- API response times
- Search latency
- Upload success rate
- User activity
- Database performance
- Qdrant query performance

### Logging
- Application logs (FastAPI)
- Access logs (Nginx)
- Error logs
- Audit logs (user actions)

### Tools
- Prometheus for metrics
- Grafana for dashboards
- ELK stack for logs
- Sentry for error tracking

## Future Enhancements

### Short Term
- [ ] Batch document upload
- [ ] Document preview
- [ ] Advanced filtering
- [ ] Export functionality
- [ ] User preferences

### Medium Term
- [ ] OpenAI GPT integration for better RAG
- [ ] Multiple language support
- [ ] Document versioning
- [ ] Collaborative features
- [ ] Advanced analytics

### Long Term
- [ ] Multi-tenancy
- [ ] Custom embedding models
- [ ] Advanced access control (RBAC)
- [ ] Workflow automation
- [ ] Integration APIs
- [ ] Mobile applications
