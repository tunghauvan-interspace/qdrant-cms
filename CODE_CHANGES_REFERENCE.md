# Key Code Changes - Quick Reference

## Backend Changes

### 1. Schema: Added ChunkMatch and Extended SearchResult
```python
# backend/app/schemas/schemas.py

# NEW: ChunkMatch class for individual matching chunks
class ChunkMatch(BaseModel):
    chunk_id: int
    chunk_index: int
    chunk_content: str
    score: float

# MODIFIED: SearchResult now includes matching_chunks
class SearchResult(BaseModel):
    document_id: int
    filename: str
    chunk_content: str
    score: float
    document: DocumentResponse
    matching_chunks: Optional[List[ChunkMatch]] = None  # NEW field
```

### 2. Search API: Group Results by Document
```python
# backend/app/api/search.py

@router.post("/semantic", response_model=List[SearchResult])
async def semantic_search(...):
    # OLD: Returned each chunk as separate result (duplicates)
    # NEW: Group by document_id
    
    document_chunks: Dict[int, Dict] = {}
    
    for result in results:
        document_id = result["payload"]["document_id"]
        
        # Group chunks by document
        if document_id not in document_chunks:
            document_chunks[document_id] = {
                "filename": result["payload"]["filename"],
                "chunks": [],
                "max_score": result["score"]
            }
        
        # Add chunk to document's list
        document_chunks[document_id]["chunks"].append({
            "chunk_id": chunk.id,
            "chunk_index": chunk_index,
            "chunk_content": result["payload"]["document"],
            "score": result["score"]
        })
    
    # Return one result per document with all matching chunks
    for document_id, doc_data in document_chunks.items():
        search_results.append(
            SearchResult(
                document_id=document_id,
                filename=doc_data["filename"],
                chunk_content=sorted_chunks[0]["chunk_content"],
                score=doc_data["max_score"],
                document=DocumentResponse.model_validate(document),
                matching_chunks=matching_chunks  # NEW
            )
        )
```

### 3. Preview API: Add Highlight Support
```python
# backend/app/api/documents.py

@router.get("/{document_id}/preview")
async def preview_document(
    document_id: int,
    highlight_chunks: Optional[str] = None,  # NEW parameter
    ...
):
    # NEW: Build chunk position info
    chunks_info = []
    highlight_chunk_ids = set()
    if highlight_chunks:
        highlight_chunk_ids = set(int(cid) for cid in highlight_chunks.split(","))
    
    # Find chunk positions in text
    for chunk in sorted_chunks:
        chunk_start = text.find(chunk.content, current_position)
        if chunk_start >= 0:
            chunks_info.append({
                "chunk_id": chunk.id,
                "start": chunk_start,
                "end": chunk_start + len(chunk.content),
                "highlighted": chunk.id in highlight_chunk_ids  # NEW
            })
    
    return DocumentPreviewResponse(
        ...
        chunks=chunks_info  # NEW field
    )
```

## Frontend Changes

### 1. API Types: Extended Interfaces
```typescript
// frontend/lib/api.ts

// NEW interface
export interface ChunkMatch {
  chunk_id: number;
  chunk_index: number;
  chunk_content: string;
  score: number;
}

// MODIFIED: Extended SearchResult
export interface SearchResult {
  document_id: number;
  filename: string;
  chunk_content: string;
  score: number;
  document: Document;
  matching_chunks?: ChunkMatch[];  // NEW field
}

// NEW interface for chunk positions
export interface ChunkInfo {
  chunk_id: number;
  chunk_index: number;
  start: number;
  end: number;
  content: string;
  highlighted: boolean;
}

// MODIFIED: Extended DocumentPreview
export interface DocumentPreview {
  document_id: number;
  original_filename: string;
  file_type: string;
  content: string;
  preview_length: number;
  chunks?: ChunkInfo[];  // NEW field
}

// MODIFIED: Updated previewDocument function
export const previewDocument = async (id: number, highlightChunks?: number[]) => {
  let url = `/api/documents/${id}/preview`;
  if (highlightChunks && highlightChunks.length > 0) {
    url += `?highlight_chunks=${highlightChunks.join(',')}`;  // NEW
  }
  const response = await api.get(url);
  return response.data;
};
```

### 2. Search Results UI: Show Unique Documents
```typescript
// frontend/app/dashboard/page.tsx

// NEW: Badge showing number of matches
{result.matching_chunks && result.matching_chunks.length > 1 && (
  <span className="badge bg-indigo-100 text-indigo-700 text-xs">
    {result.matching_chunks.length} matching sections
  </span>
)}

// NEW: View Document button
<button
  onClick={() => handlePreviewFromSearch(result)}
  className="btn btn-sm btn-primary"
>
  View Document
</button>

// NEW: Handler to preview with highlights
const handlePreviewFromSearch = async (result: SearchResult) => {
  const chunkIds = result.matching_chunks?.map(c => c.chunk_id) || [];
  await handlePreview(result.document_id, chunkIds);
};
```

### 3. Preview Modal: Render Highlights
```typescript
// frontend/app/dashboard/page.tsx

// NEW: Function to render content with highlights
const renderHighlightedContent = (content: string, chunks: ChunkInfo[]) => {
  const sortedChunks = [...chunks].sort((a, b) => a.start - b.start);
  const elements: JSX.Element[] = [];
  let lastPos = 0;
  
  sortedChunks.forEach((chunk, index) => {
    // Text before chunk
    if (chunk.start > lastPos) {
      elements.push(
        <span key={`text-${index}`}>{content.substring(lastPos, chunk.start)}</span>
      );
    }
    
    // Highlighted chunk
    if (chunk.highlighted) {
      elements.push(
        <mark 
          key={`chunk-${index}`}
          className="bg-yellow-200 px-1 rounded"
        >
          {content.substring(chunk.start, chunk.end)}
        </mark>
      );
    }
    
    lastPos = chunk.end;
  });
  
  return <>{elements}</>;
};

// USE in preview modal:
{previewData.chunks && previewData.chunks.length > 0 ? (
  <div className="text-sm text-gray-800 leading-relaxed font-sans whitespace-pre-wrap">
    {renderHighlightedContent(previewData.content, previewData.chunks)}
  </div>
) : (
  <pre className="whitespace-pre-wrap text-sm text-gray-800">
    {previewData.content}
  </pre>
)}
```

## Example Flow

### Before (Problem)
```
User searches "machine learning"
↓
Backend returns 5 chunks:
  1. Doc 42, Chunk 0, "ML is a subset..." (0.95)
  2. Doc 42, Chunk 5, "Deep learning uses..." (0.87)
  3. Doc 42, Chunk 12, "Training data..." (0.82)
  4. Doc 78, Chunk 3, "AI overview..." (0.90)
  5. Doc 78, Chunk 8, "AI in healthcare..." (0.78)
↓
Frontend shows 5 results (Doc 42 appears 3 times!)
❌ Confusing duplicate entries
```

### After (Solution)
```
User searches "machine learning"
↓
Backend groups by document:
  Doc 42: 3 chunks, max score 0.95
  Doc 78: 2 chunks, max score 0.90
↓
Frontend shows 2 results:
  1. Doc 42 [3 matching sections]
  2. Doc 78 [2 matching sections]
✅ Clear, unique results

User clicks "View Document" on Doc 42
↓
Frontend requests preview with chunk IDs: [142, 143, 144]
↓
Backend returns full text with chunk positions
↓
Frontend highlights 3 sections in yellow
✅ Easy to find relevant sections
```

## Testing Example

```python
# Test that grouping works correctly
mock_results = [
    MockSearchResult(1, 0, "First chunk from doc 1", 0.95),
    MockSearchResult(2, 3, "Chunk from doc 2", 0.90),
    MockSearchResult(1, 5, "Second chunk from doc 1", 0.87),
]

grouped = group_search_results(mock_results)

assert len(grouped) == 2  # 2 unique documents
assert len(grouped[1]["chunks"]) == 2  # Doc 1 has 2 chunks
assert grouped[1]["max_score"] == 0.95  # Highest score wins
```
