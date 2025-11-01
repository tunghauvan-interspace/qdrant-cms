from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.models import Document
from typing import List
import json
import zipfile
import io
import os


class ExportService:
    """Service for exporting documents in various formats"""
    
    async def export_document_json(
        self,
        db: AsyncSession,
        document_id: int
    ) -> dict:
        """Export a single document as JSON"""
        result = await db.execute(
            select(Document)
            .options(selectinload(Document.tags))
            .where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            return None
        
        return {
            "id": document.id,
            "filename": document.original_filename,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "upload_date": document.upload_date.isoformat(),
            "description": document.description,
            "is_public": document.is_public,
            "tags": [tag.name for tag in document.tags],
            "version": document.version,
            "last_modified": document.last_modified.isoformat() if document.last_modified else None
        }
    
    async def export_documents_json(
        self,
        db: AsyncSession,
        document_ids: List[int]
    ) -> List[dict]:
        """Export multiple documents as JSON"""
        documents = []
        for doc_id in document_ids:
            doc_data = await self.export_document_json(db, doc_id)
            if doc_data:
                documents.append(doc_data)
        return documents
    
    async def export_document_file(
        self,
        db: AsyncSession,
        document_id: int
    ) -> tuple[bytes, str, str]:
        """Export document in its original format"""
        result = await db.execute(
            select(Document)
            .where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document or not os.path.exists(document.file_path):
            return None, None, None
        
        with open(document.file_path, "rb") as f:
            content = f.read()
        
        return content, document.original_filename, document.file_type
    
    async def export_documents_zip(
        self,
        db: AsyncSession,
        document_ids: List[int]
    ) -> tuple[bytes, str]:
        """Export multiple documents as a ZIP file"""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add documents
            for doc_id in document_ids:
                content, filename, file_type = await self.export_document_file(db, doc_id)
                if content:
                    zip_file.writestr(filename, content)
            
            # Add metadata JSON
            metadata = await self.export_documents_json(db, document_ids)
            zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue(), "documents_export.zip"
    
    async def export_documents_metadata_csv(
        self,
        db: AsyncSession,
        document_ids: List[int]
    ) -> tuple[str, str]:
        """Export document metadata as CSV"""
        import csv
        from io import StringIO
        
        csv_buffer = StringIO()
        fieldnames = ['id', 'filename', 'file_type', 'file_size', 'upload_date', 
                     'description', 'is_public', 'tags', 'version']
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        
        for doc_id in document_ids:
            doc_data = await self.export_document_json(db, doc_id)
            if doc_data:
                # Convert tags list to comma-separated string
                doc_data['tags'] = ', '.join(doc_data['tags']) if doc_data['tags'] else ''
                writer.writerow({k: doc_data.get(k, '') for k in fieldnames})
        
        return csv_buffer.getvalue(), "documents_metadata.csv"


export_service = ExportService()
