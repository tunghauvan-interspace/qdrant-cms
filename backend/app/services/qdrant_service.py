from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from typing import List, Optional
import uuid
from config import settings


class QdrantService:
    def __init__(self):
        self.client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        self.collection_name = settings.qdrant_collection_name
        
        # Initialize embedding model
        if settings.embedding_model == "sentence-transformers":
            self.embedding_model = SentenceTransformer(settings.embedding_model_name)
            self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
            # Generate vector name to match MCP server expectations
            model_clean = settings.embedding_model_name.replace("/", "-").replace("_", "-").lower()
            self.vector_name = f"fast-{model_clean}"
            self.openai_client = None
        else:
            # For OpenAI embeddings, dimension is typically 1536
            self.embedding_dimension = 1536
            self.vector_name = "openai-ada-002"
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
            self.embedding_model = None
            
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        self.vector_name: VectorParams(size=self.embedding_dimension, distance=Distance.COSINE)
                    }
                )
                print(f"Created collection '{self.collection_name}' with vector '{self.vector_name}'")
            else:
                print(f"Collection '{self.collection_name}' already exists")
        except Exception as e:
            print(f"Warning: Could not check/create collection due to Qdrant version compatibility issue: {e}")
            # Try to create the collection anyway, it will fail silently if it already exists
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        self.vector_name: VectorParams(size=self.embedding_dimension, distance=Distance.COSINE)
                    }
                )
                print(f"Created collection '{self.collection_name}' with vector '{self.vector_name}'")
            except Exception as create_e:
                print(f"Collection '{self.collection_name}' likely already exists: {create_e}")
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if settings.embedding_model == "sentence-transformers":
            return self.embedding_model.encode(text).tolist()
        else:
            # Use official OpenAI SDK for embeddings
            response = self.openai_client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
    
    def add_document_chunk(
        self, 
        chunk_id: str, 
        text: str, 
        document_id: int,
        metadata: Optional[dict] = None
    ) -> str:
        """Add a document chunk to Qdrant"""
        embedding = self.get_embedding(text)
        
        payload = {
            "document": text,
            "document_id": document_id,
            **(metadata or {})
        }
        
        point = PointStruct(
            id=chunk_id,
            vector={self.vector_name: embedding},
            payload=payload
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        
        return chunk_id
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        filter_conditions: Optional[dict] = None
    ) -> List[dict]:
        """Search for similar documents"""
        query_embedding = self.get_embedding(query)
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=(self.vector_name, query_embedding),
            limit=top_k,
            query_filter=filter_conditions
        )
        
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            }
            for hit in results
        ]
    
    def delete_document_chunks(self, chunk_ids: List[str]):
        """Delete document chunks from Qdrant"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=chunk_ids
        )


qdrant_service = QdrantService()
