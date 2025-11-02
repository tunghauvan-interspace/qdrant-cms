from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "documents"
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    
    # Embedding Configuration
    embedding_model: str = "sentence-transformers"
    # Using all-MiniLM-L6-v2 to match MCP server
    # Alternative options:
    # - "all-MiniLM-L6-v2": 80MB, good quality (current default for compatibility)
    # - "paraphrase-MiniLM-L3-v2": 60MB, lighter and faster
    # - "paraphrase-multilingual-MiniLM-L12-v2": 420MB, for multilingual (Vietnamese support)
    embedding_model_name: str = "all-MiniLM-L6-v2"
    
    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./documents.db"
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    remember_me_expire_days: int = 7  # Extended expiration for "Remember Me"
    
    # Application Settings
    upload_dir: str = "./uploads"
    max_file_size: int = 50000000  # 50MB
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
