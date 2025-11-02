#!/usr/bin/env python3
"""
Quick test to inspect clustering results and verify all documents are returned
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

def authenticate() -> str:
    """Authenticate and get JWT token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    response.raise_for_status()
    return response.json()["access_token"]

def get_clustering_result(token: str) -> Dict[str, Any]:
    """Get clustering result"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/clustering/generate",
        json={
            "algorithm": "kmeans",
            "n_clusters": 5,
            "reduction_method": "umap",
            "level": "document"
        },
        headers=headers
    )
    response.raise_for_status()
    return response.json()

def main():
    print("🔍 Inspecting clustering results to verify all documents are returned...")
    print("=" * 60)

    try:
        # Authenticate
        token = authenticate()
        print("✅ Authentication successful")

        # Get clustering result
        result = get_clustering_result(token)
        print("✅ Clustering result retrieved")

        # Analyze results
        summaries = result["summaries"]
        print(f"\n📊 Found {len(summaries)} clusters")

        total_docs_in_clusters = 0
        for summary in summaries:
            cluster_id = summary["cluster_id"]
            size = summary["size"]
            docs = summary["representative_docs"]
            doc_count = len(docs)

            print(f"\n🔹 Cluster {cluster_id}:")
            print(f"   • Size: {size} points")
            print(f"   • Documents returned: {doc_count}")
            print(f"   • Document list:")

            for doc in docs:
                print(f"     - {doc['filename']} (ID: {doc['document_id']}, chunks: {doc['count']})")

            total_docs_in_clusters += doc_count

        print(f"\n📈 Total documents across all clusters: {total_docs_in_clusters}")

        # Check if we have all 20 documents
        if total_docs_in_clusters == 20:
            print("✅ SUCCESS: All 20 documents are represented in clusters!")
        else:
            print(f"⚠️  WARNING: Expected 20 documents, but found {total_docs_in_clusters}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()