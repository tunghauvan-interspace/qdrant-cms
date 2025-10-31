from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import os
import uuid
from database import get_db
from app.models.models import Document, Tag, DocumentChunk, User
from app.schemas.schemas import DocumentResponse, TagResponse, DocumentPreviewResponse
from app.services.auth_service import get_current_user
from app.services.document_processor import document_processor
from app.services.qdrant_service import qdrant_service
from config import settings

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    is_public: str = Form("private"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a new document"""
    # Validate file type
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["pdf", "docx", "doc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    
    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Create document record
    document = Document(
        filename=unique_filename,
        original_filename=file.filename,
        file_type=file_ext,
        file_path=file_path,
        file_size=file_size,
        owner_id=current_user.id,
        description=description,
        is_public=is_public
    )
    
    db.add(document)
    await db.flush()
    
    # Process tags
    if tags:
        tag_names = [t.strip() for t in tags.split(",") if t.strip()]
        for tag_name in tag_names:
            result = await db.execute(select(Tag).where(Tag.name == tag_name))
            tag = result.scalar_one_or_none()
            
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                await db.flush()
            
            document.tags.append(tag)
    
    # Process document and create chunks
    try:
        text = document_processor.process_document(file_content, file_ext)
        chunks = document_processor.chunk_text(text)
        
        # Store chunks in Qdrant and database
        for idx, chunk_text in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            
            # Add to Qdrant
            qdrant_service.add_document_chunk(
                chunk_id=chunk_id,
                text=chunk_text,
                document_id=document.id,
                metadata={
                    "filename": document.original_filename,
                    "owner_id": current_user.id,
                    "chunk_index": idx
                }
            )
            
            # Add to database
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=idx,
                content=chunk_text,
                qdrant_point_id=chunk_id
            )
            db.add(chunk)
        
        await db.commit()
        await db.refresh(document)
        
        # Load relationships
        result = await db.execute(
            select(Document)
            .options(selectinload(Document.tags))
            .where(Document.id == document.id)
        )
        document = result.scalar_one()
        
        return document
    
    except Exception as e:
        # Cleanup on error
        await db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all documents accessible by current user"""
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.tags))
        .where(
            (Document.owner_id == current_user.id) | 
            (Document.is_public == "public")
        )
        .offset(skip)
        .limit(limit)
    )
    documents = result.scalars().all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific document"""
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.tags))
        .where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check access permissions
    if document.owner_id != current_user.id and document.is_public != "public":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this document"
        )
    
    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document"""
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this document"
        )
    
    # Get chunk IDs
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
    )
    chunks = result.scalars().all()
    chunk_ids = [chunk.qdrant_point_id for chunk in chunks]
    
    # Delete from Qdrant
    if chunk_ids:
        qdrant_service.delete_document_chunks(chunk_ids)
    
    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete from database
    await db.delete(document)
    await db.commit()
    
    return {"message": "Document deleted successfully"}


@router.get("/tags/all", response_model=List[TagResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all available tags"""
    result = await db.execute(select(Tag))
    tags = result.scalars().all()
    return tags


@router.get("/{document_id}/preview", response_model=DocumentPreviewResponse)
async def preview_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a preview of document content"""
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check access permissions
    if document.owner_id != current_user.id and document.is_public != "public":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this document"
        )
    
    # Read file content and extract text
    try:
        with open(document.file_path, "rb") as f:
            file_content = f.read()
        
        # Extract text from document
        text = document_processor.process_document(file_content, document.file_type)
        
        return DocumentPreviewResponse(
            document_id=document.id,
            original_filename=document.original_filename,
            file_type=document.file_type,
            content=text,
            preview_length=len(text)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating preview: {str(e)}"
        )
