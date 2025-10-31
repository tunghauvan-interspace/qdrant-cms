from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: str = "false"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class TagCreate(BaseModel):
    name: str


class TagResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True


class DocumentUpload(BaseModel):
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: str = "private"


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    upload_date: datetime
    owner_id: int
    description: Optional[str]
    is_public: str
    tags: List[TagResponse]
    
    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[dict] = None


class SearchResult(BaseModel):
    document_id: int
    filename: str
    chunk_content: str
    score: float
    document: DocumentResponse


class RAGQuery(BaseModel):
    query: str
    top_k: int = 3


class RAGResponse(BaseModel):
    answer: str
    sources: List[SearchResult]


class DocumentPreviewResponse(BaseModel):
    document_id: int
    original_filename: str
    file_type: str
    content: str
    preview_length: int
