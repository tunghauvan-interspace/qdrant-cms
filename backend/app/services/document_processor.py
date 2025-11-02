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
    
    def extract_text_from_pdf(self, file_content: bytes, use_ocr: bool = False) -> str:
        """Extract text from PDF file, optionally using OCR for scanned documents"""
        # If OCR is requested or PDF is scanned, use OCR
        if use_ocr:
            # Check if it's actually a scanned PDF
            is_scanned = ocr_service.check_if_pdf_is_scanned(file_content)
            if is_scanned:
                logger.info("PDF appears to be scanned, using OCR")
                return ocr_service.extract_text_from_scanned_pdf(file_content)
            else:
                logger.info("PDF has extractable text, using standard extraction")
        
        # Standard text extraction
        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    
    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        docx_file = io.BytesIO(file_content)
        doc = DocxDocument(docx_file)
        
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text
    
    def extract_text_from_image(self, file_content: bytes) -> str:
        """Extract text from image file using OCR"""
        return ocr_service.extract_text_from_image(file_content)
    
    def process_document(self, file_content: bytes, file_type: str, use_ocr: bool = False) -> str:
        """Process document and extract text based on file type"""
        if file_type == "pdf":
            return self.extract_text_from_pdf(file_content, use_ocr=use_ocr)
        elif file_type in ["docx", "doc"]:
            return self.extract_text_from_docx(file_content)
        elif file_type in ["png", "jpg", "jpeg"]:
            return self.extract_text_from_image(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        return self.text_splitter.split_text(text)


document_processor = DocumentProcessor()
