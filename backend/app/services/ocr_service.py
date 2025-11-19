import base64
import logging
import io
from typing import List, Optional
from pdf2image import convert_from_bytes
from openai import OpenAI
from config import settings

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self.client = None
        if settings.ocr_api_key:
            self.client = OpenAI(
                api_key=settings.ocr_api_key, 
                base_url=settings.ocr_base_url
            )

    def is_configured(self) -> bool:
        return self.client is not None

    def encode_image(self, image) -> str:
        """Encode PIL Image to base64."""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def extract_text_from_image(self, image) -> str:
        """Extract text from a single PIL image using OCR API."""
        if not self.client:
            raise ValueError("OCR service is not configured (missing API key)")

        try:
            base64_image = self.encode_image(image)

            response = self.client.chat.completions.create(
                model=settings.ocr_model_name,
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
                temperature=settings.ocr_temperature,
                max_tokens=settings.ocr_max_tokens,
                top_p=1,
                presence_penalty=0,
                frequency_penalty=0,
            )

            extracted_text = response.choices[0].message.content
            return extracted_text

        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise

    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF bytes using OCR."""
        if not self.client:
            logger.warning("OCR service not configured, skipping OCR extraction")
            return ""

        try:
            logger.info("Converting PDF bytes to images for OCR")
            images = convert_from_bytes(file_content, dpi=settings.ocr_dpi)
            
            full_text = []
            for i, image in enumerate(images, 1):
                logger.info(f"Processing page {i}/{len(images)} with OCR")
                page_text = self.extract_text_from_image(image)
                full_text.append(f"--- Page {i} ---\n{page_text}")
            
            return "\n\n".join(full_text)

        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}")
            raise

ocr_service = OCRService()
