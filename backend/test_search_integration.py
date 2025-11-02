"""
Integration test example for search improvements.
This demonstrates how the feature works with mock data.
"""

from typing import List, Dict, Any


class MockSearchResult:
    """Mock search result from Qdrant"""
    def __init__(self, doc_id: int, chunk_idx: int, content: str, score: float):
        self.id = f"chunk-{doc_id}-{chunk_idx}"
        self.score = score
        self.payload = {
            "document_id": doc_id,
            "chunk_index": chunk_idx,
            "document": content,
            "filename": f"document-{doc_id}.pdf"
        }


def group_search_results(results: List[MockSearchResult]) -> Dict[int, Dict[str, Any]]:
    """
    Simulates the grouping logic in backend/app/api/search.py
    Groups search results by document ID and aggregates matching chunks.
    """
    document_chunks = {}
    
    for result in results:
        document_id = result.payload["document_id"]
        chunk_index = result.payload["chunk_index"]
        
        if document_id not in document_chunks:
            document_chunks[document_id] = {
                "filename": result.payload["filename"],
                "chunks": [],
                "max_score": result.score
            }
        else:
            document_chunks[document_id]["max_score"] = max(
                document_chunks[document_id]["max_score"],
                result.score
            )
        
        document_chunks[document_id]["chunks"].append({
            "chunk_id": f"chunk-{document_id}-{chunk_index}",
            "chunk_index": chunk_index,
            "chunk_content": result.payload["document"],
            "score": result.score
        })
    
    return document_chunks


def test_search_grouping():
    """
    Test that multiple chunks from the same document are grouped together.
    
    Scenario: Search for "machine learning" returns 5 chunks:
    - 3 chunks from document #1 (ML_Guide.pdf)
    - 2 chunks from document #2 (AI_Basics.pdf)
    
    Expected result: 2 unique documents in results
    """
    print("=" * 70)
    print("Test: Search Result Grouping")
    print("=" * 70)
    
    # Simulate Qdrant returning 5 chunks from 2 documents
    mock_results = [
        MockSearchResult(1, 0, "Machine learning is a subset of AI...", 0.95),
        MockSearchResult(2, 3, "Artificial intelligence overview...", 0.90),
        MockSearchResult(1, 5, "Deep learning uses neural networks...", 0.87),
        MockSearchResult(1, 12, "Training data is crucial for ML...", 0.82),
        MockSearchResult(2, 8, "AI applications in healthcare...", 0.78),
    ]
    
    print(f"\n📥 Input: {len(mock_results)} chunks from Qdrant")
    for r in mock_results:
        print(f"  - Doc {r.payload['document_id']}, Chunk {r.payload['chunk_index']}, "
              f"Score: {r.score:.2f}")
    
    # Group results
    grouped = group_search_results(mock_results)
    
    print(f"\n📤 Output: {len(grouped)} unique documents")
    
    for doc_id, doc_data in grouped.items():
        print(f"\n  Document {doc_id}: {doc_data['filename']}")
        print(f"    Max Score: {doc_data['max_score']:.2f}")
        print(f"    Matching Chunks: {len(doc_data['chunks'])}")
        for chunk in doc_data['chunks']:
            print(f"      - Chunk {chunk['chunk_index']}: {chunk['chunk_content'][:50]}... "
                  f"(score: {chunk['score']:.2f})")
    
    # Assertions
    assert len(grouped) == 2, "Should have 2 unique documents"
    assert len(grouped[1]["chunks"]) == 3, "Document 1 should have 3 matching chunks"
    assert len(grouped[2]["chunks"]) == 2, "Document 2 should have 2 matching chunks"
    assert grouped[1]["max_score"] == 0.95, "Document 1 max score should be 0.95"
    assert grouped[2]["max_score"] == 0.90, "Document 2 max score should be 0.90"
    
    print("\n✅ All assertions passed!")
    return True


def test_highlight_positioning():
    """
    Test that chunk positions are correctly calculated for highlighting.
    
    Scenario: Document with known chunk positions
    Expected: Correct start/end positions returned
    """
    print("\n" + "=" * 70)
    print("Test: Chunk Position Calculation for Highlighting")
    print("=" * 70)
    
    # Mock document content
    full_text = """Introduction to AI

Machine learning is a subset of artificial intelligence that enables computers to learn from data.

Types of Learning

There are three main types: supervised, unsupervised, and reinforcement learning.

Deep learning uses neural networks with multiple layers to process complex patterns."""
    
    # Mock chunks (these would come from database)
    chunks = [
        {
            "chunk_id": 1,
            "chunk_index": 0,
            "content": "Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
            "highlighted": True
        },
        {
            "chunk_id": 2,
            "chunk_index": 2,
            "content": "Deep learning uses neural networks with multiple layers to process complex patterns.",
            "highlighted": True
        }
    ]
    
    print(f"\n📄 Document length: {len(full_text)} characters")
    print(f"🎯 Chunks to highlight: {len([c for c in chunks if c['highlighted']])}")
    
    # Find chunk positions (simulating backend logic)
    current_pos = 0
    for chunk in chunks:
        chunk_start = full_text.find(chunk["content"], current_pos)
        if chunk_start >= 0:
            chunk_end = chunk_start + len(chunk["content"])
            chunk["start"] = chunk_start
            chunk["end"] = chunk_end
            current_pos = chunk_end
            
            print(f"\n  Chunk {chunk['chunk_id']}:")
            print(f"    Position: [{chunk_start}:{chunk_end}]")
            print(f"    Content: {chunk['content'][:60]}...")
            print(f"    Highlighted: {chunk['highlighted']}")
    
    # Assertions
    assert chunks[0]["start"] == 20, f"First chunk should start at position 20, got {chunks[0]['start']}"
    assert chunks[1]["start"] > chunks[0]["end"], "Second chunk should start after first"
    
    print("\n✅ All assertions passed!")
    return True


def test_ui_rendering():
    """
    Test that the frontend correctly renders highlights.
    This is a conceptual test showing the logic.
    """
    print("\n" + "=" * 70)
    print("Test: Frontend Highlight Rendering (Conceptual)")
    print("=" * 70)
    
    content = "Hello world. This is a test. More text here."
    chunks = [
        {"start": 13, "end": 27, "highlighted": True}  # "This is a test"
    ]
    
    print(f"\n📝 Original: {content}")
    print(f"🎨 Highlighting: characters {chunks[0]['start']}-{chunks[0]['end']}")
    
    # Build rendered output (simulating React rendering)
    rendered_parts = []
    last_pos = 0
    
    for chunk in sorted(chunks, key=lambda c: c["start"]):
        # Text before highlight
        if chunk["start"] > last_pos:
            rendered_parts.append(content[last_pos:chunk["start"]])
        
        # Highlighted text
        if chunk["highlighted"]:
            highlighted_text = content[chunk["start"]:chunk["end"]]
            rendered_parts.append(f"[HIGHLIGHT]{highlighted_text}[/HIGHLIGHT]")
        
        last_pos = chunk["end"]
    
    # Remaining text
    if last_pos < len(content):
        rendered_parts.append(content[last_pos:])
    
    rendered = "".join(rendered_parts)
    print(f"\n📺 Rendered: {rendered}")
    
    assert "[HIGHLIGHT]This is a test[/HIGHLIGHT]" in rendered
    
    print("\n✅ Highlighting correctly applied!")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("SEARCH IMPROVEMENTS - INTEGRATION TESTS")
    print("=" * 70)
    
    all_passed = True
    
    try:
        all_passed &= test_search_grouping()
        all_passed &= test_highlight_positioning()
        all_passed &= test_ui_rendering()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        all_passed = False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
