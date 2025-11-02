# Integration Tests

This directory contains integration and end-to-end tests that work with the full Qdrant CMS system.

## Test Scripts

### `generate_docx.py`
Generates test documents and manages server document lifecycle for testing purposes.

**Purpose:** Creates 20 DOCX documents across 5 topics (Technology, Science, History, Literature, Sports) for testing clustering and search functionality.

**Usage:**
```bash
cd tests
python generate_docx.py
```

**Features:**
- Generates topic-specific documents with realistic content
- Authenticates with the backend API
- Clears existing documents before generating new ones
- Uploads generated documents to the server
- Perfect for testing clustering algorithms

### `inspect_clustering.py`
Inspects clustering results to verify all documents are returned in each cluster.

**Purpose:** Tests the clustering API and validates that all documents in each cluster are properly returned (not just representative samples).

**Usage:**
```bash
cd tests
python inspect_clustering.py
```

**Features:**
- Tests clustering generation with K-means algorithm
- Validates that all 20 documents are distributed across clusters
- Shows detailed cluster composition
- Verifies complete document visibility in clustering results

### `test_clustering_feature.py`
Comprehensive test suite for the clustering functionality.

**Purpose:** Runs multiple clustering tests with different algorithms and configurations to ensure the feature works correctly.

**Usage:**
```bash
cd tests
python test_clustering_feature.py
```

**Features:**
- Tests document-level and chunk-level clustering
- Tests K-means and HDBSCAN algorithms
- Validates API responses and cluster statistics
- Provides detailed test reporting

## Prerequisites

Before running these tests:

1. Start the services:
```bash
docker compose up -d --build
```

2. Create an admin user:
```bash
docker compose exec backend python scripts/admin/create_admin_api.py
```

3. Generate test documents (for clustering tests):
```bash
cd tests
python generate_docx.py
```

## Test Categories

- **Document Generation**: `generate_docx.py` - Creates test data
- **Clustering Validation**: `inspect_clustering.py` and `test_clustering_feature.py` - Verify clustering functionality
- **Integration Testing**: All scripts test the full system integration

## Notes

- These tests require the full backend and Qdrant services to be running
- Test documents are uploaded to the actual database and vector store
- Use `generate_docx.py` to clear and regenerate test data between test runs
- The tests are designed to work with the default admin credentials