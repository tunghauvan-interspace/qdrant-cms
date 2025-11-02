from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Dict
from database import get_db
from app.models.models import Document, User, DocumentChunk
from app.schemas.schemas import SearchQuery, SearchResult, RAGQuery, RAGResponse, DocumentResponse, ChunkMatch
from app.services.auth_service import get_current_user
from app.services.qdrant_service import qdrant_service

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.post("/semantic", response_model=List[SearchResult])
async def semantic_search(
    search_query: SearchQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Perform semantic search across documents, grouping results by document"""
    # Search in Qdrant
    results = qdrant_service.search(
        query=search_query.query,
        top_k=search_query.top_k,
        filter_conditions=search_query.filters
    )
    
    # Group results by document
    document_chunks: Dict[int, Dict] = {}
    
    for result in results:
        document_id = result["payload"]["document_id"]
        chunk_index = result["payload"].get("chunk_index", 0)
        
        # Get chunk ID from database to ensure we have the right chunk reference
        chunk_result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .where(DocumentChunk.chunk_index == chunk_index)
        )
        chunk = chunk_result.scalar_one_or_none()
        
        if not chunk:
            continue
            
        if document_id not in document_chunks:
            document_chunks[document_id] = {
                "filename": result["payload"]["filename"],
                "chunks": [],
                "max_score": result["score"]
            }
        else:
            # Keep track of the highest score
            document_chunks[document_id]["max_score"] = max(
                document_chunks[document_id]["max_score"], 
                result["score"]
            )
        
        # Add chunk to the document's list
        document_chunks[document_id]["chunks"].append({
            "chunk_id": chunk.id,
            "chunk_index": chunk_index,
            "chunk_content": result["payload"]["document"],
            "score": result["score"]
        })
    
    # Fetch document details and create search results
    search_results = []
    for document_id, doc_data in document_chunks.items():
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
        
        # Sort chunks by score (highest first)
        sorted_chunks = sorted(doc_data["chunks"], key=lambda x: x["score"], reverse=True)
        
        # Create ChunkMatch objects
        matching_chunks = [
            ChunkMatch(
                chunk_id=chunk["chunk_id"],
                chunk_index=chunk["chunk_index"],
                chunk_content=chunk["chunk_content"],
                score=chunk["score"]
            )
            for chunk in sorted_chunks
        ]
        
        search_results.append(
            SearchResult(
                document_id=document_id,
                filename=doc_data["filename"],
                chunk_content=sorted_chunks[0]["chunk_content"],  # Show best matching chunk
                score=doc_data["max_score"],  # Use highest score
                document=DocumentResponse.model_validate(document),
                matching_chunks=matching_chunks
            )
        )
    
    # Sort results by score
    search_results.sort(key=lambda x: x.score, reverse=True)
    
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
