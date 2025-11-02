# Semantic Clustering & Topic Detection

## Overview

The semantic clustering feature enables automatic grouping of documents by topic or semantic similarity, helping users discover knowledge, explore themes, and find similar documents in large repositories.

## Features

- **Multiple Clustering Algorithms**
  - K-Means: Fixed number of clusters
  - HDBSCAN: Density-based clustering with automatic cluster detection

- **Dimensionality Reduction**
  - UMAP: Fast, scalable visualization
  - t-SNE: High-quality visualization for smaller datasets

- **Two Clustering Levels**
  - Document-level: Groups entire documents by their average embeddings
  - Chunk-level: Groups text chunks for fine-grained topic detection

- **Interactive Visualization**
  - Scatter plot with color-coded clusters
  - Hover tooltips with document information
  - Click to drill down into cluster details

- **Cluster Analysis**
  - Automatic keyword extraction
  - Representative documents per cluster
  - Cluster size and statistics

## Usage

### Accessing the Clusters Page

1. Log in to the Qdrant CMS dashboard
2. Click on "Clusters" in the sidebar navigation
3. Configure clustering parameters
4. Click "Generate Clusters" to visualize your documents

### Configuration Options

#### Algorithm Selection

**K-Means**
- Best for: When you know how many topics you expect
- Parameters:
  - Number of Clusters: 2-20 (default: 5)
- Produces: Exactly the specified number of clusters

**HDBSCAN**
- Best for: Discovering topics automatically
- Parameters:
  - Min Cluster Size: 2-50 (default: 5)
- Produces: Variable number of clusters based on density

#### Visualization Method

**UMAP (Recommended)**
- Faster computation
- Better for larger datasets (>100 documents)
- Preserves both local and global structure

**t-SNE**
- Better for smaller datasets (<100 documents)
- High-quality visualization
- Slower computation

#### Clustering Level

**Document Level**
- Groups entire documents together
- Best for: Finding similar documents
- Faster computation

**Chunk Level**
- Groups text chunks across documents
- Best for: Finding specific topics and themes
- More detailed but slower

## API Reference

### Generate Clusters

```
POST /api/clustering/generate
```

**Request Body:**
```json
{
  "algorithm": "kmeans",
  "n_clusters": 5,
  "reduction_method": "umap",
  "level": "document"
}
```

**Response:**
```json
{
  "points": [
    {
      "id": "1",
      "x": -2.5,
      "y": 3.2,
      "cluster_id": 0,
      "document_id": 1,
      "filename": "example.pdf",
      "description": "Example document"
    }
  ],
  "summaries": [
    {
      "cluster_id": 0,
      "size": 5,
      "representative_docs": [
        {
          "document_id": 1,
          "filename": "example.pdf",
          "description": "Example document",
          "count": 1
        }
      ],
      "keywords": ["example", "topic", "document"]
    }
  ],
  "algorithm": "kmeans",
  "n_clusters": 5,
  "reduction_method": "umap",
  "level": "document"
}
```

### Get Cluster Statistics

```
GET /api/clustering/stats
```

**Response:**
```json
{
  "message": "Generate clusters to see statistics",
  "available_algorithms": ["kmeans", "hdbscan"],
  "available_reduction_methods": ["umap", "tsne"],
  "available_levels": ["document", "chunk"]
}
```

## Use Cases

### Knowledge Discovery
- Explore large document collections by topic
- Identify themes and patterns in your corpus
- Find related documents across different categories

### Gap Analysis
- Detect underrepresented topics
- Identify areas lacking documentation
- Discover emerging themes

### Content Organization
- Auto-categorize documents
- Suggest tags based on clusters
- Improve search and navigation

## Best Practices

1. **Start with Document-level clustering** for faster results and overview
2. **Use K-Means with 5-10 clusters** for initial exploration
3. **Switch to HDBSCAN** if you don't know the optimal number of clusters
4. **Use Chunk-level** for detailed topic analysis within documents
5. **UMAP is generally faster** and works well for most cases
6. **Upload diverse documents** (at least 10-20) for meaningful clusters

## Accessibility Features

- **Color-blind friendly palette**: Using Okabe-Ito color scheme
- **Keyboard navigation**: Tab through cluster summaries
- **Screen reader support**: ARIA labels on interactive elements
- **Responsive design**: Works on mobile and desktop

## Performance Considerations

- **Small datasets (<50 documents)**: All methods work well
- **Medium datasets (50-500 documents)**: Use UMAP, document-level preferred
- **Large datasets (>500 documents)**: Use UMAP with document-level only
- **Chunk-level clustering**: Can be slow with many documents (>100)

## Troubleshooting

### "No documents available for clustering"
- Upload some documents first
- Ensure documents are processed and have embeddings

### Clusters overlap or look unclear
- Try different reduction methods (UMAP vs t-SNE)
- Adjust number of clusters (K-Means)
- Try document-level instead of chunk-level

### Clustering takes too long
- Use document-level instead of chunk-level
- Use UMAP instead of t-SNE
- Reduce number of documents being clustered

## Technical Details

### Embedding Models
- Default: `all-MiniLM-L6-v2` (384 dimensions)
- Document embeddings: Average of chunk embeddings
- Distance metric: Cosine similarity

### Algorithms
- **K-Means**: Standard implementation from scikit-learn
- **HDBSCAN**: Hierarchical density-based clustering
- **UMAP**: Uniform Manifold Approximation and Projection
- **t-SNE**: t-distributed Stochastic Neighbor Embedding

### Keyword Extraction
- Simple frequency-based extraction
- Filters common stop words
- Extracts up to 5 keywords per cluster

## Future Enhancements

- Cluster data export (CSV, JSON)
- Save and load cluster configurations
- Cluster-based document recommendations
- Temporal clustering (track topic evolution over time)
- Multi-language support for keywords
- Advanced keyword extraction (TF-IDF, TextRank)
