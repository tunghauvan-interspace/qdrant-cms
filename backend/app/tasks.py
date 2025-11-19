import asyncio
from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.models.models import Document, DocumentChunk, Tag
from app.services.storage_service import storage_service
from app.services.document_processor import document_processor
from app.services.qdrant_service import qdrant_service
from app.services.ocr_service import ocr_service
from config import settings
import logging
import uuid
import os

logger = logging.getLogger(__name__)

# Create sync engine for Celery worker
# Convert async sqlite url to sync
sync_db_url = settings.database_url.replace("+aiosqlite", "")
engine = create_engine(sync_db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@shared_task(name="app.tasks.process_document_task")
def process_document_task(document_id: int):
    logger.info(f"Starting processing for document {document_id}")
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return

        document.status = "processing"
        db.commit()

        # Download from MinIO
        try:
            file_content = storage_service.download_file(document.file_path)
        except Exception as e:
            document.status = "failed"
            document.processing_error = f"Download failed: {str(e)}"
            db.commit()
            return

        # Process document
        try:
            # Extract text (with OCR fallback)
            text = document_processor.process_document(file_content, document.file_type)
            
            # Chunk text
            chunks = document_processor.chunk_text(text)
            
            # Store chunks
            for idx, chunk_text in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                
                # Add to Qdrant
                qdrant_service.add_document_chunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    document_id=document.id,
                    metadata={
                        "filename": document.original_filename,
                        "owner_id": document.owner_id,
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
            
            document.status = "completed"
            db.commit()
            logger.info(f"Document {document_id} processed successfully")

        except Exception as e:
            logger.error(f"Processing failed for {document_id}: {e}")
            document.status = "failed"
            document.processing_error = str(e)
            db.commit()

    except Exception as e:
        logger.error(f"Task failed: {e}")
    finally:
        db.close()
