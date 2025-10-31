# Qdrant CMS/DMS

A comprehensive Document Management System (CMS/DMS) using Qdrant as a vector database backend for semantic search and document management.

## Features

- **Document Upload**: Upload PDF and DOCX files
- **Automatic Processing**: Documents are automatically chunked and embedded
- **Vector Search**: Semantic search powered by Qdrant
- **RAG Support**: Retrieval-Augmented Generation for intelligent document queries
- **Document Management**: 
  - Tagging system
  - Access control (public/private)
  - Full CRUD operations
- **User Authentication**: Secure JWT-based authentication
- **Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Qdrant**: Vector database for similarity search
- **LangChain**: Document processing and chunking
- **Sentence Transformers**: Local embedding generation
- **SQLAlchemy**: Database ORM
- **SQLite**: Metadata storage

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Axios**: HTTP client

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/tunghauvan-interspace/qdrant-cms.git
cd qdrant-cms
```

2. Start all services:
```bash
docker compose up -d --build
```

3. Create the admin account:
```bash
docker compose exec backend python create_admin.py
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Qdrant Dashboard: http://localhost:6333/dashboard

**Default Admin Credentials:**
- Username: `admin`
- Email: `admin@example.com`
- Password: `admin123`

⚠️ **Important:** Change the default admin password after first login!

### Manual Setup

#### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start Qdrant (using Docker):
```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

On Windows/PowerShell:
```powershell
docker run -p 6333:6333 -p 6334:6334 -v ${PWD}/qdrant_storage:/qdrant/storage qdrant/qdrant
```

6. Run the backend:
```bash
uvicorn main:app --reload
```

#### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

4. Run the development server:
```bash
npm run dev
```

## Usage

### Getting Started

1. **Admin Account Setup**:
   - After starting the services, run the admin creation script
   - Default admin credentials are provided above
   - Change the default password immediately after login

2. **Register Additional Accounts**:
   - Navigate to http://localhost:3000
   - Click "Register" and create a new account

3. **Upload Documents**:
   - Log in to your account
   - Go to the "Upload" tab
   - Select a PDF or DOCX file
   - Add optional description and tags
   - Choose access level (private/public)
   - Click "Upload Document"

4. **Search Documents**:
   - **Semantic Search**: Use natural language queries to find relevant documents
   - **RAG Query**: Ask questions about your documents and get AI-generated answers

5. **Manage Documents**:
   - View all your documents in the "My Documents" tab
   - Delete documents as needed
   - Filter and browse by tags

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

### Key Endpoints

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get access token
- `POST /api/documents/upload` - Upload a document
- `GET /api/documents/` - List documents
- `DELETE /api/documents/{id}` - Delete a document
- `POST /api/search/semantic` - Perform semantic search
- `POST /api/search/rag` - Perform RAG query

## Configuration

### Backend Configuration (.env)

```env
# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=documents

# Embedding Model
EMBEDDING_MODEL=sentence-transformers
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

# Database
DATABASE_URL=sqlite+aiosqlite:///./documents.db

# Security
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=50000000
```

### Frontend Configuration (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Admin Account Management

The application includes a script to create an admin user account. This is essential for initial setup and administrative access.

### Creating Admin Account

After starting the services with Docker:

```bash
docker compose exec backend python create_admin.py
```

### Custom Admin Credentials

You can customize the admin account by setting environment variables before running the script:

```bash
export ADMIN_USERNAME=myadmin
export ADMIN_EMAIL=admin@mydomain.com
export ADMIN_PASSWORD=securepassword123
docker compose exec backend python create_admin.py
```

Or create a `.env` file in the backend directory with these variables.

### Admin Features

The admin account has full access to:
- All documents (including private ones from other users)
- User management capabilities
- System configuration
- All CRUD operations on documents and users

⚠️ **Security Note:** Always change the default admin password after first login and use strong, unique passwords for admin accounts.

### Document Processing Pipeline

1. **Upload**: User uploads PDF/DOCX file
2. **Text Extraction**: Extract text from document
3. **Chunking**: Split text into meaningful chunks using LangChain
4. **Embedding**: Generate embeddings for each chunk using Sentence Transformers
5. **Storage**: Store embeddings in Qdrant and metadata in SQLite
6. **Indexing**: Enable fast semantic search

### Search Flow

1. **Query**: User submits search query
2. **Embedding**: Convert query to embedding vector
3. **Search**: Find similar vectors in Qdrant
4. **Filtering**: Apply access control filters
5. **Results**: Return ranked results with context

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Running Tests

Backend tests (when implemented):
```bash
cd backend
pytest
```

Frontend tests (Playwright E2E tests):
```bash
cd frontend
npm install
npx playwright install chromium
npm test
```

For more details on frontend testing, see:
- [Frontend Tests README](frontend/tests/README.md)

## Production Deployment

### Environment Variables

For production deployment, ensure you:
1. Change the `SECRET_KEY` to a secure random value
2. Use a production-grade database (PostgreSQL recommended)
3. Configure proper CORS settings
4. Enable HTTPS
5. Set up proper logging and monitoring

### Docker Production Build

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Docker Build Optimization

The backend Docker image is optimized for fast builds and reduced bandwidth usage:
- Pip caching enabled for faster dependency installation
- Sentence-transformers models pre-downloaded during build
- No runtime model downloads needed

See [DOCKER_OPTIMIZATION.md](DOCKER_OPTIMIZATION.md) for details on the optimizations and best practices.

## Security Considerations

- JWT-based authentication with expiring tokens
- Password hashing using bcrypt
- Access control for documents (public/private)
- Input validation and sanitization
- File type restrictions (PDF and DOCX only)
- File size limits

## Limitations and Future Enhancements

### Current Limitations
- Basic RAG implementation (can be enhanced with LLM integration)
- SQLite database (suitable for development, consider PostgreSQL for production)
- Local file storage (consider cloud storage for production)

### Planned Enhancements
- [ ] Integration with OpenAI GPT for advanced RAG
- [ ] More document formats (TXT, MD, etc.)
- [ ] Advanced access control (user groups, permissions)
- [ ] Document versioning
- [ ] Collaborative features
- [ ] Full-text search alongside vector search
- [ ] Document preview
- [ ] Batch upload
- [ ] Export functionality
- [ ] Analytics and usage statistics

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open-source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Acknowledgments

- [Qdrant](https://qdrant.tech/) - Vector database
- [LangChain](https://www.langchain.com/) - Document processing
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [Next.js](https://nextjs.org/) - Frontend framework
- [Sentence Transformers](https://www.sbert.net/) - Embeddings