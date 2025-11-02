"""
Test script to verify search improvements without running the full application.
This script checks that the changes compile correctly.
"""

def test_schema_changes():
    """Test that schema changes are syntactically correct"""
    print("Testing schema changes...")
    
    # Test import
    try:
        import ast
        with open('app/schemas/schemas.py', 'r') as f:
            code = f.read()
        ast.parse(code)
        print("  ✓ schemas.py syntax is valid")
    except SyntaxError as e:
        print(f"  ❌ schemas.py has syntax error: {e}")
        return False
    
    # Check for new classes/fields
    if 'class ChunkMatch' in code:
        print("  ✓ ChunkMatch class added")
    else:
        print("  ❌ ChunkMatch class not found")
        return False
    
    if 'matching_chunks' in code:
        print("  ✓ matching_chunks field added to SearchResult")
    else:
        print("  ❌ matching_chunks field not found")
        return False
    
    if 'chunks: Optional[List[Dict[str, Any]]]' in code:
        print("  ✓ chunks field added to DocumentPreviewResponse")
    else:
        print("  ❌ chunks field not found in DocumentPreviewResponse")
        return False
    
    return True


def test_search_api_changes():
    """Test that search API changes are syntactically correct"""
    print("\nTesting search API changes...")
    
    try:
        import ast
        with open('app/api/search.py', 'r') as f:
            code = f.read()
        ast.parse(code)
        print("  ✓ search.py syntax is valid")
    except SyntaxError as e:
        print(f"  ❌ search.py has syntax error: {e}")
        return False
    
    # Check for grouping logic
    if 'document_chunks: Dict[int, Dict]' in code:
        print("  ✓ Document grouping logic added")
    else:
        print("  ❌ Document grouping logic not found")
        return False
    
    if 'matching_chunks=matching_chunks' in code:
        print("  ✓ matching_chunks passed to SearchResult")
    else:
        print("  ❌ matching_chunks not passed to SearchResult")
        return False
    
    return True


def test_documents_api_changes():
    """Test that documents API changes are syntactically correct"""
    print("\nTesting documents API changes...")
    
    try:
        import ast
        with open('app/api/documents.py', 'r') as f:
            code = f.read()
        ast.parse(code)
        print("  ✓ documents.py syntax is valid")
    except SyntaxError as e:
        print(f"  ❌ documents.py has syntax error: {e}")
        return False
    
    # Check for highlight_chunks parameter
    if 'highlight_chunks: Optional[str]' in code:
        print("  ✓ highlight_chunks parameter added to preview endpoint")
    else:
        print("  ❌ highlight_chunks parameter not found")
        return False
    
    if 'chunks_info' in code and 'highlighted' in code:
        print("  ✓ Chunk highlighting logic added")
    else:
        print("  ❌ Chunk highlighting logic not found")
        return False
    
    return True


def main():
    """Run all tests"""
    print("="*60)
    print("Search Improvements Verification Tests")
    print("="*60)
    print()
    
    all_passed = True
    
    # Run tests
    all_passed &= test_schema_changes()
    all_passed &= test_search_api_changes()
    all_passed &= test_documents_api_changes()
    
    # Summary
    print()
    print("="*60)
    if all_passed:
        print("✅ All syntax tests passed!")
        print("="*60)
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("="*60)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
