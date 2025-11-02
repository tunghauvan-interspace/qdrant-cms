# Visual Guide: Search UI Improvements

## Before vs After Comparison

### Before: Duplicate Document Results
```
Search Results: "machine learning"

┌─────────────────────────────────────────┐
│ 📄 ML_Guide.pdf                        │
│ Relevance: 95%                          │
│ "Machine learning is a subset of AI..." │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 📄 ML_Guide.pdf                        │  ← Same document again!
│ Relevance: 87%                          │
│ "Deep learning uses neural networks..." │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 📄 ML_Guide.pdf                        │  ← Same document third time!
│ Relevance: 82%                          │
│ "Training data is crucial for ML..."    │
└─────────────────────────────────────────┘
```

### After: Unique Documents with Aggregated Matches
```
Search Results: "machine learning"

┌─────────────────────────────────────────┐
│ 📄 ML_Guide.pdf                        │
│ Relevance: 95%  [3 matching sections]  │  ← Badge shows multiple matches
│ "Machine learning is a subset of AI..." │
│                                         │
│ [View Document] ← Opens with highlights│
└─────────────────────────────────────────┘
```

## Document Preview with Highlights

When clicking "View Document" from search results:

```
┌──────────────────────────────────────────────────────────────┐
│  Document Preview: ML_Guide.pdf                              │
│  PDF | 15,234 characters | 3 matching sections highlighted   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Introduction to Machine Learning                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Machine learning is a subset of AI that enables     │  │ ← Highlighted
│  │ computers to learn from data without being           │  │   (yellow bg)
│  │ explicitly programmed.                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Types of Machine Learning                                   │
│                                                              │
│  There are three main types: supervised, unsupervised, and  │
│  reinforcement learning. Each has different applications.    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Deep learning uses neural networks with multiple     │  │ ← Highlighted
│  │ layers to process complex patterns in data.          │  │   (yellow bg)
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Best Practices                                              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Training data is crucial for ML model performance.   │  │ ← Highlighted
│  │ Always validate with separate test datasets.         │  │   (yellow bg)
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Code Flow

### 1. Search Request
```typescript
// User types query and clicks search
handleSearch(query: "machine learning")
  ↓
semanticSearch({ query: "machine learning", top_k: 5 })
  ↓
Backend groups by document_id
  ↓
Returns unique documents with matching_chunks[]
```

### 2. Backend Grouping Logic
```python
# Group results by document
document_chunks: Dict[int, Dict] = {}

for result in qdrant_results:
    document_id = result["payload"]["document_id"]
    
    if document_id not in document_chunks:
        document_chunks[document_id] = {
            "chunks": [],
            "max_score": result["score"]
        }
    
    document_chunks[document_id]["chunks"].append({
        "chunk_id": chunk.id,
        "chunk_content": result["payload"]["document"],
        "score": result["score"]
    })
```

### 3. Preview with Highlights
```typescript
// User clicks "View Document" button
handlePreviewFromSearch(result)
  ↓
Extract chunk IDs: [42, 137, 258]
  ↓
previewDocument(documentId, [42, 137, 258])
  ↓
Backend finds chunk positions in text
  ↓
Frontend highlights chunks with yellow background
```

### 4. Highlight Rendering
```typescript
renderHighlightedContent(content, chunks) {
  // Sort chunks by position
  chunks.sort((a, b) => a.start - b.start)
  
  // Build highlighted content
  for each chunk:
    - Add text before chunk
    - Add <mark className="bg-yellow-200"> around chunk text
    - Continue to next chunk
}
```

## API Response Examples

### Search Response (New Format)
```json
[
  {
    "document_id": 42,
    "filename": "ML_Guide.pdf",
    "chunk_content": "Machine learning is a subset of AI...",
    "score": 0.95,
    "document": { /* full document metadata */ },
    "matching_chunks": [
      {
        "chunk_id": 142,
        "chunk_index": 0,
        "chunk_content": "Machine learning is a subset of AI...",
        "score": 0.95
      },
      {
        "chunk_id": 143,
        "chunk_index": 5,
        "chunk_content": "Deep learning uses neural networks...",
        "score": 0.87
      },
      {
        "chunk_id": 144,
        "chunk_index": 12,
        "chunk_content": "Training data is crucial for ML...",
        "score": 0.82
      }
    ]
  }
]
```

### Preview Response (New Format)
```json
{
  "document_id": 42,
  "original_filename": "ML_Guide.pdf",
  "file_type": "pdf",
  "content": "Full document text...",
  "preview_length": 15234,
  "chunks": [
    {
      "chunk_id": 142,
      "chunk_index": 0,
      "start": 0,
      "end": 150,
      "content": "Machine learning is a subset of AI...",
      "highlighted": true
    },
    {
      "chunk_id": 143,
      "chunk_index": 5,
      "start": 1250,
      "end": 1420,
      "content": "Deep learning uses neural networks...",
      "highlighted": true
    },
    {
      "chunk_id": 144,
      "chunk_index": 12,
      "start": 3580,
      "end": 3730,
      "content": "Training data is crucial for ML...",
      "highlighted": true
    }
  ]
}
```

## UI Components Changed

### Search Results Card
- Added matching sections badge
- Added "View Document" button
- Shows document tags
- Displays best matching chunk content

### Preview Modal
- Enhanced header with match count
- Yellow highlighting for matched chunks
- Maintains full document context
- Accessible color contrast (WCAG AA compliant)

## Benefits

1. **Reduced Clutter**: See each document once instead of multiple times
2. **Better Context**: Full document view with highlights shows surrounding text
3. **Clear Navigation**: Badge shows how many matches without scrolling
4. **Improved UX**: Direct path from search → relevant document sections
5. **Accessibility**: High contrast highlighting, semantic HTML
