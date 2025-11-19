"""Configuration management for OCR Extractor."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    base_url: str = Field(default="https://mkp-api.fptcloud.com", alias="OCR_BASE_URL")
    api_key: str = Field(..., alias="OCR_API_KEY")  # Required
    model_name: str = Field(default="gemma-3-27b-it", alias="OCR_MODEL_NAME")
    reconstruction_model_name: str = Field(
        default="gpt-oss-20b", alias="OCR_RECONSTRUCTION_MODEL_NAME"
    )

    # Processing Configuration
    dpi: int = Field(default=200, alias="OCR_DPI")
    max_tokens: int = Field(default=2048, alias="OCR_MAX_TOKENS")
    temperature: float = Field(default=1.0, alias="OCR_TEMPERATURE")

    # Output Configuration
    output_dir: str = Field(default="img", alias="OCR_OUTPUT_DIR")
    default_output_file: str = Field(
        default="extracted_text.md", alias="OCR_OUTPUT_FILE"
    )

    model_config = {
        "env_file": ".env",
        "populate_by_name": True,
    }


# Global settings instance
settings = Settings()
