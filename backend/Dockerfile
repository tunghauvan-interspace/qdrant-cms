# Build stage - for building packages that need compilation
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
# Remove --no-cache-dir to enable pip caching for faster rebuilds
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Pre-download sentence-transformers model to cache it in the image
# This prevents downloading the model on every container start
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-MiniLM-L3-v2')"

# Runtime stage - smaller final image
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy pre-downloaded sentence-transformers models from builder
COPY --from=builder /root/.cache/torch /root/.cache/torch

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Set sentence-transformers cache directory
ENV SENTENCE_TRANSFORMERS_HOME=/root/.cache/torch/sentence_transformers

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /home/appuser/.cache/torch && \
    cp -r /root/.cache/torch/. /home/appuser/.cache/torch/ 2>/dev/null || true && \
    chown -R appuser:appuser /home/appuser/.cache

USER appuser

# Set cache directory for non-root user
ENV SENTENCE_TRANSFORMERS_HOME=/home/appuser/.cache/torch/sentence_transformers

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
