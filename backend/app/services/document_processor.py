from pypdf import PdfReader
from docx import Document as DocxDocument
from app.utils.text_splitter import RecursiveCharacterTextSplitter
from app.services.ocr_service import ocr_service
from typing import List
import io
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file. Tries pypdf first, falls back to OCR if text is sparse."""
        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)
        
        text = ""
        page_count = 0
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            page_count += 1
        
        # Heuristic: If text is very short relative to page count, it might be a scanned PDF
        # Assuming an average page has at least 50 characters of text
        if len(text.strip()) < (page_count * 50) and ocr_service.is_configured():
            logger.info("PDF text extraction yielded low content. Attempting OCR...")
            try:
                ocr_text = ocr_service.extract_text_from_pdf(file_content)
                if len(ocr_text) > len(text):
                    logger.info("OCR extraction successful and yielded more text.")
                    return ocr_text
            except Exception as e:
                logger.error(f"OCR fallback failed: {e}")
                # Fall back to original text if OCR fails
        
        return text
    
    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        docx_file = io.BytesIO(file_content)
        doc = DocxDocument(docx_file)
        
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text
    
    def extract_text_from_md(self, file_content: bytes) -> str:
        """Extract text from MD file"""
        try:
            # Try to decode as UTF-8 first
            text = file_content.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to latin-1 if UTF-8 fails
            text = file_content.decode('latin-1')
        
        return text
    
    def process_document(self, file_content: bytes, file_type: str) -> str:
        """Process document and extract text based on file type"""
        if file_type == "pdf":
            return self.extract_text_from_pdf(file_content)
        elif file_type in ["docx", "doc"]:
            return self.extract_text_from_docx(file_content)
        elif file_type == "md":
            return self.extract_text_from_md(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        return self.text_splitter.split_text(text)


document_processor = DocumentProcessor()
