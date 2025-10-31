#!/bin/bash
# Test script to verify sentence-transformers caching optimizations
# This script validates the Dockerfile changes and provides verification steps

set -e

echo "========================================="
echo "Sentence-Transformers Caching Validation"
echo "========================================="
echo ""

# Check if required files exist
echo "1. Checking required files..."
FILES=(
    "backend/Dockerfile"
    "DOCKER_OPTIMIZATION.md"
    "docker-compose.dev-cache.yml"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file exists"
    else
        echo "   ✗ $file missing"
        exit 1
    fi
done
echo ""

# Validate Dockerfile contains optimizations
echo "2. Validating Dockerfile optimizations..."

# Check for pip without --no-cache-dir
if grep -q "pip install --user -r requirements.txt" backend/Dockerfile; then
    echo "   ✓ Pip caching enabled (--no-cache-dir removed)"
else
    echo "   ✗ Pip caching not properly configured"
    exit 1
fi

# Check for model pre-download
if grep -q "SentenceTransformer('paraphrase-MiniLM-L3-v2')" backend/Dockerfile; then
    echo "   ✓ Model pre-download step present"
else
    echo "   ✗ Model pre-download step missing"
    exit 1
fi

# Check for cache directory copy
if grep -q "COPY --from=builder /root/.cache/torch /root/.cache/torch" backend/Dockerfile; then
    echo "   ✓ Model cache copy from builder stage"
else
    echo "   ✗ Model cache copy missing"
    exit 1
fi

# Check for environment variable
if grep -q "SENTENCE_TRANSFORMERS_HOME" backend/Dockerfile; then
    echo "   ✓ Cache environment variable configured"
else
    echo "   ✗ Cache environment variable missing"
    exit 1
fi

# Check for non-root user cache setup
if grep -q "cp -r /root/.cache/torch/\* /home/appuser/.cache/torch/" backend/Dockerfile; then
    echo "   ✓ Non-root user cache setup present"
else
    echo "   ✗ Non-root user cache setup missing"
    exit 1
fi

echo ""
echo "========================================="
echo "All validation checks passed! ✓"
echo "========================================="
echo ""

# Provide manual verification steps
echo "Manual Verification Steps:"
echo "--------------------------"
echo ""
echo "To verify the optimizations work correctly:"
echo ""
echo "1. Build the Docker image (first build):"
echo "   docker-compose build backend"
echo "   (This will take 3-5 minutes as it downloads everything)"
echo ""
echo "2. Check the image was built:"
echo "   docker images | grep qdrant-cms"
echo ""
echo "3. Make a small code change (e.g., add a comment)"
echo "   echo '# Comment' >> backend/main.py"
echo ""
echo "4. Rebuild and time it (should be fast, ~10-30 seconds):"
echo "   time docker-compose build backend"
echo ""
echo "5. Start the container and verify model is cached:"
echo "   docker-compose up -d backend"
echo "   docker-compose exec backend python -c \"from sentence_transformers import SentenceTransformer; model = SentenceTransformer('paraphrase-MiniLM-L3-v2'); print('Model loaded successfully')\""
echo "   (Should complete in < 1 second)"
echo ""
echo "6. Check model cache directory:"
echo "   docker-compose exec backend ls -la /home/appuser/.cache/torch/sentence_transformers"
echo ""
echo "Expected Results:"
echo "- First build: 3-5 minutes"
echo "- Subsequent builds: 10-30 seconds (with code changes only)"
echo "- Model loading: < 1 second (no download)"
echo "- Container startup: Immediate (no waiting for model download)"
echo ""
