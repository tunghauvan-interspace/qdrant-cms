from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from collections import Counter, defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.models import Document, DocumentChunk, User
from app.services.qdrant_service import qdrant_service
from app.schemas.schemas import (
    ClusterRequest, ClusterResult, ClusterPoint, 
    ClusterSummary, DocumentResponse
)

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False


class ClusteringService:
    """Service for document/chunk clustering and topic detection"""
    
    def __init__(self):
        self.qdrant_service = qdrant_service
    
    async def generate_clusters(
        self,
        request: ClusterRequest,
        current_user: User,
        db: AsyncSession
    ) -> ClusterResult:
        """Generate clusters from document/chunk embeddings"""
        
        # Fetch all accessible documents for the user
        query = select(Document).options(selectinload(Document.chunks))
        
        # Filter by user's documents and public documents
        query = query.where(
            (Document.owner_id == current_user.id) | 
            (Document.is_public == "public")
        )
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        if not documents:
            return ClusterResult(
                points=[],
                summaries=[],
                algorithm=request.algorithm,
                n_clusters=0,
                reduction_method=request.reduction_method,
                level=request.level
            )
        
        # Collect embeddings and metadata
        embeddings = []
        metadata = []
        
        if request.level == "document":
            # Document-level clustering: average chunk embeddings
            for doc in documents:
                if not doc.chunks:
                    continue
                
                chunk_embeddings = []
                for chunk in doc.chunks:
                    # Retrieve embedding from Qdrant
                    try:
                        vector = await self._get_vector_from_qdrant(chunk.qdrant_point_id)
                        if vector is not None:
                            chunk_embeddings.append(vector)
                    except Exception as e:
                        print(f"Error retrieving vector for chunk {chunk.id}: {e}")
                        continue
                
                if chunk_embeddings:
                    # Average embeddings for document representation
                    doc_embedding = np.mean(chunk_embeddings, axis=0)
                    embeddings.append(doc_embedding)
                    metadata.append({
                        'type': 'document',
                        'id': str(doc.id),
                        'document_id': doc.id,
                        'filename': doc.filename,
                        'description': doc.description
                    })
        else:
            # Chunk-level clustering
            for doc in documents:
                for chunk in doc.chunks:
                    try:
                        vector = await self._get_vector_from_qdrant(chunk.qdrant_point_id)
                        if vector is not None:
                            embeddings.append(vector)
                            metadata.append({
                                'type': 'chunk',
                                'id': str(chunk.id),
                                'document_id': doc.id,
                                'filename': doc.filename,
                                'chunk_index': chunk.chunk_index,
                                'chunk_content': chunk.content[:200]  # Preview
                            })
                    except Exception as e:
                        print(f"Error retrieving vector for chunk {chunk.id}: {e}")
                        continue
        
        if len(embeddings) < 2:
            return ClusterResult(
                points=[],
                summaries=[],
                algorithm=request.algorithm,
                n_clusters=0,
                reduction_method=request.reduction_method,
                level=request.level
            )
        
        embeddings_array = np.array(embeddings)
        
        # Perform clustering
        if request.algorithm == "kmeans":
            n_clusters = min(request.n_clusters or 5, len(embeddings))
            cluster_labels = self._kmeans_clustering(embeddings_array, n_clusters)
        elif request.algorithm == "hdbscan":
            if not HDBSCAN_AVAILABLE:
                raise ValueError("HDBSCAN is not available. Please install hdbscan.")
            cluster_labels = self._hdbscan_clustering(
                embeddings_array, 
                request.min_cluster_size or 5
            )
        else:
            raise ValueError(f"Unknown algorithm: {request.algorithm}")
        
        # Perform dimensionality reduction for visualization
        if request.reduction_method == "umap":
            if not UMAP_AVAILABLE:
                raise ValueError("UMAP is not available. Please install umap-learn.")
            reduced_embeddings = self._umap_reduction(embeddings_array)
        elif request.reduction_method == "tsne":
            reduced_embeddings = self._tsne_reduction(embeddings_array)
        else:
            raise ValueError(f"Unknown reduction method: {request.reduction_method}")
        
        # Create cluster points
        points = []
        for i, (meta, coords, label) in enumerate(
            zip(metadata, reduced_embeddings, cluster_labels)
        ):
            point = ClusterPoint(
                id=meta['id'],
                x=float(coords[0]),
                y=float(coords[1]),
                cluster_id=int(label),
                document_id=meta['document_id'],
                filename=meta['filename'],
                chunk_index=meta.get('chunk_index'),
                chunk_content=meta.get('chunk_content'),
                description=meta.get('description')
            )
            points.append(point)
        
        # Generate cluster summaries
        summaries = await self._generate_cluster_summaries(
            cluster_labels, metadata, embeddings_array, db
        )
        
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        
        return ClusterResult(
            points=points,
            summaries=summaries,
            algorithm=request.algorithm,
            n_clusters=n_clusters,
            reduction_method=request.reduction_method,
            level=request.level
        )
    
    async def _get_vector_from_qdrant(self, point_id: str) -> Optional[np.ndarray]:
        """Retrieve vector from Qdrant by point ID"""
        try:
            points = self.qdrant_service.client.retrieve(
                collection_name=self.qdrant_service.collection_name,
                ids=[point_id],
                with_vectors=True
            )
            
            if points and len(points) > 0:
                vector_data = points[0].vector
                # Handle named vectors
                if isinstance(vector_data, dict):
                    # Get the first vector (should match our vector_name)
                    vector = list(vector_data.values())[0]
                else:
                    vector = vector_data
                return np.array(vector)
        except Exception as e:
            print(f"Error retrieving vector {point_id}: {e}")
        return None
    
    def _kmeans_clustering(self, embeddings: np.ndarray, n_clusters: int) -> np.ndarray:
        """Perform K-means clustering"""
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        return labels
    
    def _hdbscan_clustering(
        self, embeddings: np.ndarray, min_cluster_size: int
    ) -> np.ndarray:
        """Perform HDBSCAN clustering"""
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            metric='euclidean',
            cluster_selection_method='eom'
        )
        labels = clusterer.fit_predict(embeddings)
        return labels
    
    def _umap_reduction(self, embeddings: np.ndarray) -> np.ndarray:
        """Reduce dimensionality using UMAP"""
        n_samples = len(embeddings)
        n_neighbors = min(15, n_samples - 1)
        
        reducer = umap.UMAP(
            n_components=2,
            n_neighbors=n_neighbors,
            min_dist=0.1,
            metric='cosine',
            random_state=42
        )
        reduced = reducer.fit_transform(embeddings)
        return reduced
    
    def _tsne_reduction(self, embeddings: np.ndarray) -> np.ndarray:
        """Reduce dimensionality using t-SNE"""
        n_samples = len(embeddings)
        perplexity = min(30, n_samples - 1)
        
        tsne = TSNE(
            n_components=2,
            perplexity=perplexity,
            random_state=42,
            max_iter=1000
        )
        reduced = tsne.fit_transform(embeddings)
        return reduced
    
    async def _generate_cluster_summaries(
        self,
        cluster_labels: np.ndarray,
        metadata: List[Dict],
        embeddings: np.ndarray,
        db: AsyncSession
    ) -> List[ClusterSummary]:
        """Generate summaries for each cluster"""
        summaries = []
        unique_labels = set(cluster_labels)
        
        for label in sorted(unique_labels):
            if label == -1:  # Noise cluster in HDBSCAN
                continue
            
            # Get indices for this cluster
            cluster_indices = np.where(cluster_labels == label)[0]
            cluster_size = len(cluster_indices)
            
            # Get representative documents (up to 3)
            cluster_metadata = [metadata[i] for i in cluster_indices]
            
            # Group by document_id to avoid duplicates
            docs_by_id = defaultdict(list)
            for meta in cluster_metadata:
                docs_by_id[meta['document_id']].append(meta)
            
            # Select up to 3 representative documents
            representative_docs = []
            for doc_id in list(docs_by_id.keys())[:3]:
                doc_metas = docs_by_id[doc_id]
                representative_docs.append({
                    'document_id': doc_id,
                    'filename': doc_metas[0]['filename'],
                    'description': doc_metas[0].get('description', ''),
                    'count': len(doc_metas)
                })
            
            # Calculate centroid
            cluster_embeddings = embeddings[cluster_indices]
            centroid = np.mean(cluster_embeddings, axis=0).tolist()
            
            # Generate keywords (simple approach: most common words from chunks)
            keywords = self._extract_keywords(cluster_metadata)
            
            summary = ClusterSummary(
                cluster_id=int(label),
                size=cluster_size,
                representative_docs=representative_docs,
                keywords=keywords,
                centroid=centroid
            )
            summaries.append(summary)
        
        return summaries
    
    def _extract_keywords(self, cluster_metadata: List[Dict], top_k: int = 5) -> List[str]:
        """Extract keywords from cluster documents"""
        # Simple keyword extraction: collect all words and find most common
        all_words = []
        
        for meta in cluster_metadata:
            # Use filename and description/chunk content
            text = meta.get('filename', '').lower()
            if meta.get('description'):
                text += ' ' + meta.get('description', '').lower()
            if meta.get('chunk_content'):
                text += ' ' + meta.get('chunk_content', '').lower()
            
            # Simple tokenization
            words = text.split()
            # Filter out common words and short words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
                'that', 'these', 'those', 'it', 'its', 'their', 'there', 'pdf', 'docx'
            }
            filtered_words = [
                w for w in words 
                if len(w) > 3 and w.isalpha() and w not in stop_words
            ]
            all_words.extend(filtered_words)
        
        if not all_words:
            return []
        
        # Get most common words
        word_counts = Counter(all_words)
        keywords = [word for word, count in word_counts.most_common(top_k)]
        return keywords
    
    async def get_cluster_stats(
        self,
        cluster_result: ClusterResult
    ) -> Dict[str, Any]:
        """Get statistics for cluster result"""
        stats = {
            'total_points': len(cluster_result.points),
            'n_clusters': cluster_result.n_clusters,
            'algorithm': cluster_result.algorithm,
            'reduction_method': cluster_result.reduction_method,
            'level': cluster_result.level,
            'cluster_sizes': {}
        }
        
        for summary in cluster_result.summaries:
            stats['cluster_sizes'][summary.cluster_id] = summary.size
        
        return stats
    
    async def search_within_cluster(
        self,
        cluster_id: int,
        points: List[ClusterPoint],
        query: Optional[str],
        limit: int,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Search within a specific cluster"""
        # Filter points by cluster_id
        cluster_points = [p for p in points if p.cluster_id == cluster_id]
        
        if not query:
            # Return all points in cluster (limited)
            return [p.model_dump() for p in cluster_points[:limit]]
        
        # If query provided, perform semantic search on cluster points
        document_ids = list(set(p.document_id for p in cluster_points))
        
        # Get documents
        query_db = select(Document).where(Document.id.in_(document_ids))
        result = await db.execute(query_db)
        documents = result.scalars().all()
        
        # Perform search and filter by cluster
        search_results = []
        for doc in documents:
            for point in cluster_points:
                if point.document_id == doc.id:
                    search_results.append({
                        'document_id': doc.id,
                        'filename': doc.filename,
                        'description': doc.description,
                        'chunk_content': point.chunk_content,
                        'cluster_id': cluster_id
                    })
        
        return search_results[:limit]


clustering_service = ClusteringService()
