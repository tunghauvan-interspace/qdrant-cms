from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.models import Document, DocumentVersion, Tag
from typing import Optional
import json


class VersionService:
    """Service for managing document versions"""
    
    async def create_version(
        self,
        db: AsyncSession,
        document: Document,
        user_id: int,
        change_summary: Optional[str] = None
    ) -> DocumentVersion:
        """Create a new version snapshot for a document"""
        # Get current tags
        tags_snapshot = [tag.name for tag in document.tags]
        
        version = DocumentVersion(
            document_id=document.id,
            version_number=document.version,
            description=document.description,
            tags_snapshot=tags_snapshot,
            is_public_snapshot=document.is_public,
            created_by_id=user_id,
            change_summary=change_summary
        )
        
        db.add(version)
        await db.flush()
        
        # Increment document version
        document.version += 1
        
        return version
    
    async def get_versions(
        self,
        db: AsyncSession,
        document_id: int
    ) -> list[DocumentVersion]:
        """Get all versions for a document"""
        result = await db.execute(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.desc())
        )
        return result.scalars().all()
    
    async def get_version(
        self,
        db: AsyncSession,
        version_id: int
    ) -> Optional[DocumentVersion]:
        """Get a specific version"""
        result = await db.execute(
            select(DocumentVersion)
            .where(DocumentVersion.id == version_id)
        )
        return result.scalar_one_or_none()
    
    async def rollback_to_version(
        self,
        db: AsyncSession,
        document: Document,
        version: DocumentVersion,
        user_id: int
    ) -> DocumentVersion:
        """Rollback document to a specific version"""
        # Create a snapshot of current state before rollback
        await self.create_version(
            db, document, user_id,
            change_summary=f"Auto-backup before rollback to version {version.version_number}"
        )
        
        # Restore document metadata from version
        document.description = version.description
        document.is_public = version.is_public_snapshot
        
        # Restore tags
        if version.tags_snapshot:
            # Clear current tags
            document.tags.clear()
            
            # Add tags from snapshot
            for tag_name in version.tags_snapshot:
                result = await db.execute(select(Tag).where(Tag.name == tag_name))
                tag = result.scalar_one_or_none()
                
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                    await db.flush()
                
                document.tags.append(tag)
        
        # Create new version for the rollback
        new_version = await self.create_version(
            db, document, user_id,
            change_summary=f"Rolled back to version {version.version_number}"
        )
        
        return new_version


version_service = VersionService()
