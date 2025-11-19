"""Core OCR extraction functionality."""

import base64
import logging
from pathlib import Path
from typing import Dict, List, Optional

from docx import Document
from openai import OpenAI
from pdf2image import convert_from_path

from .config import settings

logger = logging.getLogger(__name__)


class PDFTextExtractor:
    """Main class for PDF to text extraction using OCR."""

    def __init__(self):
        """Initialize the extractor with API client."""
        self.client = OpenAI(api_key=settings.api_key, base_url=settings.base_url)
        self.extracted_data: List[Dict] = []

    def extract_images_from_pdf(
        self, pdf_path: str, output_dir: Optional[str] = None
    ) -> List[str]:
        """Extract all pages of a PDF as images.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save images (uses config default if None)

        Returns:
            List of saved image paths
        """
        output_path = Path(output_dir or settings.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        pdf_name = Path(pdf_path).stem

        try:
            logger.info(f"Converting PDF: {pdf_path}")
            images = convert_from_path(pdf_path, dpi=settings.dpi)

            saved_images = []
            for i, image in enumerate(images, 1):
                image_filename = f"{pdf_name}_page_{i}.png"
                image_path = output_path / image_filename
                image.save(str(image_path), "PNG")
                saved_images.append(str(image_path))
                logger.info(f"Saved page {i}: {image_path}")

            logger.info(f"Total images extracted: {len(saved_images)}")
            return saved_images

        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            raise

    def encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from a single image using OCR API."""
        try:
            logger.info(f"Processing: {Path(image_path).name}")
            base64_image = self.encode_image(image_path)

            response = self.client.chat.completions.create(
                model=settings.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text from this image. Preserve formatting and structure.",
                            },
                            {
                                "type": "image_url",
                                "image_url": f"data:image/png;base64,{base64_image}",
                            },
                        ],
                    }
                ],
                stream=False,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                top_p=1,
                presence_penalty=0,
                frequency_penalty=0,
            )

            extracted_text = response.choices[0].message.content
            logger.info(f"Text extracted ({len(extracted_text)} characters)")
            return extracted_text

        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            raise

    def extract_text_from_images(self, image_paths: List[str]) -> Dict[str, str]:
        """Extract text from multiple images."""
        logger.info(f"Extracting text from {len(image_paths)} image(s)...")

        results = {}
        for image_path in image_paths:
            text = self.extract_text_from_image(image_path)
            results[image_path] = text
            self.extracted_data.append({"image": image_path, "text": text})

        return results

    def save_results(
        self, results: Dict[str, str], output_file: Optional[str] = None
    ) -> None:
        """Save extracted text to markdown file."""
        output_path = Path(output_file or settings.default_output_file)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("# Extracted Text from PDF\n\n")
                f.write(f"Total pages processed: {len(results)}\n\n")

                for i, (image_path, text) in enumerate(results.items(), 1):
                    f.write(f"## Page {i}: {Path(image_path).name}\n\n")
                    f.write(text)
                    f.write("\n\n---\n\n")

            logger.info(f"Results saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            raise

    def process_pdf(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None,
        output_file: Optional[str] = None,
    ) -> Dict[str, str]:
        """Complete workflow: extract images and text from PDF."""
        logger.info("Starting PDF to text extraction pipeline")

        # Step 1: Extract images
        images = self.extract_images_from_pdf(pdf_path, output_dir)
        if not images:
            raise ValueError("No images extracted from PDF")

        # Step 2: Extract text from images
        results = self.extract_text_from_images(images)

        # Step 3: Save results
        self.save_results(results, output_file)

        logger.info("Processing complete!")
        return results

    def reconstruct_document(self, extracted_text: str) -> str:
        """Reconstruct a complete document from extracted text.

        Args:
            extracted_text: The raw extracted text (e.g. from markdown file)

        Returns:
            Reconstructed coherent document text
        """
        try:
            logger.info("Reconstructing document from extracted text...")

            response = self.client.chat.completions.create(
                model=settings.reconstruction_model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a document reconstruction expert. Your task is to take text extracted from a PDF (which may contain page numbers, headers, footers, and split paragraphs) and reconstruct it into a single, coherent, well-formatted document. Remove artifacts like '## Page X', page numbers, and redundant headers/footers. Merge paragraphs that were split across pages.",
                    },
                    {
                        "role": "user",
                        "content": f"Here is the extracted text:\n\n{extracted_text}",
                    },
                ],
                stream=False,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                top_p=1,
                presence_penalty=0,
                frequency_penalty=0,
            )

            reconstructed_text = response.choices[0].message.content
            logger.info(
                f"Document reconstructed ({len(reconstructed_text)} characters)"
            )
            return reconstructed_text

        except Exception as e:
            logger.error(f"Error reconstructing document: {e}")
            raise

    def save_to_docx(self, text: str, output_file: str) -> None:
        """Save text to a DOCX file.

        Args:
            text: The text to save
            output_file: Path to the output DOCX file
        """
        try:
            doc = Document()
            # Split text by newlines to create paragraphs
            for paragraph in text.split("\n"):
                if paragraph.strip():
                    doc.add_paragraph(paragraph)
            
            doc.save(output_file)
            logger.info(f"Saved DOCX to: {output_file}")
        except Exception as e:
            logger.error(f"Error saving DOCX: {e}")
            raise


def extract_text_from_images_batch(image_paths: List[str]) -> Dict[str, str]:
    """Extract text from multiple images (standalone function)."""
    extractor = PDFTextExtractor()
    return extractor.extract_text_from_images(image_paths)


def get_images_from_directory(directory: str = "img") -> List[str]:
    """Get all image files from a directory."""
    img_dir = Path(directory)
    if not img_dir.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    # Support common image formats
    image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp"]
    images = []

    for ext in image_extensions:
        images.extend(img_dir.glob(f"*{ext}"))
        images.extend(img_dir.glob(f"*{ext.upper()}"))

    return sorted([str(img) for img in images])
