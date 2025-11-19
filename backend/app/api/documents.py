from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
import os
import uuid
import json
import logging
from database import get_db
from app.models.models import Document, Tag, DocumentChunk, User
from app.schemas.schemas import (
    DocumentResponse, TagResponse, DocumentPreviewResponse, DocumentUpdate,
    DocumentVersionResponse, DocumentShareCreate, DocumentShareResponse,
    DocumentStatsResponse, DocumentFavoriteResponse, BulkUpdateRequest,
    BulkShareRequest, ExportRequest
)
from app.services.auth_service import get_current_user
from app.services.document_processor import document_processor
from app.services.qdrant_service import qdrant_service
from app.services.version_service import version_service
from app.services.share_service import share_service
from app.services.analytics_service import analytics_service
from app.services.favorite_service import favorite_service
from app.services.export_service import export_service
from app.services.storage_service import storage_service
from app.tasks import process_document_task
from config import settings
import io

router = APIRouter(prefix="/api/documents", tags=["Documents"])
logger = logging.getLogger(__name__)


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
    if file_ext not in ["pdf", "docx", "doc", "md"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, DOCX, DOC, and MD files are supported"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
        )
    
    # Generate unique filename/object name
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    
    try:
        # Upload to MinIO
        storage_service.upload_file(
            file_content, 
            unique_filename, 
            content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to storage: {str(e)}"
        )
    
    # Create document record
    document = Document(
        filename=unique_filename,
        original_filename=file.filename,
        file_type=file_ext,
        file_path=unique_filename, # Storing object name as file_path
        file_size=file_size,
        owner_id=current_user.id,
        description=description,
        is_public=is_public,
        status="pending"
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
    
    await db.commit()
    await db.refresh(document)
    
    # Trigger async processing
    process_document_task.delay(document.id)
    
    # Reload with relationships to avoid MissingGreenlet error
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.tags))
        .where(Document.id == document.id)
    )
    document = result.scalar_one()
    
    return document


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
    
    # Delete file from MinIO
    try:
        storage_service.delete_file(document.file_path)
    except Exception as e:
        logger.error(f"Error deleting file from storage: {e}")
    
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
    highlight_chunks: Optional[str] = None,  # Comma-separated list of chunk IDs to highlight
    chunk_scores: Optional[str] = None,  # Comma-separated list of chunk scores (format: "chunk_id:score,chunk_id:score")
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a preview of document content with optional chunk highlighting and scores"""
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.chunks))
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
        # Download from MinIO
        file_content = storage_service.download_file(document.file_path)
        
        # Extract text from document
        text = document_processor.process_document(file_content, document.file_type)
        
        # Build chunk information with positions in the text
        chunks_info = []
        highlight_chunk_ids = set()
        chunk_score_map = {}  # Map of chunk_id -> score
        
        if highlight_chunks:
            highlight_chunk_ids = set(int(cid) for cid in highlight_chunks.split(",") if cid.strip().isdigit())
        
        # Parse chunk scores if provided (format: "chunk_id:score,chunk_id:score")
        if chunk_scores:
            for pair in chunk_scores.split(","):
                if ":" in pair:
                    try:
                        chunk_id_str, score_str = pair.split(":")
                        chunk_id = int(chunk_id_str.strip())
                        score = float(score_str.strip())
                        # Validate score is in expected range
                        if 0 <= score <= 1:
                            chunk_score_map[chunk_id] = score
                        else:
                            logger.warning(f"Chunk score out of range (0-1): chunk_id={chunk_id}, score={score}")
                    except (ValueError, IndexError) as e:
                        # Log invalid entries for debugging
                        logger.warning(f"Invalid chunk score format '{pair}': {e}")
                        pass  # Skip invalid entries
        
        # Sort chunks by index
        sorted_chunks = sorted(document.chunks, key=lambda c: c.chunk_index)
        
        current_position = 0
        for chunk in sorted_chunks:
            # Find the chunk content in the full text
            chunk_start = text.find(chunk.content, current_position)
            if chunk_start >= 0:
                chunk_end = chunk_start + len(chunk.content)
                chunk_info = {
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "start": chunk_start,
                    "end": chunk_end,
                    "content": chunk.content,
                    "highlighted": chunk.id in highlight_chunk_ids
                }
                
                # Add score if available
                if chunk.id in chunk_score_map:
                    chunk_info["score"] = chunk_score_map[chunk.id]
                
                chunks_info.append(chunk_info)
                current_position = chunk_end
        
        return DocumentPreviewResponse(
            document_id=document.id,
            original_filename=document.original_filename,
            file_type=document.file_type,
            content=text,
            preview_length=len(text),
            chunks=chunks_info
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating preview: {str(e)}"
        )


# ========== Document Editing & Update ==========

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    update_data: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update document metadata (description, tags, visibility)"""
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
    
    # Check edit permission
    has_permission = await share_service.check_permission(
        db, document_id, current_user.id, "edit"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this document"
        )
    
    # Track changes for version history
    changes = []
    
    # Update description
    if update_data.description is not None:
        if document.description != update_data.description:
            changes.append(f"Description updated")
        document.description = update_data.description
    
    # Update visibility
    if update_data.is_public is not None:
        if document.is_public != update_data.is_public:
            changes.append(f"Visibility changed to {update_data.is_public}")
        document.is_public = update_data.is_public
    
    # Update tags
    if update_data.tags is not None:
        old_tags = {tag.name for tag in document.tags}
        new_tags = set(update_data.tags)
        if old_tags != new_tags:
            changes.append(f"Tags updated")
        
        # Clear and re-add tags
        document.tags.clear()
        for tag_name in update_data.tags:
            result = await db.execute(select(Tag).where(Tag.name == tag_name))
            tag = result.scalar_one_or_none()
            
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                await db.flush()
            
            document.tags.append(tag)
    
    # Create version snapshot if changes were made
    if changes:
        await version_service.create_version(
            db, document, current_user.id,
            change_summary="; ".join(changes)
        )
    
    await db.commit()
    await db.refresh(document)
    
    # Reload with relationships
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.tags))
        .where(Document.id == document_id)
    )
    document = result.scalar_one()
    
    return document


# ========== Version Management ==========

@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
async def list_document_versions(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get version history for a document"""
    # Check access
    has_permission = await share_service.check_permission(
        db, document_id, current_user.id, "view"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this document"
        )
    
    versions = await version_service.get_versions(db, document_id)
    return versions


@router.post("/{document_id}/versions/{version_id}/rollback", response_model=DocumentResponse)
async def rollback_to_version(
    document_id: int,
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Rollback document to a specific version"""
    # Check edit permission
    has_permission = await share_service.check_permission(
        db, document_id, current_user.id, "edit"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to rollback this document"
        )
    
    # Get document and version
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
    
    version = await version_service.get_version(db, version_id)
    if not version or version.document_id != document_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    # Perform rollback
    await version_service.rollback_to_version(db, document, version, current_user.id)
    
    await db.commit()
    await db.refresh(document)
    
    return document


# ========== Sharing & Permissions ==========

@router.post("/{document_id}/share", response_model=DocumentShareResponse)
async def share_document(
    document_id: int,
    share_data: DocumentShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Share a document with a user"""
    # Check admin permission (owner or admin share permission)
    has_permission = await share_service.check_permission(
        db, document_id, current_user.id, "admin"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to share this document"
        )
    
    # Verify target user exists
    result = await db.execute(select(User).where(User.id == share_data.user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create share
    share = await share_service.share_document(
        db, document_id, share_data.user_id, 
        share_data.permission, current_user.id
    )
    
    await db.commit()
    
    # Reload with user data
    from app.models.models import DocumentShare as DocumentShareModel
    result = await db.execute(
        select(DocumentShareModel)
        .options(selectinload(DocumentShareModel.user))
        .where(DocumentShareModel.id == share.id)
    )
    share = result.scalar_one()
    
    return share


@router.get("/{document_id}/shares", response_model=List[DocumentShareResponse])
async def list_document_shares(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all shares for a document"""
    # Check admin permission
    has_permission = await share_service.check_permission(
        db, document_id, current_user.id, "admin"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view shares"
        )
    
    shares = await share_service.get_document_shares(db, document_id)
    return shares


@router.delete("/shares/{share_id}")
async def remove_document_share(
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a document share"""
    # Get share to check document
    from app.models.models import DocumentShare
    result = await db.execute(
        select(DocumentShare)
        .where(DocumentShare.id == share_id)
    )
    share = result.scalar_one_or_none()
    
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )
    
    # Check admin permission
    has_permission = await share_service.check_permission(
        db, share.document_id, current_user.id, "admin"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to remove this share"
        )
    
    success = await share_service.remove_share(db, share_id)
    await db.commit()
    
    return {"message": "Share removed successfully"}


@router.get("/shared-with-me", response_model=List[DocumentResponse])
async def list_shared_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get documents shared with current user"""
    documents = await share_service.get_user_shared_documents(db, current_user.id)
    return documents


# ========== Analytics ==========

@router.post("/{document_id}/analytics/view")
async def track_document_view(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Track a document view"""
    # Verify document exists and user has access
    has_permission = await share_service.check_permission(
        db, document_id, current_user.id, "view"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this document"
        )
    
    await analytics_service.track_action(db, document_id, "view", current_user.id)
    await db.commit()
    
    return {"message": "View tracked"}


@router.post("/{document_id}/analytics/download")
async def track_document_download(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Track a document download"""
    has_permission = await share_service.check_permission(
        db, document_id, current_user.id, "view"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this document"
        )
    
    await analytics_service.track_action(db, document_id, "download", current_user.id)
    await db.commit()
    
    return {"message": "Download tracked"}


@router.get("/{document_id}/analytics", response_model=DocumentStatsResponse)
async def get_document_analytics(
    document_id: int,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics for a document"""
    # Check if user is owner or admin
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
    
    if document.owner_id != current_user.id and current_user.is_admin != "true":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only document owner can view analytics"
        )
    
    stats = await analytics_service.get_document_stats(db, document_id, days)
    return stats


@router.get("/analytics/popular", response_model=List[dict])
async def get_popular_documents(
    limit: int = 10,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get most popular documents"""
    popular = await analytics_service.get_popular_documents(
        db, limit, days, current_user.id
    )
    return popular


# ========== Favorites ==========

@router.post("/{document_id}/favorite", response_model=DocumentFavoriteResponse)
async def add_to_favorites(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add document to favorites"""
    # Verify document exists and user has access
    has_permission = await share_service.check_permission(
        db, document_id, current_user.id, "view"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this document"
        )
    
    favorite = await favorite_service.add_favorite(db, document_id, current_user.id)
    await db.commit()
    
    return favorite


@router.delete("/{document_id}/favorite")
async def remove_from_favorites(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove document from favorites"""
    success = await favorite_service.remove_favorite(db, document_id, current_user.id)
    await db.commit()
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )
    
    return {"message": "Removed from favorites"}


@router.get("/favorites", response_model=List[DocumentResponse])
async def list_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's favorite documents"""
    documents = await favorite_service.get_user_favorites(db, current_user.id)
    return documents


# ========== Bulk Operations ==========

@router.post("/bulk/update")
async def bulk_update_documents(
    bulk_data: BulkUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bulk update document metadata"""
    updated_count = 0
    errors = []
    
    for doc_id in bulk_data.document_ids:
        try:
            # Check permission
            has_permission = await share_service.check_permission(
                db, doc_id, current_user.id, "edit"
            )
            if not has_permission:
                errors.append({"document_id": doc_id, "error": "No edit permission"})
                continue
            
            result = await db.execute(
                select(Document)
                .options(selectinload(Document.tags))
                .where(Document.id == doc_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                errors.append({"document_id": doc_id, "error": "Not found"})
                continue
            
            # Apply updates
            if bulk_data.updates.description is not None:
                document.description = bulk_data.updates.description
            
            if bulk_data.updates.is_public is not None:
                document.is_public = bulk_data.updates.is_public
            
            if bulk_data.updates.tags is not None:
                document.tags.clear()
                for tag_name in bulk_data.updates.tags:
                    result = await db.execute(select(Tag).where(Tag.name == tag_name))
                    tag = result.scalar_one_or_none()
                    
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.add(tag)
                        await db.flush()
                    
                    document.tags.append(tag)
            
            # Create version
            await version_service.create_version(
                db, document, current_user.id,
                change_summary="Bulk update"
            )
            
            updated_count += 1
        except Exception as e:
            errors.append({"document_id": doc_id, "error": str(e)})
    
    await db.commit()
    
    return {
        "updated_count": updated_count,
        "errors": errors
    }


@router.post("/bulk/share")
async def bulk_share_documents(
    bulk_data: BulkShareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bulk share documents with a user"""
    shared_count = 0
    errors = []
    
    # Verify target user exists
    result = await db.execute(select(User).where(User.id == bulk_data.user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    for doc_id in bulk_data.document_ids:
        try:
            # Check permission
            has_permission = await share_service.check_permission(
                db, doc_id, current_user.id, "admin"
            )
            if not has_permission:
                errors.append({"document_id": doc_id, "error": "No admin permission"})
                continue
            
            await share_service.share_document(
                db, doc_id, bulk_data.user_id,
                bulk_data.permission, current_user.id
            )
            shared_count += 1
        except Exception as e:
            errors.append({"document_id": doc_id, "error": str(e)})
    
    await db.commit()
    
    return {
        "shared_count": shared_count,
        "errors": errors
    }


# ========== Export ==========

@router.post("/export/json")
async def export_documents_json(
    export_data: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export documents as JSON"""
    # Verify access to all documents
    accessible_docs = []
    for doc_id in export_data.document_ids:
        has_permission = await share_service.check_permission(
            db, doc_id, current_user.id, "view"
        )
        if has_permission:
            accessible_docs.append(doc_id)
    
    if not accessible_docs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No accessible documents to export"
        )
    
    documents = await export_service.export_documents_json(db, accessible_docs)
    
    return {
        "documents": documents,
        "count": len(documents)
    }


@router.post("/export/zip")
async def export_documents_zip(
    export_data: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export documents as ZIP file"""
    # Verify access to all documents
    accessible_docs = []
    for doc_id in export_data.document_ids:
        has_permission = await share_service.check_permission(
            db, doc_id, current_user.id, "view"
        )
        if has_permission:
            accessible_docs.append(doc_id)
    
    if not accessible_docs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No accessible documents to export"
        )
    
    zip_content, filename = await export_service.export_documents_zip(db, accessible_docs)
    
    # Track downloads
    for doc_id in accessible_docs:
        await analytics_service.track_action(db, doc_id, "download", current_user.id)
    await db.commit()
    
    return StreamingResponse(
        io.BytesIO(zip_content),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/export/csv")
async def export_documents_csv(
    export_data: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export document metadata as CSV"""
    # Verify access to all documents
    accessible_docs = []
    for doc_id in export_data.document_ids:
        has_permission = await share_service.check_permission(
            db, doc_id, current_user.id, "view"
        )
        if has_permission:
            accessible_docs.append(doc_id)
    
    if not accessible_docs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No accessible documents to export"
        )
    
    csv_content, filename = await export_service.export_documents_metadata_csv(db, accessible_docs)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
