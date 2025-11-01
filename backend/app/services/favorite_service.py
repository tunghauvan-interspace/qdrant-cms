from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Document, DocumentFavorite
from typing import Optional


class FavoriteService:
    """Service for managing document favorites"""
    
    async def add_favorite(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int
    ) -> DocumentFavorite:
        """Add a document to user's favorites"""
        # Check if already favorited
        result = await db.execute(
            select(DocumentFavorite)
            .where(
                DocumentFavorite.document_id == document_id,
                DocumentFavorite.user_id == user_id
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing
        
        favorite = DocumentFavorite(
            document_id=document_id,
            user_id=user_id
        )
        db.add(favorite)
        await db.flush()
        return favorite
    
    async def remove_favorite(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int
    ) -> bool:
        """Remove a document from user's favorites"""
        result = await db.execute(
            select(DocumentFavorite)
            .where(
                DocumentFavorite.document_id == document_id,
                DocumentFavorite.user_id == user_id
            )
        )
        favorite = result.scalar_one_or_none()
        
        if favorite:
            await db.delete(favorite)
            return True
        return False
    
    async def get_user_favorites(
        self,
        db: AsyncSession,
        user_id: int
    ) -> list[Document]:
        """Get all favorited documents for a user"""
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(Document)
            .join(DocumentFavorite)
            .options(selectinload(Document.tags))
            .where(DocumentFavorite.user_id == user_id)
            .order_by(DocumentFavorite.created_at.desc())
        )
        return result.scalars().all()
    
    async def is_favorited(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int
    ) -> bool:
        """Check if a document is favorited by user"""
        result = await db.execute(
            select(DocumentFavorite)
            .where(
                DocumentFavorite.document_id == document_id,
                DocumentFavorite.user_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None


favorite_service = FavoriteService()
