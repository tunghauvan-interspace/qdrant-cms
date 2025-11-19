"""Tests for OCR Extractor."""

import pytest
from unittest.mock import patch

from ocr_extractor.extractor import PDFTextExtractor, get_images_from_directory


class TestPDFTextExtractor:
    """Test cases for PDFTextExtractor."""

    @patch("ocr_extractor.extractor.OpenAI")
    def test_init(self, mock_openai):
        """Test extractor initialization."""
        extractor = PDFTextExtractor()
        mock_openai.assert_called_once()
        assert extractor.extracted_data == []

    def test_encode_image(self, tmp_path):
        """Test image encoding to base64."""
        # Create a test image
        test_image = tmp_path / "test.png"
        test_image.write_bytes(b"fake image data")

        extractor = PDFTextExtractor()
        result = extractor.encode_image(str(test_image))

        assert isinstance(result, str)
        assert result == "ZmFrZSBpbWFnZSBkYXRh"  # base64 of "fake image data"

    def test_get_images_from_directory(self, tmp_path):
        """Test getting images from directory."""
        # Create test images
        img_dir = tmp_path / "images"
        img_dir.mkdir()

        (img_dir / "test1.png").write_text("png")
        (img_dir / "test2.jpg").write_text("jpg")
        (img_dir / "test3.jpeg").write_text("jpeg")
        (img_dir / "test4.gif").write_text("gif")
        (img_dir / "test5.webp").write_text("webp")
        (img_dir / "not_image.txt").write_text("text")

        images = get_images_from_directory(str(img_dir))

        assert len(images) == 5
        assert all(str(img_dir) in img for img in images)
        assert any("test1.png" in img for img in images)

    def test_get_images_from_nonexistent_directory(self):
        """Test error when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            get_images_from_directory("nonexistent_dir")
