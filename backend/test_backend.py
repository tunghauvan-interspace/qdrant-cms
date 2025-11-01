"""
Simple test script to verify backend models and services load correctly.
Run this after installing dependencies to ensure everything is set up properly.
"""

import sys
import traceback


def test_imports():
    """Test that all modules can be imported"""
    print("Testing backend imports...")
    
    try:
        print("  ✓ Importing database models...")
        from app.models.models import (
            Document, DocumentVersion, DocumentShare, 
            DocumentAnalytics, DocumentFavorite, User, Tag
        )
        
        print("  ✓ Importing schemas...")
        from app.schemas.schemas import (
            DocumentResponse, DocumentUpdate, DocumentVersionResponse,
            DocumentShareResponse, DocumentStatsResponse, DocumentFavoriteResponse,
            BulkUpdateRequest, BulkShareRequest, ExportRequest
        )
        
        print("  ✓ Importing services...")
        from app.services.version_service import version_service
        from app.services.share_service import share_service
        from app.services.analytics_service import analytics_service
        from app.services.favorite_service import favorite_service
        from app.services.export_service import export_service
        
        print("\n✅ All imports successful!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        traceback.print_exc()
        return False


def test_model_structure():
    """Test that models have expected attributes"""
    print("Testing model structure...")
    
    try:
        from app.models.models import Document, DocumentVersion
        
        # Check Document model has new fields
        doc_fields = ['last_modified', 'version', 'versions', 'shares', 'analytics', 'favorites']
        for field in doc_fields:
            if not hasattr(Document, field):
                print(f"  ❌ Document missing field: {field}")
                return False
        print("  ✓ Document model structure correct")
        
        # Check DocumentVersion model
        version_fields = ['version_number', 'tags_snapshot', 'change_summary']
        for field in version_fields:
            if not hasattr(DocumentVersion, field):
                print(f"  ❌ DocumentVersion missing field: {field}")
                return False
        print("  ✓ DocumentVersion model structure correct")
        
        print("\n✅ Model structure tests passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Model structure test failed: {e}")
        traceback.print_exc()
        return False


def test_service_methods():
    """Test that services have expected methods"""
    print("Testing service methods...")
    
    try:
        from app.services.version_service import version_service
        from app.services.share_service import share_service
        from app.services.analytics_service import analytics_service
        from app.services.favorite_service import favorite_service
        from app.services.export_service import export_service
        
        # Check version service
        assert hasattr(version_service, 'create_version')
        assert hasattr(version_service, 'get_versions')
        assert hasattr(version_service, 'rollback_to_version')
        print("  ✓ Version service methods present")
        
        # Check share service
        assert hasattr(share_service, 'share_document')
        assert hasattr(share_service, 'check_permission')
        assert hasattr(share_service, 'get_user_permission')
        print("  ✓ Share service methods present")
        
        # Check analytics service
        assert hasattr(analytics_service, 'track_action')
        assert hasattr(analytics_service, 'get_document_stats')
        assert hasattr(analytics_service, 'get_popular_documents')
        print("  ✓ Analytics service methods present")
        
        # Check favorite service
        assert hasattr(favorite_service, 'add_favorite')
        assert hasattr(favorite_service, 'remove_favorite')
        assert hasattr(favorite_service, 'get_user_favorites')
        print("  ✓ Favorite service methods present")
        
        # Check export service
        assert hasattr(export_service, 'export_document_json')
        assert hasattr(export_service, 'export_documents_zip')
        assert hasattr(export_service, 'export_documents_metadata_csv')
        print("  ✓ Export service methods present")
        
        print("\n✅ Service method tests passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Service method test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("Backend Verification Tests")
    print("="*60)
    print()
    
    all_passed = True
    
    # Run tests
    all_passed &= test_imports()
    all_passed &= test_model_structure()
    all_passed &= test_service_methods()
    
    # Summary
    print("="*60)
    if all_passed:
        print("✅ All tests passed! Backend is ready to use.")
        print("="*60)
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
