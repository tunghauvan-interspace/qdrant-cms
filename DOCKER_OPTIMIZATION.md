# Docker Build Optimization Guide

## Sentence-Transformers Caching

This document explains the optimizations made to improve Docker build times and reduce bandwidth usage when working with sentence-transformers.

## Problem

Previously, the Docker build process had the following inefficiencies:

1. **No pip caching**: Using `--no-cache-dir` forced pip to download all packages from scratch on every build
2. **Runtime model downloads**: The sentence-transformers model was downloaded when the container first started, adding startup time and bandwidth usage
3. **No model caching**: Each new container would need to re-download the ~60MB model

## Solution

The optimized Dockerfile now includes:

### 1. Enable Pip Caching

**Before:**
```dockerfile
RUN pip install --no-cache-dir --user -r requirements.txt
```

**After:**
```dockerfile
RUN pip install --user -r requirements.txt
```

**Benefit**: Docker layer caching will preserve the installed packages. Rebuilds only download changed dependencies.

### 2. Pre-download Models During Build

Added a step to download the sentence-transformers model during the Docker build:

```dockerfile
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-MiniLM-L3-v2')"
```

**Benefit**: The model is downloaded once during build and cached in the Docker image layer.

### 3. Copy Model Cache to Runtime Stage

```dockerfile
COPY --from=builder /root/.cache/torch /root/.cache/torch
```

**Benefit**: The pre-downloaded model is available in the final image without re-downloading.

### 4. Configure Cache Directories

Set environment variables to ensure sentence-transformers uses the cached models:

```dockerfile
ENV SENTENCE_TRANSFORMERS_HOME=/home/appuser/.cache/torch/sentence_transformers
```

**Benefit**: Consistent cache location for both root and non-root users.

## Results

### Build Time Improvements

- **First build**: Similar time (model is downloaded during build)
- **Subsequent builds**: 
  - No changes to requirements.txt: ~10-30 seconds (vs 2-5 minutes previously)
  - Changes to code only: ~10-30 seconds
  - Changes to requirements.txt: Downloads only changed packages

### Runtime Improvements

- **Container startup**: No model download needed (immediate start)
- **Bandwidth**: Model downloaded once per build, not per container instance

### Image Size

The image size increases by approximately 60-80MB to include the pre-downloaded model, but this is a worthwhile trade-off for:
- Faster container startup
- No runtime downloads
- Consistent behavior across environments

## Best Practices

### For Development

When using docker-compose with volume mounts, models are cached on the host:

```yaml
volumes:
  - ./backend:/app
  - model_cache:/home/appuser/.cache/torch
```

### For Production

The optimized Dockerfile is production-ready:
- Models are pre-downloaded
- No runtime dependencies on external downloads
- Faster scaling (new containers start immediately)

### Using Different Models

If you need to use a different sentence-transformers model:

1. Update `config.py`:
   ```python
   embedding_model_name: str = "all-MiniLM-L6-v2"
   ```

2. Update the Dockerfile pre-download step:
   ```dockerfile
   RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
   ```

3. Rebuild the Docker image:
   ```bash
   docker-compose build backend
   ```

## Docker BuildKit Caching

To maximize caching benefits, ensure you're using Docker BuildKit:

```bash
export DOCKER_BUILDKIT=1
docker-compose build
```

Or enable it permanently in `/etc/docker/daemon.json`:

```json
{
  "features": {
    "buildkit": true
  }
}
```

## Troubleshooting

### Model not found at runtime

If you see errors about missing models:

1. Check the cache directory:
   ```bash
   docker-compose exec backend ls -la /home/appuser/.cache/torch/sentence_transformers
   ```

2. Verify the environment variable:
   ```bash
   docker-compose exec backend env | grep SENTENCE_TRANSFORMERS_HOME
   ```

3. Rebuild the image:
   ```bash
   docker-compose build --no-cache backend
   ```

### Slow first build

The first build will take longer as it downloads:
- Python packages (torch, transformers, sentence-transformers)
- The sentence-transformers model (~60-80MB)

This is expected. Subsequent builds will be much faster due to Docker layer caching.

## Additional Optimizations

### Multi-platform Builds

For advanced use cases with multiple architectures, you can use BuildKit cache mounts as an alternative caching strategy:

```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user -r requirements.txt
```

**Note:** This is an alternative approach to the layer caching used in our current Dockerfile. Use this if you need to build for multiple architectures (linux/amd64, linux/arm64, etc.).

### CI/CD Optimization

For CI/CD pipelines, consider:

1. **Docker layer caching**: Use cache-from/cache-to options
2. **Pre-built base images**: Create a base image with common dependencies
3. **Registry caching**: Push intermediate layers to a registry

Example for GitHub Actions:

```yaml
- name: Build Docker image
  uses: docker/build-push-action@v5
  with:
    context: ./backend
    cache-from: type=registry,ref=myregistry/qdrant-cms:cache
    cache-to: type=registry,ref=myregistry/qdrant-cms:cache,mode=max
```

See the example workflow file for complete GitHub Actions examples: [.github-workflows-example.yml](.github-workflows-example.yml)

**Note:** To use the example workflow in your project, copy it to `.github/workflows/docker-build.yml` in your repository.

## Verification

To verify the optimizations are working:

```bash
# Build the image
docker-compose build backend

# Check image size
docker images | grep qdrant-cms

# Start a container and check startup time
time docker-compose up backend

# Verify model is cached
docker-compose exec backend python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('paraphrase-MiniLM-L3-v2'); print('Model loaded successfully')"
```

The last command should complete almost instantly (< 1 second) instead of taking several seconds to download the model.

Or run the automated validation script:

```bash
./test-caching.sh
```

## Related Documentation

- [.github-workflows-example.yml](.github-workflows-example.yml) - Example CI/CD workflows with caching
- [docker-compose.dev-cache.yml](docker-compose.dev-cache.yml) - Development setup with volume caching
- [README.md](README.md) - Main project documentation
