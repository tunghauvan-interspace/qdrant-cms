# Qdrant CMS/DMS

A comprehensive Document Management System (CMS/DMS) using Qdrant as a vector database backend for semantic search and document management.

## Features

### Core Features
- **Document Upload**: Upload PDF and DOCX files
- **Automatic Processing**: Documents are automatically chunked and embedded
- **Vector Search**: Semantic search powered by Qdrant
- **RAG Support**: Retrieval-Augmented Generation for intelligent document queries
- **User Authentication**: Secure JWT-based authentication
- **Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS

### Document Management
- **Tagging System**: Organize documents with custom tags
- **Access Control**: Public/private/restricted document visibility
- **Full CRUD Operations**: Create, read, update, and delete documents
- **Document Preview**: View formatted content display for PDF and DOCX files
- **Metadata Editing**: Update document descriptions, tags, and visibility settings

### Advanced Features ✨ NEW
- **📝 Document Versioning**: 
  - Automatic version tracking for all document changes
  - View complete version history with timestamps
  - Rollback to any previous version
  - Track who made changes and when
  
- **🤝 Advanced Sharing System**:
  - Share documents with specific users
  - Granular permissions: View, Edit, or Admin access
  - Manage sharing permissions and revoke access
  - View all documents shared with you
  
- **📊 Comprehensive Analytics**:
  - Track document views, downloads, and search hits
  - View usage statistics and engagement metrics
  - Identify popular documents and trending content
  - User activity tracking and reporting
  
- **⭐ Favorites/Bookmarking**:
  - Bookmark important documents for quick access
  - Personal favorites list
  - Easy add/remove from any document
  
- **⚡ Bulk Operations**:
  - Update metadata for multiple documents at once
  - Share multiple documents with users simultaneously
  - Efficient batch processing for large document sets
  
- **📤 Export Capabilities**:
  - Export document metadata as JSON
  - Download documents as ZIP archives
  - Export metadata to CSV for analysis
  - Bulk export functionality

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Qdrant**: Vector database for similarity search
- **LangChain**: Document processing and chunking
- **Sentence Transformers**: Local embedding generation
- **SQLAlchemy**: Database ORM
- **SQLite**: Metadata storage (upgradable to PostgreSQL)

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

4. **Upgrade Database** (if upgrading from previous version):
```bash
docker compose exec backend python migrate_database.py
```

5. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Qdrant Dashboard: http://localhost:6333/dashboard

**Default Admin Credentials:**
- Username: `admin`
- Email: `admin@example.com`
- Password: `admin123`

⚠️ **Important:** Change the default admin password after first login!

### Upgrading from Previous Version

If you're upgrading from a previous version of Qdrant CMS, you need to run the database migration:

```bash
# Using Docker
docker compose exec backend python migrate_database.py

# Or locally
cd backend
python migrate_database.py
```

This will:
- Add new columns to the documents table (last_modified, version)
- Create new tables for versions, shares, analytics, and favorites
- Preserve all existing data

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

5. **Preview Documents**:
   - Click the "Preview" button next to any document in your list
   - View the full text content of PDF and DOCX files
   - Preview is only available for documents you own or public documents

6. **Manage Documents**:
   - View all your documents in the "My Documents" tab
   - Delete documents as needed
   - Filter and browse by tags

### Advanced Features Usage

#### Document Editing & Versioning
- **Edit Document Metadata**: Update description, tags, and visibility settings
- **Version History**: View all changes made to a document over time
- **Rollback**: Restore a document to any previous version
- All changes are automatically tracked with timestamps and user information

#### Sharing Documents
- **Share with Users**: Grant specific users access to your documents
- **Set Permissions**:
  - **View**: Can only view and download the document
  - **Edit**: Can modify metadata and content
  - **Admin**: Full control including sharing with others
- **Manage Shares**: View and revoke access for shared documents
- **Shared with Me**: Access documents others have shared with you

#### Analytics & Insights
- **Track Engagement**: Monitor views, downloads, and search hits
- **Usage Statistics**: View comprehensive analytics for your documents
- **Popular Documents**: Discover trending and most-viewed content
- **Activity Reports**: Track user engagement over time periods (7, 30, 90 days)

#### Favorites & Quick Access
- **Bookmark Documents**: Mark important documents as favorites
- **Quick Access**: View all your favorite documents in one place
- **Easy Management**: Add or remove favorites with one click

#### Bulk Operations
- **Mass Updates**: Update metadata for multiple documents simultaneously
- **Bulk Sharing**: Share multiple documents with a user at once
- **Time Savings**: Efficient operations for managing large document collections

#### Export & Backup
- **JSON Export**: Export document metadata in JSON format
- **ZIP Archive**: Download selected documents in a compressed archive
- **CSV Export**: Export metadata to spreadsheet format for analysis
- **Backup**: Create backups of important documents and their metadata

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

### Core Endpoints

#### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get access token
- `GET /api/auth/me` - Get current user information

#### Document Management
- `POST /api/documents/upload` - Upload a document
- `GET /api/documents/` - List documents (with pagination)
- `GET /api/documents/{id}` - Get a specific document
- `PUT /api/documents/{id}` - Update document metadata
- `DELETE /api/documents/{id}` - Delete a document
- `GET /api/documents/{id}/preview` - Preview document content
- `GET /api/documents/tags/all` - List all available tags

#### Search
- `POST /api/search/semantic` - Perform semantic search
- `POST /api/search/rag` - Perform RAG query

### Advanced Feature Endpoints ✨

#### Version Management
- `GET /api/documents/{id}/versions` - Get version history for a document
- `POST /api/documents/{id}/versions/{version_id}/rollback` - Rollback to specific version

#### Sharing & Permissions
- `POST /api/documents/{id}/share` - Share document with a user
- `GET /api/documents/{id}/shares` - List all shares for a document
- `DELETE /api/documents/shares/{share_id}` - Remove a document share
- `GET /api/documents/shared-with-me` - Get documents shared with current user

#### Analytics
- `POST /api/documents/{id}/analytics/view` - Track a document view
- `POST /api/documents/{id}/analytics/download` - Track a document download
- `GET /api/documents/{id}/analytics` - Get analytics for a document
- `GET /api/documents/analytics/popular` - Get most popular documents

#### Favorites
- `POST /api/documents/{id}/favorite` - Add document to favorites
- `DELETE /api/documents/{id}/favorite` - Remove document from favorites
- `GET /api/documents/favorites` - Get user's favorite documents

#### Bulk Operations
- `POST /api/documents/bulk/update` - Bulk update document metadata
- `POST /api/documents/bulk/share` - Bulk share documents with a user

#### Export
- `POST /api/documents/export/json` - Export documents as JSON
- `POST /api/documents/export/zip` - Export documents as ZIP archive
- `POST /api/documents/export/csv` - Export document metadata as CSV

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

## Helper Scripts

The project includes several utility scripts located in `backend/helper/` for maintenance and debugging purposes.

### check_docs.py

Lists all documents stored in the database.

**Usage:**
```bash
cd backend
python helper/check_docs.py
```

**Output:** Displays the number of documents and their filenames with IDs.

### recreate_collection.py

Recreates the 'documents' collection in Qdrant. Useful for resetting the vector database.

**Usage:**
```bash
cd backend
python helper/recreate_collection.py
```

**Note:** This will delete all existing vectors in the 'documents' collection. Use with caution.

### recreate_memory.py

Recreates the 'memory' collection in Qdrant. Useful for resetting the memory vector database.

**Usage:**
```bash
cd backend
python helper/recreate_memory.py
```

**Note:** This will delete all existing vectors in the 'memory' collection. Use with caution.

## Production Deployment

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
- Password hashing using bcrypt
- Access control for documents (public/private/shared)
- User-specific permissions (view, edit, admin)
- Input validation and sanitization
- File type restrictions (PDF and DOCX only)
- File size limits
- Audit logging through version history and analytics

## Limitations and Future Enhancements

### Current Limitations
- Basic RAG implementation (can be enhanced with LLM integration)
- SQLite database (suitable for development, consider PostgreSQL for production)
- Local file storage (consider cloud storage for production)
- Frontend UI for advanced features pending implementation

### Completed Features ✅
- [x] Document preview
- [x] Advanced access control with user-specific permissions
- [x] Document versioning with rollback
- [x] Collaborative features (sharing and permissions)
- [x] Export functionality (JSON, ZIP, CSV)
- [x] Analytics and usage statistics
- [x] Favorites/bookmarking system
- [x] Bulk operations

### Planned Enhancements
- [ ] Integration with OpenAI GPT for advanced RAG
- [ ] More document formats (TXT, MD, etc.)
- [ ] User groups and team-based permissions
- [ ] Full-text search alongside vector search
- [ ] Batch upload
- [ ] Document comparison between versions
- [ ] Advanced analytics dashboard with charts
- [ ] Email notifications for shares and updates
- [ ] Document templates
- [ ] Workflow automation

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