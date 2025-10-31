# Quick Start Guide

## Starting the Application with Docker

1. **Clone the repository**:
```bash
git clone https://github.com/tunghauvan-interspace/qdrant-cms.git
cd qdrant-cms
```

2. **Start all services**:
```bash
docker-compose up -d
```

> **Note**: The first build may take 3-5 minutes as it downloads dependencies and ML models. 
> Subsequent builds will be much faster (10-30 seconds) thanks to Docker layer caching.
> See [DOCKER_OPTIMIZATION.md](DOCKER_OPTIMIZATION.md) for details.

3. **Wait for services to start** (about 30 seconds):
```bash
docker-compose logs -f
```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - Qdrant: http://localhost:6333/dashboard

## First Time Setup

1. **Register a new account**:
   - Open http://localhost:3000
   - Click "Register"
   - Enter username, email, and password
   - Click "Register"

2. **Login**:
   - Enter your username and password
   - Click "Sign in"

3. **Upload your first document**:
   - Click the "Upload" tab
   - Choose a PDF or DOCX file
   - (Optional) Add a description
   - (Optional) Add tags (comma-separated)
   - Select access level (private or public)
   - Click "Upload Document"

4. **Search your documents**:
   - Go to "Semantic Search" tab
   - Enter a natural language query
   - Click "Search"
   - View relevant chunks from your documents

5. **Use RAG Query**:
   - Go to "RAG Query" tab
   - Ask a question about your documents
   - Get an AI-generated answer with sources

## Manual Setup (Without Docker)

### Backend Setup

1. **Install Python dependencies**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Start Qdrant**:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env if needed
```

4. **Run the backend**:
```bash
uvicorn main:app --reload
```

### Frontend Setup

1. **Install Node dependencies**:
```bash
cd frontend
npm install
```

2. **Configure environment**:
```bash
cp .env.local.example .env.local
```

3. **Run the frontend**:
```bash
npm run dev
```

## Troubleshooting

### Backend won't start
- Check if Qdrant is running: `docker ps`
- Verify Python version: `python --version` (should be 3.11+)
- Check logs: `docker-compose logs backend`

### Frontend won't start
- Check Node version: `node --version` (should be 18+)
- Clear node_modules: `rm -rf node_modules && npm install`
- Check logs: `docker-compose logs frontend`

### Qdrant connection error
- Ensure Qdrant is running on port 6333
- Check QDRANT_HOST in .env file
- Verify firewall settings

### Upload fails
- Check file format (must be PDF or DOCX)
- Verify file size (max 50MB by default)
- Check uploads directory permissions
- Review backend logs for detailed errors

## API Testing

Use the Swagger UI at http://localhost:8000/docs to test API endpoints directly:

1. Register a user via `/api/auth/register`
2. Login via `/api/auth/login` to get a token
3. Click "Authorize" and enter token as "Bearer YOUR_TOKEN"
4. Test other endpoints

## Stopping the Application

```bash
docker-compose down
```

To remove all data:
```bash
docker-compose down -v
rm -rf uploads qdrant_storage backend/documents.db
```
