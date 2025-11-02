from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from database import get_db
from app.models.models import User
from app.schemas.schemas import (
    ClusterRequest, ClusterResult, ClusterSearchRequest
)
from app.services.auth_service import get_current_user
from app.services.clustering_service import clustering_service

router = APIRouter(prefix="/api/clustering", tags=["Clustering"])


@router.post("/generate", response_model=ClusterResult)
async def generate_clusters(
    request: ClusterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate clusters from document/chunk embeddings.
    
    - **algorithm**: Clustering algorithm (kmeans, hdbscan)
    - **n_clusters**: Number of clusters for K-means (default: 5)
    - **min_cluster_size**: Minimum cluster size for HDBSCAN (default: 5)
    - **reduction_method**: Dimensionality reduction method (umap, tsne)
    - **level**: Clustering level (document, chunk)
    """
    try:
        result = await clustering_service.generate_clusters(request, current_user, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating clusters: {str(e)}"
        )


@router.get("/stats")
async def get_cluster_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about available documents for clustering.
    
    Returns information about the number of documents and chunks available.
    """
    # This endpoint could be extended to return cached cluster stats
    return {
        "message": "Generate clusters to see statistics",
        "available_algorithms": ["kmeans", "hdbscan"],
        "available_reduction_methods": ["umap", "tsne"],
        "available_levels": ["document", "chunk"]
    }


@router.post("/search", response_model=List[Dict[str, Any]])
async def search_within_cluster(
    request: ClusterSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search within a specific cluster.
    
    - **cluster_id**: ID of the cluster to search within
    - **query**: Optional search query (if None, returns all points in cluster)
    - **limit**: Maximum number of results (default: 10)
    - **cluster_result**: The cluster result object containing all points
    """
    try:
        results = await clustering_service.search_within_cluster(
            cluster_id=request.cluster_id,
            points=request.cluster_result.points,
            query=request.query,
            limit=request.limit,
            db=db
        )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching cluster: {str(e)}"
        )
