#!/usr/bin/env python3
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

client = QdrantClient(host='qdrant', port=6333)
collection_name = 'documents'
vector_name = 'fast-all-minilm-l6-v2'

try:
    print('Deleting existing collection...')
    client.delete_collection(collection_name)
    print('Collection deleted')
except Exception as e:
    print(f'Error deleting collection (might not exist): {e}')

print('Creating new collection with named vector...')
client.create_collection(
    collection_name=collection_name,
    vectors_config={
        vector_name: VectorParams(size=384, distance=Distance.COSINE)
    }
)
print(f'Created collection {collection_name} with vector {vector_name}')