# Example Usage Scenarios

## Scenario 1: Company Knowledge Base

A company wants to build an internal knowledge base with technical documentation.

### Setup
1. Upload company documentation (PDFs, DOCX)
2. Tag documents by department or topic
3. Set access level to "private" for internal use

### Usage
- **Employee A** searches: "How to deploy to production?"
- System returns relevant chunks from deployment guides
- Employee reads the exact section they need

### Benefits
- Quick access to information
- No need to read entire documents
- Find related information across multiple documents

## Scenario 2: Research Paper Management

A researcher manages and searches through academic papers.

### Setup
1. Upload research papers (PDFs)
2. Tag by topic, year, or author
3. Keep papers private or share publicly

### Usage
- Search: "machine learning optimization techniques"
- RAG Query: "What are the main approaches to neural network optimization discussed in my papers?"
- Get synthesized answer with sources

### Benefits
- Quickly find relevant papers
- Cross-reference information
- Get summaries and insights

## Scenario 3: Legal Document Search

A law firm manages legal documents and contracts.

### Setup
1. Upload contracts, case files (PDFs, DOCX)
2. Tag by case type, client, date
3. Set appropriate access levels

### Usage
- Search for specific clauses or precedents
- Find similar cases
- Extract relevant information quickly

### Benefits
- Fast document discovery
- Semantic understanding (not just keyword matching)
- Compliance and reference checking

## Testing the System

### Test 1: Basic Upload and Search

1. **Upload a test document**:
   - Create a simple DOCX file with content about "machine learning"
   - Upload it with tag "AI"

2. **Perform search**:
   - Search query: "What is machine learning?"
   - Verify you get relevant results

3. **Test RAG**:
   - Ask: "Explain machine learning from the documents"
   - Check if answer includes content from your document

### Test 2: Multiple Documents

1. **Upload 3-5 different documents** on various topics
2. **Search across all**:
   - Try queries that span multiple documents
   - Verify results from different documents

### Test 3: Access Control

1. **Create two users**
2. **Upload documents**:
   - User 1: Upload private document
   - User 2: Upload public document
3. **Test access**:
   - Verify User 2 cannot access User 1's private documents
   - Verify both can access public documents

### Test 4: Tagging System

1. **Upload documents with tags**: "report", "2024", "finance"
2. **Search by tag** (via search results)
3. **Verify tag filtering** works

### Test 5: Large Documents

1. **Upload a large PDF** (10+ pages)
2. **Verify chunking**: Search for content from different pages
3. **Check performance**: Ensure reasonable response times

## Performance Testing

### Load Test
```bash
# Install apache bench
sudo apt-get install apache2-utils

# Test API endpoint (after getting auth token)
ab -n 100 -c 10 -H "Authorization: Bearer YOUR_TOKEN" \
   http://localhost:8000/api/documents/
```

### Search Performance
- Upload 50+ documents
- Perform various searches
- Measure response times
- Typical: < 1 second for semantic search

## API Testing with curl

### Register User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

### Upload Document
```bash
TOKEN="your_token_here"

curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf" \
  -F "description=Test document" \
  -F "tags=test,demo" \
  -F "is_public=private"
```

### Search
```bash
curl -X POST http://localhost:8000/api/search/semantic \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "top_k": 5
  }'
```

### RAG Query
```bash
curl -X POST http://localhost:8000/api/search/rag \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "top_k": 3
  }'
```

## Expected Results

### Upload Response
```json
{
  "id": 1,
  "filename": "uuid_document.pdf",
  "original_filename": "document.pdf",
  "file_type": "pdf",
  "file_size": 1024000,
  "upload_date": "2024-01-01T00:00:00",
  "owner_id": 1,
  "description": "Test document",
  "is_public": "private",
  "tags": [
    {"id": 1, "name": "test"},
    {"id": 2, "name": "demo"}
  ]
}
```

### Search Response
```json
[
  {
    "document_id": 1,
    "filename": "document.pdf",
    "chunk_content": "Machine learning is...",
    "score": 0.89,
    "document": { /* document details */ }
  }
]
```

### RAG Response
```json
{
  "answer": "Based on the retrieved documents:\n\nQuery: What is machine learning?\n\n...",
  "sources": [ /* search results */ ]
}
```

## Troubleshooting Common Issues

### Issue: No search results
- **Check**: Are documents uploaded and processed?
- **Check**: Is Qdrant collection created?
- **Solution**: Verify backend logs for processing errors

### Issue: Slow searches
- **Check**: How many documents are indexed?
- **Check**: Size of document chunks
- **Solution**: Adjust chunk size in document_processor.py

### Issue: Low quality results
- **Check**: Document quality and content
- **Solution**: Try different queries or embedding models
- **Solution**: Adjust top_k parameter

### Issue: Upload fails
- **Check**: File format (PDF/DOCX only)
- **Check**: File size (default max 50MB)
- **Solution**: Review backend error messages
