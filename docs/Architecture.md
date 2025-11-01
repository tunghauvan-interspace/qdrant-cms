# Qdrant CMS/DMS - Architecture Documentation

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [System Components](#system-components)
3. [Data Flow](#data-flow)
4. [Technology Stack](#technology-stack)
5. [Database Schema](#database-schema)
6. [API Architecture](#api-architecture)
7. [Frontend Architecture](#frontend-architecture)
8. [Vector Search & Embedding Pipeline](#vector-search--embedding-pipeline)
9. [Security Architecture](#security-architecture)
10. [Deployment Architecture](#deployment-architecture)
11. [Performance Considerations](#performance-considerations)

---

## High-Level Architecture

The Qdrant CMS/DMS is a modern distributed system that combines traditional relational databases with vector databases for semantic search capabilities. The architecture follows a three-tier model:

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│                     (Next.js Frontend)                           │
│                    Port 3000 (HTTP/WebSocket)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS/REST
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
│                    (FastAPI Backend)                             │
│                     Port 8000 (REST API)                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Authentication │ Documents │ Search │ Core Services     │   │
│  └──────────────────────────────────────────────────────────┘   │
└────┬─────────────────────────────────────────────────────┬───────┘
     │                                                      │
     │ ORM/SQLAlchemy                         Vector API   │
     │                                                      │
┌────▼──────────────────────┐          ┌───────────────────▼──┐
│     DATA LAYER            │          │  VECTOR STORE LAYER  │
│                           │          │                      │
│  ┌─────────────────────┐  │          │  ┌──────────────────┐│
│  │  SQLite Database    │  │          │  │  Qdrant Vector   ││
│  │                     │  │          │  │   Database       ││
│  │  • Users            │  │          │  │                  ││
│  │  • Documents        │  │          │  │ Port 6333        ││
│  │  • Document Chunks  │  │          │  │ Port 6334 (gRPC) ││
│  │  • Tags             │  │          │  │                  ││
│  │                     │  │          │  │ Collections:     ││
│  │ documents.db        │  │          │  │ • documents      ││
│  └─────────────────────┘  │          │  │ • memory         ││
│                           │          │  │                  ││
│  ┌─────────────────────┐  │          │  └──────────────────┘│
│  │  File Storage       │  │          │                      │
│  │  (/uploads)         │  │          │  Persistent Storage: │
│  │                     │  │          │  (/qdrant/storage)   │
│  └─────────────────────┘  │          │                      │
└───────────────────────────┘          └──────────────────────┘
```

---

## System Components

### 1. **Frontend Component** (Next.js 14)

**Location**: `frontend/`

**Responsibilities**:
- User interface for authentication (login, register)
- Document upload interface
- Search interface (semantic + RAG)
- Document management and preview
- User dashboard

**Key Features**:
- Server-side rendering (SSR) with Next.js App Router
- TypeScript for type safety
- Tailwind CSS for styling
- Playwright for E2E testing
- Axios for API communication
- React Query for state management

**Pages**:
- `/` - Home page
- `/login` - User login
- `/register` - User registration
- `/dashboard` - Main application dashboard
- `/dashboard/documents` - Document management
- `/dashboard/search` - Search interface

---

### 2. **Backend Component** (FastAPI)

**Location**: `backend/`

**Responsibilities**:
- REST API server
- User authentication and authorization
- Document processing pipeline
- Vector embedding generation
- Search coordination between SQLite and Qdrant
- File upload handling

**Core Modules**:

#### a. **Authentication Module** (`app/api/auth.py`)
- User registration
- User login with JWT tokens
- Current user retrieval
- Password hashing with bcrypt

#### b. **Document Module** (`app/api/documents.py`)
- Upload documents (PDF, DOCX)
- List user documents
- Get specific document details
- Preview document content
- Delete documents
- Manage document tags

#### c. **Search Module** (`app/api/search.py`)
- Semantic search across documents
- RAG (Retrieval-Augmented Generation) queries
- Query embedding generation
- Result filtering and ranking

#### d. **Services Layer** (`app/services/`)

**Auth Service** (`auth_service.py`):
- JWT token creation and validation
- Password verification and hashing
- User extraction from tokens

**Document Processor** (`document_processor.py`):
- PDF text extraction using PyPDF
- DOCX text extraction using python-docx
- Text chunking using LangChain's RecursiveCharacterTextSplitter
- Default chunk size: 1000 characters
- Default overlap: 200 characters

**Qdrant Service** (`qdrant_service.py`):
- Connection management to Qdrant
- Embedding generation (local or OpenAI)
- Collection management
- Vector upsertion and search
- Document chunk deletion

#### e. **Models & Schemas** (`app/models/`, `app/schemas/`)

**Data Models**:
- `User` - User accounts with admin privileges
- `Document` - Document metadata
- `DocumentChunk` - Text chunks with Qdrant references
- `Tag` - Tags for document categorization

**Request/Response Schemas**:
- `UserCreate`, `UserResponse`
- `DocumentUpload`, `DocumentResponse`
- `SearchQuery`, `SearchResult`
- `RagQuery`, `RagResult`

#### f. **Utils** (`app/utils/`)
- Text splitting utilities
- Custom tokenizers for chunk size calculation

---

### 3. **Qdrant Vector Database**

**Location**: Docker service on port 6333 (REST) / 6334 (gRPC)

**Responsibilities**:
- Store document chunk embeddings
- Perform semantic similarity search
- Maintain vector indices for fast retrieval

**Collections**:
1. **documents** - Stores embeddings for all document chunks
   - Vector name: `fast-all-minilm-l6-v2` (configurable)
   - Vector size: 384 (for default embedding model)
   - Distance metric: COSINE similarity

2. **memory** - Optional collection for memory/conversation history

**Data Persistence**:
- Volume: `qdrant_storage:/qdrant/storage`
- Survives container restarts

---

### 4. **SQLite Database**

**Location**: `documents.db` (generated at runtime)

**Responsibilities**:
- Store user information
- Store document metadata
- Store document chunk references
- Manage document tags
- Maintain relationships and constraints

**Tables**:

```
users
├─ id (PK)
├─ username (UNIQUE)
├─ email (UNIQUE)
├─ hashed_password
├─ is_admin
└─ created_at

documents
├─ id (PK)
├─ filename
├─ original_filename
├─ file_type
├─ file_path
├─ file_size
├─ upload_date
├─ owner_id (FK → users.id)
├─ description
└─ is_public (public/private/restricted)

document_chunks
├─ id (PK)
├─ document_id (FK → documents.id)
├─ chunk_index
├─ content
└─ qdrant_point_id (link to Qdrant)

tags
├─ id (PK)
├─ name (UNIQUE)
└─ (many-to-many with documents)

document_tags (junction table)
├─ document_id (FK)
└─ tag_id (FK)
```

---

## Data Flow

### 1. **Document Upload Flow**

```
User Browser (Frontend)
    │
    ├─ Select PDF/DOCX file
    │
    ▼
[POST /api/documents/upload]
    │
    ├─ Authenticate user (JWT)
    │
    ├─ Validate file (type, size)
    │
    ▼
Backend (FastAPI)
    │
    ├─ Save file to disk (/uploads)
    │
    ├─ Extract text (PDF/DOCX parser)
    │
    ├─ Split text into chunks (overlap=200)
    │
    ├─ Store document metadata in SQLite:
    │   • filename, file_type, owner_id
    │   • Store DocumentChunk records
    │
    ▼
Generate Embeddings
    │
    ├─ For each chunk:
    │   • Send to Sentence Transformers
    │   • Generate 384-dimensional vector
    │
    ▼
Store in Qdrant
    │
    ├─ Create PointStruct with:
    │   • Embedding vector
    │   • Chunk content
    │   • Document ID
    │   • Metadata
    │
    ├─ Upsert to 'documents' collection
    │
    ▼
Return Response
    │
    └─ Document ID + chunk count
```

**Performance**: Typically 1-5 seconds depending on document size

---

### 2. **Semantic Search Flow**

```
User Query (Frontend)
    │
    ├─ Type search query
    │
    ▼
[POST /api/search/semantic]
    │
    ├─ Authenticate user (JWT)
    │
    ├─ Validate query
    │
    ▼
Backend (FastAPI)
    │
    ├─ Generate embedding for query
    │   • Same model as document chunks
    │   • Output: 384-dimensional vector
    │
    ▼
Search Qdrant
    │
    ├─ Execute similarity search:
    │   • Query vector vs stored vectors
    │   • Cosine distance metric
    │   • Top-K results (default: 5)
    │
    ├─ Get hit.score (0-2 range)
    │
    ▼
Post-Process Results
    │
    ├─ Filter by access control:
    │   • Owner documents (always)
    │   • Public documents
    │
    ├─ Deduplicate by document
    │
    ├─ Sort by relevance score
    │
    ▼
Return Results
    │
    └─ [{"id": ..., "score": ..., "content": ...}, ...]
```

**Latency**: ~200-500ms per query

---

### 3. **RAG (Retrieval-Augmented Generation) Flow**

```
User Question (Frontend)
    │
    ├─ "What are the main topics in my documents?"
    │
    ▼
[POST /api/search/rag]
    │
    ├─ Query + top_k parameter
    │
    ▼
Backend (FastAPI)
    │
    ├─ Step 1: Retrieve relevant chunks (same as semantic search)
    │
    ├─ Step 2: Context construction
    │   • Combine top-K chunks
    │   • Create context string
    │
    ├─ Step 3: Prompt assembly
    │   • System prompt
    │   • Context
    │   • User question
    │
    ├─ Step 4: LLM call
    │   • Send to GPT (OpenAI) or local model
    │   • Get generated answer
    │
    ▼
Return Response
    │
    └─ {"answer": "...", "sources": [...]}
```

**Note**: RAG implementation can use local LLMs or OpenAI API (configurable)

---

### 4. **User Authentication Flow**

```
Registration:
┌────────────────────┐
│ User Form          │
│ (username, email,  │
│  password)         │
└─────────┬──────────┘
          │
          ▼
   Check duplicates
          │
          ▼
   Hash password
   (bcrypt)
          │
          ▼
   Save to SQLite
          │
          ▼
   Return user info

Login:
┌────────────────────┐
│ User credentials   │
│ (username,         │
│  password)         │
└─────────┬──────────┘
          │
          ▼
   Find user in DB
          │
          ▼
   Verify password
          │
          ▼
   Create JWT token
   (HS256, 30min exp)
          │
          ▼
   Return token
          │
          ▼
   Frontend stores
   in localStorage
```

---

## Technology Stack

### Backend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | FastAPI | 0.104.1 | REST API server |
| Server | Uvicorn | 0.24.0 | ASGI server |
| Vector DB | Qdrant | latest | Vector search |
| Client SDK | qdrant-client | 1.7.0 | Qdrant communication |
| ORM | SQLAlchemy | 2.0.23 | Database abstraction |
| Async DB | aiosqlite | 0.19.0 | Async SQLite driver |
| Embeddings | sentence-transformers | 2.7.0 | Local embeddings |
| LLM | OpenAI | 1.3.0 | GPT integration (optional) |
| PDF Parsing | PyPDF | 3.17.1 | PDF extraction |
| DOCX Parsing | python-docx | 1.1.0 | DOCX extraction |
| Text Processing | LangChain | (implicit) | Chunking strategies |
| Deep Learning | PyTorch | 2.3.0+cpu | Embeddings backend |
| Auth | python-jose | 3.3.0 | JWT tokens |
| Hashing | bcrypt | 4.1.2 | Password hashing |
| Config | python-dotenv | 1.0.0 | Environment management |
| Validation | pydantic | 2.5.0 | Data validation |

### Frontend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | Next.js | 14.0.3 | React meta-framework |
| Language | TypeScript | 5.3.2 | Type safety |
| Runtime | Node.js | 18+ | JavaScript runtime |
| Styling | Tailwind CSS | 3.3.5 | Utility CSS |
| HTTP Client | Axios | 1.6.2 | API requests |
| State Mgmt | React Query | 3.39.3 | Server state |
| Testing | Playwright | 1.56.1 | E2E testing |
| Linting | ESLint | 8.54.0 | Code quality |

### Infrastructure

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Container | Docker | latest | Application containerization |
| Orchestration | Docker Compose | latest | Multi-container management |
| Database | SQLite | - | Metadata storage |
| Vector DB | Qdrant | latest | Vector search |
| OS | Linux | - | Container base |

---

## Database Schema

### Detailed Schema Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USERS TABLE                               │
├──────────┬──────────┬──────────┬──────────┬────────┬─────────┤
│ id (PK)  │ username │ email    │ hashed_  │is_admin│created_ │
│ INTEGER  │ STRING   │ STRING   │password  │STRING  │at       │
│          │UNIQUE    │UNIQUE    │ STRING   │        │DATETIME │
│          │INDEXED   │INDEXED   │          │        │         │
└──────────┴──────────┴──────────┴──────────┴────────┴─────────┘
           │
           │ 1:N relationship
           │ (owner_id)
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                  DOCUMENTS TABLE                             │
├──────────┬──────────┬─────────┬──────────┬───────────┬───────┤
│ id (PK)  │ filename │file_type│ file_    │owner_id   │is_    │
│ INTEGER  │ STRING   │ STRING  │path      │(FK)       │public │
│ INDEXED  │          │         │ STRING   │           │STRING │
│          │          │         │          │           │       │
├──────────┼──────────┼─────────┼──────────┼───────────┼───────┤
│original_ │file_size │upload_  │description│           │
│filename  │ INTEGER  │date     │ TEXT      │           │
│ STRING   │          │DATETIME │           │           │
└──────────┴──────────┴─────────┴──────────┴───────────┴───────┘
           │
           │ 1:N relationship
           │ (document_id)
           │
           ▼
┌────────────────────────────────────────────────────────────┐
│              DOCUMENT_CHUNKS TABLE                         │
├──────────┬─────────┬──────────┬────────┬─────────────────┤
│ id (PK)  │document_│chunk_    │content │qdrant_point_id  │
│ INTEGER  │id (FK)  │index     │ TEXT   │ STRING (UNIQUE) │
│ INDEXED  │ INTEGER │ INTEGER  │        │ INDEXED         │
│          │         │          │        │ (external ref)  │
└──────────┴─────────┴──────────┴────────┴─────────────────┘
           │
           │ N:M relationship
           │ (via document_tags)
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                    TAGS TABLE                                │
├──────────┬──────────────────────────────────────────────────┤
│ id (PK)  │ name (UNIQUE, INDEXED)                           │
│ INTEGER  │ STRING                                           │
└──────────┴──────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│            DOCUMENT_TAGS (JUNCTION TABLE)                  │
├──────────────────────┬──────────────────────────────────────┤
│ document_id (FK)     │ tag_id (FK)                          │
│ INTEGER              │ INTEGER                              │
└──────────────────────┴──────────────────────────────────────┘
```

### Key Design Decisions

1. **Separate Chunk Storage**: Document chunks are stored in SQLite for relationship tracking and text retrieval, while embeddings are in Qdrant for efficient similarity search.

2. **Qdrant Point ID Reference**: Each chunk maintains a reference (`qdrant_point_id`) to its vector in Qdrant, enabling deletion synchronization.

3. **User-Document Ownership**: Foreign key from documents to users enables access control and filtering.

4. **Many-to-Many Tags**: Junction table supports flexible tagging without content duplication.

5. **Async-Ready**: All tables designed for async ORM operations with SQLAlchemy.

---

## API Architecture

### RESTful Endpoints Structure

```
/api/
├── /auth
│   ├── POST /register          - Register new user
│   ├── POST /login             - Login and get JWT
│   └── GET /me                 - Get current user info
│
├── /documents
│   ├── POST /upload            - Upload document
│   ├── GET /                   - List user's documents
│   ├── GET /{id}               - Get document details
│   ├── GET /{id}/preview       - Get document content
│   └── DELETE /{id}            - Delete document
│
└── /search
    ├── POST /semantic          - Semantic search
    └── POST /rag               - RAG query
```

### Request/Response Examples

#### Upload Document

**Request**:
```http
POST /api/documents/upload HTTP/1.1
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: <binary PDF/DOCX>
description: "Optional description"
tags: ["tag1", "tag2"]
is_public: "private"
```

**Response**:
```json
{
  "id": 1,
  "filename": "doc_abc123.pdf",
  "chunks_count": 45,
  "upload_date": "2024-11-01T10:30:00",
  "status": "success"
}
```

#### Semantic Search

**Request**:
```json
POST /api/search/semantic
{
  "query": "machine learning algorithms",
  "top_k": 5,
  "min_score": 0.5
}
```

**Response**:
```json
{
  "results": [
    {
      "id": "chunk_uuid_1",
      "score": 0.876,
      "document_id": 1,
      "content": "Machine learning is...",
      "source": "document_name.pdf"
    }
  ],
  "query_time_ms": 245
}
```

### Authentication Mechanism

**JWT Token Structure**:
```
Header: {
  "alg": "HS256",
  "typ": "JWT"
}

Payload: {
  "sub": "username",
  "exp": 1699000000,
  "iat": 1698996400
}

Signature: HMAC-SHA256(header.payload, SECRET_KEY)
```

**Token Validation**:
1. Token extracted from Authorization header
2. Signature verified using SECRET_KEY
3. Expiration checked
4. User retrieved from database
5. User object injected into request context

---

## Frontend Architecture

### Component Structure

```
frontend/
├── app/
│   ├── layout.tsx              - Root layout with providers
│   ├── page.tsx                - Home page
│   ├── globals.css             - Global styles
│   │
│   ├── login/
│   │   └── page.tsx            - Login page
│   │
│   ├── register/
│   │   └── page.tsx            - Registration page
│   │
│   └── dashboard/
│       └── page.tsx            - Dashboard (protected)
│
├── lib/
│   └── api.ts                  - Axios instance + API calls
│
└── tests/
    ├── home.spec.ts            - Home page tests
    ├── login.spec.ts           - Login tests
    ├── register.spec.ts        - Registration tests
    └── preview.spec.ts         - Preview tests
```

### Page Navigation Flow

```
                    ┌──────────────┐
                    │  /           │
                    │  Home Page   │
                    └──────┬───────┘
                           │
                ┌──────────┴──────────┐
                │                     │
                ▼                     ▼
         ┌────────────┐        ┌────────────┐
         │  /login    │        │ /register  │
         └─────┬──────┘        └─────┬──────┘
               │                     │
               └──────────┬──────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │   /dashboard           │
              │   Protected Route      │
              │   (JWT Required)       │
              └────────────────────────┘
```

### State Management Pattern

```
API Request Flow:
┌─────────────┐
│ Component   │
│ (use state) │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│ lib/api.ts                          │
│ • Axios instance                    │
│ • API endpoints                     │
│ • Request/response interceptors     │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Backend API (/api/*)                │
│ • Request validation                │
│ • Database operations               │
│ • Vector search                     │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Response Handling                   │
│ • Error handling                    │
│ • State update                      │
│ • UI re-render                      │
└─────────────────────────────────────┘
```

### Authentication State Management

```
LocalStorage (Frontend):
├─ access_token: "jwt_token_here"
└─ (optional) user_info: JSON

API Requests:
├─ Include Authorization header
└─ Bearer {token}

Token Validation:
├─ On page load, verify token
├─ Check expiration
└─ Redirect to login if invalid
```

---

## Vector Search & Embedding Pipeline

### Embedding Generation Process

**Model Used**: `sentence-transformers/all-MiniLM-L6-v2`

**Characteristics**:
- Input: Any text string
- Output: 384-dimensional dense vector
- Parameters: ~22M
- Processing: CPU-optimized (can run on CPU)
- Speed: ~1000 documents/second

**Embedding Process**:

```
Text Input
    │
    ▼
┌─────────────────────────────┐
│ Tokenization                │
│ • Split into subwords       │
│ • Convert to token IDs      │
│ • Add special tokens        │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Transformer Layers          │
│ • Sentence Transformers     │
│ • 6 attention layers        │
│ • Contextual understanding  │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Mean Pooling                │
│ • Average all token vectors │
│ • Normalize to unit length  │
└──────────┬──────────────────┘
           │
           ▼
384-D Vector Output
```

### Similarity Search Algorithm

**Distance Metric**: Cosine Similarity

```
Query Vector: [q1, q2, q3, ..., q384]
Document Vector: [d1, d2, d3, ..., d384]

Cosine Similarity = (Q · D) / (|Q| × |D|)

Output Range: [-1, 1]
Interpretation:
  • 1.0 = identical
  • 0.0 = orthogonal
  • -1.0 = opposite
```

### Qdrant Vector Storage

**Collection Configuration**:
```python
{
  "name": "documents",
  "vectors": {
    "fast-all-minilm-l6-v2": {
      "size": 384,
      "distance": "Cosine"
    }
  },
  "payload_schema": {
    "document": {"type": "text"},
    "document_id": {"type": "integer"},
    "metadata": {"type": "object"}
  }
}
```

**Indexing Strategy**:
- HNSW (Hierarchical Navigable Small World)
- Enables O(log n) search complexity
- Built automatically by Qdrant
- No manual index management needed

### Chunking Strategy

**Algorithm**: RecursiveCharacterTextSplitter

**Parameters**:
- Chunk size: 1000 characters
- Overlap: 200 characters
- Separators: `["\n\n", "\n", " ", ""]`

**Example**:
```
Original Text (3000 chars):
"Chapter 1. Introduction...[long text]...End of chapter 1."

After Chunking (overlap=200):

Chunk 1 (0-1000):   "Chapter 1. Introduction...[text]..."
Chunk 2 (800-1800): "[overlap text]...[new text]..."
Chunk 3 (1600-2600):"[overlap text]...[new text]..."
Chunk 4 (2400-3000):"[overlap text]...End of chapter 1."

Result: 4 chunks with context overlap for semantic coherence
```

---

## Security Architecture

### Authentication & Authorization

**Multi-Layer Security**:

```
┌──────────────────────────────────────────┐
│ 1. Transport Security (HTTPS)            │
│    (In production, enforce TLS 1.3)      │
└──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│ 2. Credential Validation                 │
│    • Username/password verification      │
│    • Bcrypt password hashing             │
│    • Rate limiting (recommended)         │
└──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│ 3. JWT Token Generation                  │
│    • HS256 signature algorithm           │
│    • 30-minute expiration                │
│    • User ID in payload                  │
└──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│ 4. Request Authorization                 │
│    • Token extraction from headers       │
│    • Signature verification              │
│    • Expiration check                    │
│    • User retrieval from database        │
└──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│ 5. Resource-Level Authorization          │
│    • Owner verification                  │
│    • Access control (public/private)     │
│    • Admin privilege checks              │
└──────────────────────────────────────────┘
```

### Password Security

**Hashing Algorithm**: bcrypt with salt

```
User Password: "MySecurePassword123"
    │
    ▼
Bcrypt Hash:
$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUe

Components:
$2b$ → Algorithm version
12 → Cost factor (rounds = 2^12)
R9h/cIPz0gi... → Salt + Hash
```

### File Security

**Upload Validation**:
1. File type validation (PDF, DOCX only)
2. File size limits (configurable max)
3. Filename sanitization
4. Virus scanning (optional)

**Storage Security**:
- Files stored in isolated `/uploads` directory
- Access controlled through database records
- Private files not directly web-accessible
- Deletion cascades to both storage and database

### Access Control Model

```
Document Access Rules:

Owner (User A):
└─ Full access (read, delete, modify metadata)

is_public = "private":
└─ Only owner + admin can read

is_public = "public":
├─ Any authenticated user can read
└─ Only owner + admin can delete

Admin User:
└─ Can access all documents regardless of visibility
```

---

## Deployment Architecture

### Docker Compose Services

```yaml
qdrant:
  • Image: qdrant/qdrant:latest
  • Ports: 6333 (REST), 6334 (gRPC)
  • Volume: qdrant_storage (persistent)
  • Environment: QDRANT__SERVICE__GRPC_PORT=6334

backend:
  • Build: ./backend/Dockerfile
  • Ports: 8000 (HTTP)
  • Volumes: ./backend:/app, ./uploads:/app/uploads
  • Environment: QDRANT_HOST=qdrant, QDRANT_PORT=6333
  • Depends on: qdrant
  • Command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

frontend:
  • Build: ./frontend/Dockerfile
  • Ports: 3000 (HTTP)
  • Volumes: ./frontend:/app, /app/node_modules, /app/.next
  • Environment: NEXT_PUBLIC_API_URL=http://localhost:8000
  • Depends on: backend

mcp-server (optional):
  • Image: python:3.11-slim
  • Ports: 8001
  • Environment: QDRANT_URL=http://qdrant:6333
  • Optional MCP server integration
```

### Production Deployment Considerations

**Database**:
- Current: SQLite (suitable for development/small deployments)
- Recommended: PostgreSQL for production
- Enable connection pooling

**Vector Database**:
- Current: Single Qdrant instance
- Recommended: Qdrant cluster for high availability
- Enable replication

**Storage**:
- Current: Local filesystem
- Recommended: Cloud storage (S3, Azure Blob, etc.)
- Benefits: Scalability, backup, CDN integration

**Load Balancing**:
- Reverse proxy (Nginx/HAProxy)
- Multiple backend instances behind load balancer
- Session affinity for WebSocket support

**Monitoring & Logging**:
- Application metrics (Prometheus)
- Log aggregation (ELK stack, Loki)
- Health checks on all services
- Database performance monitoring

---

## Performance Considerations

### Optimization Strategies

#### 1. **Embedding Caching**
- Cache document embeddings in Qdrant
- Skip re-embedding unchanged documents
- Reduces computational overhead

#### 2. **Vector Search Optimization**
```
Search Performance Factors:
├─ Collection size (documents)
├─ Vector dimension (384)
├─ Top-K parameter (default: 5)
└─ Qdrant index type (HNSW)

Typical Latencies:
├─ 10K documents: ~50-100ms
├─ 100K documents: ~100-300ms
├─ 1M documents: ~200-500ms
└─ 10M documents: ~500ms-1s
```

#### 3. **Database Query Optimization**
```sql
-- Indexed columns for fast retrieval:
• users.username (UNIQUE)
• users.email (UNIQUE)
• documents.owner_id (FK)
• document_chunks.qdrant_point_id (UNIQUE)
• tags.name (UNIQUE)
```

#### 4. **Text Chunking Efficiency**
- Chunk size: 1000 characters (balance between context and speed)
- Overlap: 200 characters (maintain semantic continuity)
- Typical document: 100-200 chunks

#### 5. **API Response Caching**
- Cache search results for popular queries
- Redis for distributed caching (optional)
- TTL: 1 hour

### Scalability Considerations

#### Horizontal Scaling

```
Load Balancer
    │
    ├─ Backend Instance 1
    ├─ Backend Instance 2
    ├─ Backend Instance 3
    └─ Backend Instance N
    
All connect to:
├─ Shared PostgreSQL
├─ Shared Qdrant Cluster
└─ Shared S3 Storage
```

#### Vertical Scaling

```
Current (Single Server):
├─ CPU: 2+ cores
├─ RAM: 4GB (minimum), 8GB+ (recommended)
├─ Storage: Variable (depends on documents)
└─ Network: 1Gbps

High-Volume:
├─ CPU: 8+ cores (Qdrant: 4 cores, Backend: 4 cores)
├─ RAM: 32GB+ (Qdrant: 16GB, Backend: 8GB, System: 8GB)
├─ Storage: Fast SSD (NVMe) with RAID
└─ Network: 10Gbps
```

### Monitoring Metrics

**Backend Metrics**:
- Request latency (p50, p95, p99)
- Error rate (5xx, validation errors)
- Database query time
- Vector search time

**Infrastructure Metrics**:
- CPU usage per service
- Memory usage
- Disk I/O
- Network throughput

**Application Metrics**:
- Documents uploaded (cumulative)
- Search queries (per minute)
- Active users
- Average response times

---

## Summary

The Qdrant CMS/DMS architecture combines:

1. **Modern Frontend** - Next.js with TypeScript for type-safe UI
2. **Robust Backend** - FastAPI with async/await for high concurrency
3. **Dual Database Strategy** - SQLite for metadata, Qdrant for vectors
4. **Semantic Search** - Local embeddings with efficient similarity search
5. **Security First** - JWT authentication, password hashing, access control
6. **Scalable Design** - Docker-based deployment, horizontal scaling ready
7. **Production Ready** - Configuration management, error handling, logging

This architecture supports document management, semantic search, and RAG capabilities while maintaining code clarity and deployment simplicity.
