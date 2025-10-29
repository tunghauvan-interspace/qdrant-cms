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
    # Using paraphrase-MiniLM-L3-v2: smaller and faster than all-MiniLM-L6-v2
    # Alternative options:
    # - "all-MiniLM-L6-v2": 80MB, good quality (previous default)
    # - "paraphrase-MiniLM-L3-v2": 60MB, lighter and faster (new default)
    # - "paraphrase-multilingual-MiniLM-L12-v2": 420MB, for multilingual (Vietnamese support)
    embedding_model_name: str = "paraphrase-MiniLM-L3-v2"
    
    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./documents.db"
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application Settings
    upload_dir: str = "./uploads"
    max_file_size: int = 50000000  # 50MB
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
