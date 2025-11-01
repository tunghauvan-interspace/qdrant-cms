from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
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


class DocumentUpdate(BaseModel):
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[str] = None


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
    last_modified: Optional[datetime] = None
    version: Optional[int] = None
    
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


# Version schemas
class DocumentVersionResponse(BaseModel):
    id: int
    document_id: int
    version_number: int
    description: Optional[str]
    tags_snapshot: Optional[List[str]]
    is_public_snapshot: str
    created_at: datetime
    created_by_id: int
    change_summary: Optional[str]
    
    class Config:
        from_attributes = True


# Share schemas
class DocumentShareCreate(BaseModel):
    user_id: int
    permission: str  # view, edit, admin


class DocumentShareResponse(BaseModel):
    id: int
    document_id: int
    user_id: int
    permission: str
    shared_at: datetime
    shared_by_id: int
    user: UserResponse
    
    class Config:
        from_attributes = True


# Analytics schemas
class DocumentAnalyticsResponse(BaseModel):
    id: int
    document_id: int
    user_id: Optional[int]
    action: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class DocumentStatsResponse(BaseModel):
    document_id: int
    total_views: int
    total_downloads: int
    total_search_hits: int
    unique_viewers: int
    recent_views: List[DocumentAnalyticsResponse]


# Favorite schemas
class DocumentFavoriteResponse(BaseModel):
    id: int
    document_id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Bulk operation schemas
class BulkUpdateRequest(BaseModel):
    document_ids: List[int]
    updates: DocumentUpdate


class BulkShareRequest(BaseModel):
    document_ids: List[int]
    user_id: int
    permission: str


# Export schemas
class ExportRequest(BaseModel):
    document_ids: List[int]
    format: str  # pdf, docx, json
