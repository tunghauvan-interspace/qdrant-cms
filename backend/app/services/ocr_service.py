import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
from pypdf import PdfReader
import io
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class OCRService:
    """Service for extracting text from images and scanned PDFs using OCR"""
    
    # Constants for scanned PDF detection
    PAGES_TO_CHECK = 3  # Number of pages to check for text content
    MIN_TEXT_THRESHOLD = 100  # Minimum characters to consider PDF as text-based
    
    def __init__(self):
        # Default OCR configuration
        self.config = r'--oem 3 --psm 6'  # OEM 3: Default, PSM 6: Assume uniform text block
    
    def _convert_image_to_rgb(self, image: Image.Image) -> Image.Image:
        """
        Convert image to RGB mode if necessary for OCR processing
        
        Args:
            image: PIL Image object
        
        Returns:
            RGB PIL Image object
        """
        if image.mode in ('RGBA', 'LA'):
            # Images with alpha channel
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            return background
        elif image.mode == 'P':
            # Palette mode - convert to RGB
            return image.convert('RGB')
        elif image.mode != 'RGB':
            # Any other mode - convert to RGB
            return image.convert('RGB')
        return image
    
    def extract_text_from_image(self, image_content: bytes, language: str = 'eng') -> str:
        """
        Extract text from an image using OCR
        
        Args:
            image_content: Image file content as bytes
            language: Tesseract language code (default: 'eng' for English)
        
        Returns:
            Extracted text as string
        """
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_content))
            
            # Convert to RGB if necessary
            image = self._convert_image_to_rgb(image)
            
            # Perform OCR
            text = pytesseract.image_to_string(image, lang=language, config=self.config)
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            raise ValueError(f"Failed to extract text from image: {str(e)}")
    
    def extract_text_from_scanned_pdf(self, pdf_content: bytes, language: str = 'eng') -> str:
        """
        Extract text from a scanned PDF using OCR
        
        Args:
            pdf_content: PDF file content as bytes
            language: Tesseract language code (default: 'eng' for English)
        
        Returns:
            Extracted text as string
        """
        try:
            # Convert PDF pages to images
            images = convert_from_bytes(pdf_content)
            
            # Extract text from each page
            all_text = []
            for i, image in enumerate(images):
                logger.info(f"Processing page {i + 1}/{len(images)}")
                
                # Convert to RGB if necessary
                image = self._convert_image_to_rgb(image)
                
                # Perform OCR on the page
                page_text = pytesseract.image_to_string(image, lang=language, config=self.config)
                all_text.append(page_text.strip())
            
            # Combine all pages with page breaks
            return "\n\n".join(all_text)
        except Exception as e:
            logger.error(f"Error extracting text from scanned PDF: {str(e)}")
            raise ValueError(f"Failed to extract text from scanned PDF: {str(e)}")
    
    def check_if_pdf_is_scanned(self, pdf_content: bytes) -> bool:
        """
        Heuristically check if a PDF is scanned (image-based) or has extractable text
        
        Args:
            pdf_content: PDF file content as bytes
        
        Returns:
            True if PDF appears to be scanned, False otherwise
        """
        try:
            pdf_file = io.BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            
            # Check first few pages for text content
            pages_to_check = min(self.PAGES_TO_CHECK, len(reader.pages))
            total_text_length = 0
            
            for i in range(pages_to_check):
                page_text = reader.pages[i].extract_text()
                total_text_length += len(page_text.strip())
            
            # If very little text is extractable, it's likely a scanned PDF
            # Threshold: less than MIN_TEXT_THRESHOLD characters
            return total_text_length < self.MIN_TEXT_THRESHOLD
        except Exception as e:
            logger.warning(f"Error checking if PDF is scanned: {str(e)}")
            # If we can't determine, assume it might need OCR
            return True


# Global instance
ocr_service = OCRService()
