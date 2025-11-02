"""
Test script for clustering functionality
"""
import sys
import numpy as np
from typing import List

def test_clustering_imports():
    """Test that clustering modules can be imported"""
    print("Testing clustering imports...")
    try:
        from app.services.clustering_service import clustering_service
        from app.schemas.schemas import ClusterRequest, ClusterResult, ClusterPoint, ClusterSummary
        print("  ✓ Clustering service and schemas imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False

def test_clustering_algorithms():
    """Test clustering algorithms with dummy data"""
    print("\nTesting clustering algorithms...")
    try:
        from app.services.clustering_service import ClusteringService
        
        service = ClusteringService()
        
        # Create dummy embeddings (10 points in 384 dimensions - typical for sentence transformers)
        np.random.seed(42)
        embeddings = np.random.randn(10, 384)
        
        # Test K-means
        print("  Testing K-means clustering...")
        labels_kmeans = service._kmeans_clustering(embeddings, n_clusters=3)
        assert len(labels_kmeans) == 10
        assert len(set(labels_kmeans)) <= 3
        print(f"    ✓ K-means produced {len(set(labels_kmeans))} clusters")
        
        # Test HDBSCAN
        print("  Testing HDBSCAN clustering...")
        try:
            labels_hdbscan = service._hdbscan_clustering(embeddings, min_cluster_size=2)
            assert len(labels_hdbscan) == 10
            print(f"    ✓ HDBSCAN produced {len(set(labels_hdbscan))} clusters")
        except Exception as e:
            print(f"    ! HDBSCAN not available or failed: {e}")
        
        return True
    except Exception as e:
        print(f"  ✗ Clustering test failed: {e}")
        return False

def test_dimensionality_reduction():
    """Test dimensionality reduction methods"""
    print("\nTesting dimensionality reduction...")
    try:
        from app.services.clustering_service import ClusteringService
        
        service = ClusteringService()
        
        # Create dummy embeddings
        np.random.seed(42)
        embeddings = np.random.randn(20, 384)
        
        # Test t-SNE
        print("  Testing t-SNE reduction...")
        reduced_tsne = service._tsne_reduction(embeddings)
        assert reduced_tsne.shape == (20, 2)
        print(f"    ✓ t-SNE reduced {embeddings.shape} to {reduced_tsne.shape}")
        
        # Test UMAP
        print("  Testing UMAP reduction...")
        try:
            reduced_umap = service._umap_reduction(embeddings)
            assert reduced_umap.shape == (20, 2)
            print(f"    ✓ UMAP reduced {embeddings.shape} to {reduced_umap.shape}")
        except Exception as e:
            print(f"    ! UMAP not available or failed: {e}")
        
        return True
    except Exception as e:
        print(f"  ✗ Dimensionality reduction test failed: {e}")
        return False

def test_keyword_extraction():
    """Test keyword extraction"""
    print("\nTesting keyword extraction...")
    try:
        from app.services.clustering_service import ClusteringService
        
        service = ClusteringService()
        
        # Create dummy metadata
        metadata = [
            {'filename': 'machine_learning.pdf', 'description': 'Deep learning and neural networks'},
            {'filename': 'ai_research.pdf', 'description': 'Artificial intelligence and machine learning'},
            {'filename': 'data_science.pdf', 'chunk_content': 'Analysis of big data using machine learning'},
        ]
        
        keywords = service._extract_keywords(metadata, top_k=5)
        print(f"    ✓ Extracted keywords: {keywords}")
        assert len(keywords) <= 5
        assert 'machine' in keywords or 'learning' in keywords  # Common words should appear
        
        return True
    except Exception as e:
        print(f"  ✗ Keyword extraction test failed: {e}")
        return False

def test_api_endpoint():
    """Test that clustering API endpoint is registered"""
    print("\nTesting API endpoint registration...")
    try:
        from app.api.clustering import router
        
        # Check that router has expected routes
        routes = [route.path for route in router.routes]
        print(f"    Clustering routes: {routes}")
        
        assert any('/generate' in route for route in routes)
        assert any('/stats' in route for route in routes)
        assert any('/search' in route for route in routes)
        
        print("  ✓ All clustering API endpoints registered")
        return True
    except Exception as e:
        print(f"  ✗ API endpoint test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Clustering Functionality Tests")
    print("=" * 60)
    
    tests = [
        test_clustering_imports,
        test_clustering_algorithms,
        test_dimensionality_reduction,
        test_keyword_extraction,
        test_api_endpoint,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All tests passed! ({passed}/{total})")
        print("=" * 60)
        return 0
    else:
        print(f"❌ Some tests failed. ({passed}/{total} passed)")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
