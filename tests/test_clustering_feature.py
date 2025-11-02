#!/usr/bin/env python3
"""
Test script for Qdrant CMS clustering feature.
This script tests the document clustering functionality by:
1. Checking existing documents
2. Generating/uploading test documents if needed
3. Testing clustering API endpoints
4. Verifying clustering results
"""

import requests
import json
import os
import sys
from typing import Dict, List, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class ClusteringTester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()

    def authenticate(self) -> bool:
        """Authenticate with the API and get JWT token"""
        print("🔐 Authenticating with API...")

        login_url = f"{API_BASE_URL}/api/auth/login"
        login_data = {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }

        try:
            response = self.session.post(login_url, data=login_data)
            response.raise_for_status()
            token_data = response.json()
            self.token = token_data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print("✅ Authentication successful")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Authentication failed: {e}")
            return False

    def check_existing_documents(self) -> List[Dict]:
        """Check what documents are currently available"""
        print("📄 Checking existing documents...")

        try:
            response = self.session.get(f"{API_BASE_URL}/api/documents/")
            response.raise_for_status()
            documents = response.json()
            print(f"📊 Found {len(documents)} existing documents")

            if documents:
                print("📋 Existing documents:")
                for doc in documents[:5]:  # Show first 5
                    print(f"   • {doc['original_filename']} (ID: {doc['id']})")
                if len(documents) > 5:
                    print(f"   ... and {len(documents) - 5} more")

            return documents
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch documents: {e}")
            return []

    def upload_test_documents(self) -> bool:
        """Upload test documents if we don't have enough"""
        print("📤 Uploading test documents...")

        # Check if we have the test documents directory
        test_docs_dir = "test_documents"
        if not os.path.exists(test_docs_dir):
            print(f"❌ Test documents directory '{test_docs_dir}' not found")
            print("💡 Run 'python tests/generate_docx.py' first to generate test documents")
            return False

        # Get list of DOCX files
        docx_files = [f for f in os.listdir(test_docs_dir) if f.endswith('.docx')]
        if not docx_files:
            print(f"❌ No DOCX files found in '{test_docs_dir}'")
            return False

        print(f"📁 Found {len(docx_files)} DOCX files to upload")

        uploaded_count = 0
        for filename in docx_files[:5]:  # Upload first 5 to keep it manageable
            filepath = os.path.join(test_docs_dir, filename)

            try:
                with open(filepath, 'rb') as f:
                    files = {
                        'file': (filename, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                    }
                    data = {
                        'description': f'Test document: {filename}',
                        'is_public': 'public'
                    }

                    response = self.session.post(
                        f"{API_BASE_URL}/api/documents/upload",
                        files=files,
                        data=data
                    )
                    response.raise_for_status()

                    result = response.json()
                    print(f"   ✅ Uploaded: {filename} (ID: {result['id']})")
                    uploaded_count += 1

            except requests.exceptions.RequestException as e:
                print(f"   ❌ Failed to upload {filename}: {e}")
                continue

        print(f"📊 Successfully uploaded {uploaded_count} documents")
        return uploaded_count > 0

    def test_clustering_generation(self) -> Dict[str, Any]:
        """Test the clustering generation endpoint"""
        print("🎯 Testing clustering generation...")

        # Test different clustering configurations
        test_configs = [
            {
                "name": "Document-level K-means",
                "config": {
                    "algorithm": "kmeans",
                    "n_clusters": 3,
                    "reduction_method": "umap",
                    "level": "document"
                }
            },
            {
                "name": "Chunk-level HDBSCAN",
                "config": {
                    "algorithm": "hdbscan",
                    "min_cluster_size": 2,
                    "reduction_method": "tsne",
                    "level": "chunk"
                }
            }
        ]

        results = {}

        for test_config in test_configs:
            print(f"   🔄 Testing: {test_config['name']}")

            try:
                response = self.session.post(
                    f"{API_BASE_URL}/api/clustering/generate",
                    json=test_config['config']
                )
                response.raise_for_status()

                cluster_result = response.json()
                results[test_config['name']] = cluster_result

                # Validate result structure
                self._validate_cluster_result(cluster_result, test_config['name'])

            except requests.exceptions.RequestException as e:
                print(f"   ❌ {test_config['name']} failed: {e}")
                results[test_config['name']] = {"error": str(e)}
                continue

        return results

    def _validate_cluster_result(self, result: Dict, test_name: str):
        """Validate the structure of clustering results"""
        required_fields = ['points', 'summaries', 'algorithm', 'n_clusters', 'reduction_method', 'level']

        for field in required_fields:
            if field not in result:
                print(f"   ⚠️  Missing field '{field}' in {test_name}")
                return False

        points = result['points']
        summaries = result['summaries']

        if not isinstance(points, list):
            print(f"   ⚠️  'points' is not a list in {test_name}")
            return False

        if not isinstance(summaries, list):
            print(f"   ⚠️  'summaries' is not a list in {test_name}")
            return False

        # Check if we have actual data
        if len(points) == 0:
            print(f"   ⚠️  No points generated in {test_name} (no documents?)")
            return False

        if len(summaries) == 0:
            print(f"   ⚠️  No summaries generated in {test_name}")
            return False

        # Validate point structure
        if points:
            point = points[0]
            required_point_fields = ['id', 'x', 'y', 'cluster_id', 'document_id', 'filename']
            for field in required_point_fields:
                if field not in point:
                    print(f"   ⚠️  Point missing field '{field}' in {test_name}")
                    return False

        # Validate summary structure
        if summaries:
            summary = summaries[0]
            required_summary_fields = ['cluster_id', 'size', 'representative_docs', 'keywords']
            for field in required_summary_fields:
                if field not in summary:
                    print(f"   ⚠️  Summary missing field '{field}' in {test_name}")
                    return False

        print(f"   ✅ {test_name}: {result['n_clusters']} clusters, {len(points)} points")
        return True

    def test_clustering_stats(self) -> Dict[str, Any]:
        """Test the clustering stats endpoint"""
        print("📊 Testing clustering stats endpoint...")

        try:
            response = self.session.get(f"{API_BASE_URL}/api/clustering/stats")
            response.raise_for_status()
            stats = response.json()
            print("✅ Clustering stats retrieved successfully")
            print(f"   📋 Available algorithms: {stats.get('available_algorithms', [])}")
            print(f"   📋 Available reduction methods: {stats.get('available_reduction_methods', [])}")
            print(f"   📋 Available levels: {stats.get('available_levels', [])}")
            return stats
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to get clustering stats: {e}")
            return {"error": str(e)}

    def run_comprehensive_test(self) -> bool:
        """Run comprehensive clustering tests"""
        print("🚀 Starting comprehensive clustering tests...")
        print("=" * 60)

        # Step 1: Authenticate
        if not self.authenticate():
            return False

        # Step 2: Check existing documents
        existing_docs = self.check_existing_documents()

        # Step 3: Upload test documents if needed
        if len(existing_docs) < 5:
            print("📝 Not enough documents for meaningful clustering, uploading test documents...")
            if not self.upload_test_documents():
                print("❌ Failed to upload test documents")
                return False
        else:
            print("✅ Sufficient documents available for testing")

        # Step 4: Test clustering stats
        stats_result = self.test_clustering_stats()

        # Step 5: Test clustering generation
        clustering_results = self.test_clustering_generation()

        # Step 6: Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)

        success_count = 0
        total_tests = 0

        # Check stats
        if "error" not in stats_result:
            success_count += 1
        total_tests += 1

        # Check clustering results
        for test_name, result in clustering_results.items():
            total_tests += 1
            if "error" not in result and len(result.get('points', [])) > 0:
                success_count += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")

        print(f"\n🎯 Overall: {success_count}/{total_tests} tests passed")

        if success_count == total_tests:
            print("🎉 All clustering tests PASSED! The feature is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
            return False

def main():
    """Main test function"""
    tester = ClusteringTester()
    success = tester.run_comprehensive_test()

    if success:
        print("\n✅ Clustering feature verification: SUCCESS")
        sys.exit(0)
    else:
        print("\n❌ Clustering feature verification: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()