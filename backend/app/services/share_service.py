from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.models.models import Document, DocumentShare, User
from typing import Optional


class ShareService:
    """Service for managing document sharing and permissions"""
    
    async def share_document(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        permission: str,
        shared_by_id: int
    ) -> DocumentShare:
        """Share a document with a user"""
        # Check if share already exists
        result = await db.execute(
            select(DocumentShare)
            .where(
                DocumentShare.document_id == document_id,
                DocumentShare.user_id == user_id
            )
        )
        existing_share = result.scalar_one_or_none()
        
        if existing_share:
            # Update existing share
            existing_share.permission = permission
            existing_share.shared_by_id = shared_by_id
            return existing_share
        
        # Create new share
        share = DocumentShare(
            document_id=document_id,
            user_id=user_id,
            permission=permission,
            shared_by_id=shared_by_id
        )
        db.add(share)
        await db.flush()
        return share
    
    async def remove_share(
        self,
        db: AsyncSession,
        share_id: int
    ) -> bool:
        """Remove a document share"""
        result = await db.execute(
            select(DocumentShare)
            .where(DocumentShare.id == share_id)
        )
        share = result.scalar_one_or_none()
        
        if share:
            await db.delete(share)
            return True
        return False
    
    async def get_document_shares(
        self,
        db: AsyncSession,
        document_id: int
    ) -> list[DocumentShare]:
        """Get all shares for a document"""
        result = await db.execute(
            select(DocumentShare)
            .options(selectinload(DocumentShare.user))
            .where(DocumentShare.document_id == document_id)
        )
        return result.scalars().all()
    
    async def get_user_shared_documents(
        self,
        db: AsyncSession,
        user_id: int
    ) -> list[Document]:
        """Get all documents shared with a user"""
        result = await db.execute(
            select(Document)
            .join(DocumentShare)
            .where(DocumentShare.user_id == user_id)
        )
        return result.scalars().all()
    
    async def check_permission(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        required_permission: str = "view"
    ) -> bool:
        """Check if user has required permission for document"""
        # Get document
        result = await db.execute(
            select(Document)
            .where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            return False
        
        # Owner has all permissions
        if document.owner_id == user_id:
            return True
        
        # Check if document is public (view only)
        if document.is_public == "public" and required_permission == "view":
            return True
        
        # Check shared permissions
        result = await db.execute(
            select(DocumentShare)
            .where(
                DocumentShare.document_id == document_id,
                DocumentShare.user_id == user_id
            )
        )
        share = result.scalar_one_or_none()
        
        if not share:
            return False
        
        # Permission hierarchy: admin > edit > view
        permission_levels = {"view": 1, "edit": 2, "admin": 3}
        user_level = permission_levels.get(share.permission, 0)
        required_level = permission_levels.get(required_permission, 0)
        
        return user_level >= required_level
    
    async def get_user_permission(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int
    ) -> Optional[str]:
        """Get user's permission level for a document"""
        # Get document
        result = await db.execute(
            select(Document)
            .where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            return None
        
        # Owner has admin permission
        if document.owner_id == user_id:
            return "admin"
        
        # Check if document is public
        if document.is_public == "public":
            return "view"
        
        # Check shared permissions
        result = await db.execute(
            select(DocumentShare)
            .where(
                DocumentShare.document_id == document_id,
                DocumentShare.user_id == user_id
            )
        )
        share = result.scalar_one_or_none()
        
        return share.permission if share else None


share_service = ShareService()
