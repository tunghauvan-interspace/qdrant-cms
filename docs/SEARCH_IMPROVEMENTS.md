# Search UI Improvements

## Overview
This feature improves the search documentation experience by:
1. Grouping search results by unique documents (instead of showing each matching chunk separately)
2. Highlighting matching chunks when viewing a document from search results
3. Providing better visual feedback about which sections of a document matched the search query

## Changes Made

### Backend Changes

#### 1. Schema Updates (`backend/app/schemas/schemas.py`)
- Added `ChunkMatch` schema to represent individual chunk matches with score
- Extended `SearchResult` to include `matching_chunks` field
- Extended `DocumentPreviewResponse` to include `chunks` field with position information

#### 2. Search API (`backend/app/api/search.py`)
- Modified `semantic_search` endpoint to group results by document ID
- Each document now appears only once in results, with all matching chunks aggregated
- Results are sorted by the highest chunk score for each document
- All matching chunks are included in the `matching_chunks` field

#### 3. Documents API (`backend/app/api/documents.py`)
- Modified `preview_document` endpoint to accept `highlight_chunks` query parameter
- Endpoint now returns chunk position information in the document text
- Chunks marked for highlighting are flagged in the response

### Frontend Changes

#### 1. API Types (`frontend/lib/api.ts`)
- Added `ChunkMatch` interface
- Extended `SearchResult` to include `matching_chunks`
- Added `ChunkInfo` interface for chunk positioning
- Extended `DocumentPreview` to include `chunks`
- Updated `previewDocument` function to accept chunk IDs for highlighting

#### 2. Dashboard (`frontend/app/dashboard/page.tsx`)
- Updated search results display to show unique documents
- Added badge showing number of matching sections per document
- Added "View Document" button to open preview with highlights
- Implemented `renderHighlightedContent` function to highlight matched chunks
- Preview modal now shows highlighted sections in yellow background
- Added accessibility-friendly highlighting with appropriate contrast

## User Experience Improvements

### Before
- Search results showed duplicate document entries (one per matching chunk)
- No way to see which parts of a document matched the query
- Confusing when a document had multiple relevant sections

### After
- Search results show each document only once
- Badge indicates how many sections matched the query
- Clicking "View Document" opens the full document with matching sections highlighted in yellow
- Users can easily navigate to and read the relevant parts of documents
- Maintains context by showing the full document with highlights

## Accessibility Considerations

### Color Contrast
- Highlight color: `bg-yellow-200` (#fef08a) on white background
- Provides sufficient contrast for readability
- Yellow was chosen as it's commonly used for highlighting and has good visibility

### Semantic HTML
- Uses `<mark>` element for highlights (semantic HTML for marked/highlighted text)
- ARIA labels maintained on interactive elements

## Testing

### Backend Tests
Run the syntax verification:
```bash
cd backend
python test_search_improvements.py
```

### Manual Testing Steps
1. Start the application (backend and frontend)
2. Upload multiple documents
3. Perform a search that matches multiple sections in the same document
4. Verify that:
   - Each document appears only once in results
   - Badge shows correct number of matching sections
   - Clicking "View Document" opens preview
   - Matching sections are highlighted in yellow
   - Highlights are accurately positioned in the text

## Technical Details

### Chunk Matching Algorithm
1. Qdrant search returns top-k chunks across all documents
2. Backend groups these chunks by document_id
3. For each document, all matching chunks are preserved
4. Document score is the maximum score among its chunks
5. Results are sorted by this maximum score

### Highlighting Algorithm
1. When preview is requested with chunk IDs, backend:
   - Retrieves full document text
   - Finds each chunk's position in the text
   - Returns chunk boundaries (start, end positions)
2. Frontend renders text with `<mark>` elements for highlighted chunks
3. Non-overlapping chunks are handled by sorting by start position

## Future Enhancements
- Add ability to navigate between highlighted sections
- Allow users to adjust highlight colors for accessibility preferences
- Add option to show/hide highlights
- Implement smooth scrolling to first highlighted section
- Add statistics about match distribution in document
