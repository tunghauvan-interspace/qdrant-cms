from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from database import get_db
from app.models.models import Document, User, DocumentChunk
from app.schemas.schemas import SearchQuery, SearchResult, RAGQuery, RAGResponse, DocumentResponse
from app.services.auth_service import get_current_user
from app.services.qdrant_service import qdrant_service

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.post("/semantic", response_model=List[SearchResult])
async def semantic_search(
    search_query: SearchQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Perform semantic search across documents"""
    # Search in Qdrant
    results = qdrant_service.search(
        query=search_query.query,
        top_k=search_query.top_k,
        filter_conditions=search_query.filters
    )
    
    # Fetch document details
    search_results = []
    for result in results:
        document_id = result["payload"]["document_id"]
        
        # Get document
        doc_result = await db.execute(
            select(Document)
            .options(selectinload(Document.tags))
            .where(Document.id == document_id)
        )
        document = doc_result.scalar_one_or_none()
        
        if not document:
            continue
        
        # Check access permissions
        if document.owner_id != current_user.id and document.is_public != "public":
            continue
        
        search_results.append(
            SearchResult(
                document_id=document_id,
                filename=result["payload"]["filename"],
                chunk_content=result["payload"]["document"],
                score=result["score"],
                document=DocumentResponse.model_validate(document)
            )
        )
    
    return search_results


@router.post("/rag", response_model=RAGResponse)
async def rag_search(
    rag_query: RAGQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Perform RAG (Retrieval-Augmented Generation) search"""
    # Search in Qdrant
    results = qdrant_service.search(
        query=rag_query.query,
        top_k=rag_query.top_k
    )
    
    # Fetch document details and filter by permissions
    sources = []
    context_texts = []
    
    for result in results:
        document_id = result["payload"]["document_id"]
        
        # Get document
        doc_result = await db.execute(
            select(Document)
            .options(selectinload(Document.tags))
            .where(Document.id == document_id)
        )
        document = doc_result.scalar_one_or_none()
        
        if not document:
            continue
        
        # Check access permissions
        if document.owner_id != current_user.id and document.is_public != "public":
            continue
        
        context_texts.append(result["payload"]["document"])
        sources.append(
            SearchResult(
                document_id=document_id,
                filename=result["payload"]["filename"],
                chunk_content=result["payload"]["document"],
                score=result["score"],
                document=DocumentResponse.model_validate(document)
            )
        )
    
    # Generate answer using context
    # This is a simple implementation. In production, you would use an LLM
    if context_texts:
        answer = f"Based on the retrieved documents:\n\n"
        answer += f"Query: {rag_query.query}\n\n"
        answer += "Relevant information:\n"
        for i, text in enumerate(context_texts[:3], 1):
            answer += f"{i}. {text[:200]}...\n\n"
        answer += "\nNote: For full RAG capabilities with LLM-generated answers, integrate with OpenAI GPT or similar models."
    else:
        answer = "No relevant documents found for your query."
    
    return RAGResponse(
        answer=answer,
        sources=sources
    )
