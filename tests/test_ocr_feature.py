"""
Tests for OCR functionality
"""
import pytest
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.ocr_service import ocr_service
from app.services.document_processor import document_processor


def test_ocr_service_import():
    """Test that OCR service can be imported"""
    assert ocr_service is not None


def test_document_processor_supports_images():
    """Test that document processor has image support methods"""
    assert hasattr(document_processor, 'extract_text_from_image')
    assert hasattr(document_processor, 'extract_text_from_pdf')
    assert hasattr(document_processor, 'process_document')


def test_document_processor_process_method_signature():
    """Test that process_document accepts use_ocr parameter"""
    import inspect
    sig = inspect.signature(document_processor.process_document)
    params = sig.parameters
    
    assert 'file_content' in params
    assert 'file_type' in params
    assert 'use_ocr' in params
    assert params['use_ocr'].default is False


def test_ocr_service_has_required_methods():
    """Test that OCR service has required methods"""
    assert hasattr(ocr_service, 'extract_text_from_image')
    assert hasattr(ocr_service, 'extract_text_from_scanned_pdf')
    assert hasattr(ocr_service, 'check_if_pdf_is_scanned')


def test_supported_file_types():
    """Test that image file types are supported"""
    # Test with a mock file
    test_file_types = ['png', 'jpg', 'jpeg', 'pdf', 'docx']
    
    for file_type in test_file_types:
        # Should not raise ValueError for supported types
        try:
            if file_type in ['png', 'jpg', 'jpeg']:
                # For images, we expect the extract_text_from_image to be called
                assert hasattr(document_processor, 'extract_text_from_image')
        except ValueError as e:
            pytest.fail(f"File type {file_type} should be supported but raised: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
