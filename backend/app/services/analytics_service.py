from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.models import DocumentAnalytics, Document
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class AnalyticsService:
    """Service for tracking and reporting document analytics"""
    
    async def track_action(
        self,
        db: AsyncSession,
        document_id: int,
        action: str,
        user_id: Optional[int] = None,
        action_metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentAnalytics:
        """Track a document action (view, download, search_hit)"""
        analytics = DocumentAnalytics(
            document_id=document_id,
            user_id=user_id,
            action=action,
            action_metadata=action_metadata
        )
        db.add(analytics)
        await db.flush()
        return analytics
    
    async def get_document_stats(
        self,
        db: AsyncSession,
        document_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive statistics for a document"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total views
        result = await db.execute(
            select(func.count(DocumentAnalytics.id))
            .where(
                DocumentAnalytics.document_id == document_id,
                DocumentAnalytics.action == "view",
                DocumentAnalytics.timestamp >= cutoff_date
            )
        )
        total_views = result.scalar() or 0
        
        # Total downloads
        result = await db.execute(
            select(func.count(DocumentAnalytics.id))
            .where(
                DocumentAnalytics.document_id == document_id,
                DocumentAnalytics.action == "download",
                DocumentAnalytics.timestamp >= cutoff_date
            )
        )
        total_downloads = result.scalar() or 0
        
        # Total search hits
        result = await db.execute(
            select(func.count(DocumentAnalytics.id))
            .where(
                DocumentAnalytics.document_id == document_id,
                DocumentAnalytics.action == "search_hit",
                DocumentAnalytics.timestamp >= cutoff_date
            )
        )
        total_search_hits = result.scalar() or 0
        
        # Unique viewers
        result = await db.execute(
            select(func.count(func.distinct(DocumentAnalytics.user_id)))
            .where(
                DocumentAnalytics.document_id == document_id,
                DocumentAnalytics.action == "view",
                DocumentAnalytics.timestamp >= cutoff_date,
                DocumentAnalytics.user_id.isnot(None)
            )
        )
        unique_viewers = result.scalar() or 0
        
        # Recent activity (last 10 actions)
        result = await db.execute(
            select(DocumentAnalytics)
            .where(DocumentAnalytics.document_id == document_id)
            .order_by(DocumentAnalytics.timestamp.desc())
            .limit(10)
        )
        recent_views = result.scalars().all()
        
        return {
            "document_id": document_id,
            "total_views": total_views,
            "total_downloads": total_downloads,
            "total_search_hits": total_search_hits,
            "unique_viewers": unique_viewers,
            "recent_views": recent_views,
            "period_days": days
        }
    
    async def get_popular_documents(
        self,
        db: AsyncSession,
        limit: int = 10,
        days: int = 30,
        user_id: Optional[int] = None
    ) -> list[Dict[str, Any]]:
        """Get most popular documents by view count"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = (
            select(
                DocumentAnalytics.document_id,
                func.count(DocumentAnalytics.id).label('view_count')
            )
            .where(
                DocumentAnalytics.action == "view",
                DocumentAnalytics.timestamp >= cutoff_date
            )
            .group_by(DocumentAnalytics.document_id)
            .order_by(func.count(DocumentAnalytics.id).desc())
            .limit(limit)
        )
        
        result = await db.execute(query)
        popular = result.all()
        
        # Get document details
        popular_docs = []
        for doc_id, view_count in popular:
            result = await db.execute(
                select(Document)
                .where(Document.id == doc_id)
            )
            doc = result.scalar_one_or_none()
            if doc:
                # Check if user has access
                if user_id:
                    if doc.owner_id == user_id or doc.is_public == "public":
                        popular_docs.append({
                            "document": doc,
                            "view_count": view_count
                        })
                else:
                    popular_docs.append({
                        "document": doc,
                        "view_count": view_count
                    })
        
        return popular_docs
    
    async def get_user_activity(
        self,
        db: AsyncSession,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user's document activity statistics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total actions
        result = await db.execute(
            select(func.count(DocumentAnalytics.id))
            .where(
                DocumentAnalytics.user_id == user_id,
                DocumentAnalytics.timestamp >= cutoff_date
            )
        )
        total_actions = result.scalar() or 0
        
        # Actions by type
        result = await db.execute(
            select(
                DocumentAnalytics.action,
                func.count(DocumentAnalytics.id).label('count')
            )
            .where(
                DocumentAnalytics.user_id == user_id,
                DocumentAnalytics.timestamp >= cutoff_date
            )
            .group_by(DocumentAnalytics.action)
        )
        actions_by_type = {row[0]: row[1] for row in result.all()}
        
        # Unique documents accessed
        result = await db.execute(
            select(func.count(func.distinct(DocumentAnalytics.document_id)))
            .where(
                DocumentAnalytics.user_id == user_id,
                DocumentAnalytics.timestamp >= cutoff_date
            )
        )
        unique_documents = result.scalar() or 0
        
        return {
            "user_id": user_id,
            "total_actions": total_actions,
            "actions_by_type": actions_by_type,
            "unique_documents": unique_documents,
            "period_days": days
        }


analytics_service = AnalyticsService()
