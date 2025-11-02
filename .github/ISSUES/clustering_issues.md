

# Clustering — full picture & design sketch

This document sketches a complete design for persistent, incremental, and high-quality clustering in Qdrant CMS. It aggregates previous notes and turns them into a single implementation-ready picture: data model, APIs, incremental update strategies, metrics/drift detection, frontend UX, and a prioritized roadmap.

**Research Notes:** This document has been enhanced with comprehensive research on clustering algorithms, best practices from scikit-learn, HDBSCAN, UMAP/t-SNE, and MiniBatchKMeans implementations. All research conducted on November 2, 2025.

## Goals

- Persist cluster runs so results are authoritative and shareable.
- Allow fast, on-arrival assignment of new documents to clusters (good UX).
- Maintain quality by periodically re-clustering the corpus and regenerating topics/keywords.
- Make clustering scalable, observable, and safe (limits, sampling, rate-limiting).

## Current Implementation Analysis

**Existing Features** (based on `clustering_service.py`):
- Document-level and chunk-level clustering
- KMeans algorithm with configurable n_clusters
- HDBSCAN support (optional dependency)
- UMAP and t-SNE dimensionality reduction for visualization
- Keyword extraction from clusters (with Vietnamese + English stop words)
- Cluster summaries with representative documents
- Integration with Qdrant vector storage

**Limitations**:
- No persistence of cluster runs (ephemeral results)
- No incremental assignment mechanism
- No drift detection or quality metrics
- No centroid storage for fast lookup
- Single-shot clustering only (no updates)
- Memory-intensive for large datasets

## Core concepts

- **ClusterRun**: a persisted clustering job (parameters, status, result snapshot).
- **Centroids / representatives**: cluster-level vectors for fast assignment.
- **Assignment policy**: rules/thresholds to assign new documents to existing clusters.
- **Re-cluster job**: full or sampled recomputation that creates a new `ClusterRun`.
- **Metrics & drift detection**: silhouette, unassigned rate, cluster size distribution.

## Clustering Algorithm Deep Dive

### KMeans vs HDBSCAN Comparison

**KMeans** (scikit-learn):
- **Strengths**:
  - Fast, scalable (O(n*k*i) where n=samples, k=clusters, i=iterations)
  - Good for convex, isotropic clusters of similar size
  - Inductive: can easily assign new points to existing clusters
  - Well-understood, deterministic with k-means++ initialization
  - Supports partial_fit() via MiniBatchKMeans for incremental updates
- **Weaknesses**:
  - Requires specifying k (number of clusters) upfront
  - Assumes spherical clusters with equal variance
  - Sensitive to outliers and noise
  - Poor with elongated or irregularly shaped clusters
  - High-dimensional curse: Euclidean distances become less meaningful
- **Parameters**:
  - `n_clusters`: 3-20 typical for document clustering
  - `init='k-means++'`: Best initialization (better than random)
  - `n_init=10`: Multiple runs to avoid local minima
  - `max_iter=300`: Sufficient for convergence
- **Best for**: Exploratory clustering, balanced cluster sizes, when k is known

**HDBSCAN** (Hierarchical Density-Based Spatial Clustering):
- **Strengths**:
  - Automatically finds number of clusters
  - Handles variable density clusters
  - Robust outlier detection (noise points = -1 label)
  - Works with non-spherical, irregular cluster shapes
  - Provides cluster hierarchy and stability scores
  - No need to specify k
- **Weaknesses**:
  - Transductive: harder to assign new points (not inductive)
  - More computationally expensive: O(n log n) with optimized MST
  - Memory intensive (stores mutual reachability distances)
  - Less intuitive parameters
  - Assignment to existing clusters requires custom logic
- **Parameters**:
  - `min_cluster_size=5-50`: Minimum points for valid cluster
  - `min_samples=None`: Defaults to min_cluster_size (conservative)
  - `metric='euclidean'`: Or 'cosine' for text embeddings
  - `cluster_selection_method='eom'`: Extract stable clusters
- **Best for**: Unknown cluster count, outlier removal, hierarchical structure

**Algorithm Selection Guidelines**:
- Use KMeans when: Fast iteration needed, cluster count known, balanced sizes expected
- Use HDBSCAN when: Cluster count unknown, outliers present, hierarchical insights needed
- Hybrid approach: HDBSCAN for initial exploration → KMeans for production with known k

### Dimensionality Reduction: UMAP vs t-SNE

**UMAP** (Uniform Manifold Approximation and Projection):
- **Strengths**:
  - Preserves global structure better than t-SNE
  - Faster (especially for large datasets): O(n log n)
  - Supports transform() for new data (inductive)
  - Better for downstream clustering
  - Theoretically grounded (topological data analysis)
  - Scales to millions of points
- **Weaknesses**:
  - More parameters to tune
  - Can create false connections at boundaries
  - Requires understanding of manifold assumptions
- **Parameters**:
  - `n_neighbors=15`: Local neighborhood size (5-50 range)
  - `min_dist=0.1`: Minimum distance in embedding (0.0-0.99)
  - `n_components=2`: Typically 2 for visualization, 50 for preprocessing
  - `metric='cosine'`: For text/document embeddings
- **Best for**: Large datasets, preserving global structure, preprocessing for clustering

**t-SNE** (t-Distributed Stochastic Neighbor Embedding):
- **Strengths**:
  - Excellent local structure preservation
  - Beautiful, intuitive visualizations
  - Well-established, widely used
  - Good for final visualization
- **Weaknesses**:
  - Slow: O(n²) naive, O(n log n) with Barnes-Hut
  - Non-deterministic (random initialization)
  - Transductive: cannot transform new points
  - Distance/size interpretations unreliable
  - Sensitive to perplexity parameter
  - Not suitable for clustering (only visualization)
- **Parameters**:
  - `perplexity=30`: Balance local/global (5-50 typical)
  - `learning_rate='auto'`: max(N/early_exaggeration/4, 50)
  - `n_iter=1000`: Minimum 250, more for convergence
  - `init='pca'`: More stable than random
  - `method='barnes_hut'`: For n>1000 samples
- **Best for**: Final visualization only, NOT for preprocessing

**Recommendation for Production**:
1. **Preprocessing**: PCA to 50 dims if original dims > 100 (speeds up clustering)
2. **Clustering**: UMAP to 2D/3D for visualization, keep high-dim for actual clustering
3. **Visualization**: Use UMAP results directly (no need for t-SNE unless special needs)

## Data model (ClusterRun)

Example fields:

- id: UUID primary key
- owner_id: FK to user
- name: text (human-friendly)
- slug: url-safe unique slug
- params: json (algorithm, n_clusters, reduction_method, level, thresholds)
- status: enum {pending, running, completed, failed}
- created_at, started_at, finished_at
- result: json (points, summaries) or pointer to stored JSON file
- summaries: array of { cluster_id, size, centroid (list[float]), keywords_preview }
- n_points, n_clusters
- metrics: json (silhouette, db_index, unassigned_rate)

Notes:
- Store centroids (float32 arrays) inside the JSON or as separate table for efficient updates.
- Add unique index on slug.

## API surface (recommended)

- POST /api/clustering/generate
	- body: ClusterRequest (params)
	- response: { cluster_id, name, slug, status }
	- action: create ClusterRun (status=pending) and enqueue job

- GET /api/clustering/{cluster_id}
	- response: ClusterRun metadata + status + partial result (if completed)

- GET /api/clustering/{cluster_id}/result
	- response: ClusterResult (points + summaries), supports pagination if needed

- POST /api/clustering/{cluster_id}/assign (or /api/clustering/assign)
	- body: { document_id } or embedding
	- response: assigned cluster_id or { unassigned: true }
	- action: embed document, ANN lookup against cluster centroids/representatives, assign if within threshold and update centroid

- POST /api/clustering/search
	- body: { cluster_id, query, limit }
	- response: list of matched points/documents (server-side uses stored cluster_result)

- GET /api/clustering (list runs)
- PATCH /api/clustering/{cluster_id}/rename

## Incremental assignment (on new document arrival)

### Strategy Overview

1. Compute embedding for new document or chunk.
2. Query cluster centroids/representatives via Qdrant ANN (or in-memory if centroid count small).
3. If nearest distance < T_assign: assign to that cluster and update centroid incrementally: C_new = (n*C + x) / (n+1).
4. Else: mark as unassigned (pool) or create a candidate cluster (depends on policy).

### MiniBatchKMeans: Production-Ready Incremental Clustering

**Why MiniBatchKMeans is Ideal**:
- **Native incremental learning**: `partial_fit()` method for online updates
- **Memory efficient**: Processes mini-batches instead of full dataset
- **Fast convergence**: 3-5x faster than standard KMeans with minimal quality loss
- **Streaming support**: Can handle continuous data streams
- **Scalability**: Works well with millions of samples

**Implementation Pattern**:
```python
from sklearn.cluster import MiniBatchKMeans

# Initialize with existing centroids (from ClusterRun)
clusterer = MiniBatchKMeans(
    n_clusters=5,
    batch_size=256,  # Optimize: 256 * n_cores for parallelism
    init=existing_centroids,  # Load from ClusterRun.summaries[i].centroid
    n_init=1,  # Skip re-initialization
    reassignment_ratio=0.01,  # Prevent empty clusters
    random_state=42
)

# Incremental update on new documents
new_embeddings = [embed(doc) for doc in new_docs]
clusterer.partial_fit(np.array(new_embeddings))

# Get updated centroids
updated_centroids = clusterer.cluster_centers_
# Store back to ClusterRun
```

**Centroid Update Mathematics**:
- **Streaming mean formula**: `C_new = (n * C_old + x) / (n + 1)`
- **Exponentially weighted average** (MiniBatch): `C_new = C_old + η * (x - C_old)`
  - where η (learning_rate) = 1 / (samples_seen + 1)
- **Per-cluster tracking**: Maintain `cluster_sizes` to weight updates properly

**Assignment Threshold Guidelines**:
```python
# Distance-based threshold
T_assign = 0.7 * avg_intra_cluster_distance  # 70% of typical intra-cluster distance

# Silhouette-inspired threshold
# Assign if: distance_to_nearest < 0.5 * (distance_to_nearest + distance_to_second_nearest)

# Percentile-based threshold (more robust)
T_assign = np.percentile(intra_cluster_distances, 75)  # 75th percentile
```

### Implementation Notes

**Batching Strategy**:
- Accumulate 50-100 new documents before calling `partial_fit()`
- Update centroids in database transaction after batch processing
- Use Redis/message queue for high-throughput scenarios

**Concurrency Considerations**:
- Lock cluster run during centroid updates (row-level lock in PostgreSQL/SQLite)
- Use optimistic locking with version counter
- Consider event-sourcing pattern for audit trail

**Quality vs Speed Tradeoffs**:
| Approach | Speed | Quality | Use Case |
|----------|-------|---------|----------|
| partial_fit every doc | Slow | High | Real-time critical |
| Batch 100 docs | Medium | High | Balanced |
| Batch 1000 docs | Fast | Medium | High throughput |
| Daily re-cluster | Slow | Highest | Non-realtime |

**HDBSCAN Assignment (Custom Logic)**:
```python
# For HDBSCAN, use approximate nearest neighbors
def assign_to_hdbscan_cluster(new_embedding, cluster_run):
    # Find k nearest neighbors from each cluster
    neighbors = qdrant_client.search(
        collection_name="cluster_representatives",
        query_vector=new_embedding,
        limit=10
    )
    
    # Vote by cluster membership of neighbors
    cluster_votes = Counter([n.payload['cluster_id'] for n in neighbors])
    
    if max(cluster_votes.values()) >= 5:  # Threshold: 5/10 neighbors agree
        return cluster_votes.most_common(1)[0][0]
    else:
        return -1  # Noise/unassigned
```

**Drift Detection via Assignment Rate**:
- Track `unassigned_rate = unassigned_count / total_new_docs`
- Trigger re-clustering if `unassigned_rate > 0.3` (>30% can't be assigned)

## Periodic re-clustering

When to run:

- **Time based**: e.g., nightly or weekly.
- **Volume based**: after X new docs (e.g., max(100, 5% of corpus)).
- **Drift based**: when metrics (silhouette, unassigned_rate) cross thresholds.

What it does:

- Pull embeddings (from Qdrant or DB), optionally sample if huge.
- Optionally PCA to 50 dims, then cluster (kmeans/hdbscan) and reduce to 2d for visualization (UMAP/TSNE).
- Generate `ClusterRun` result and metrics; persist and publish new run id.
- Optionally compute mapping from previous clusters to new clusters for lineage analysis.

### Re-clustering Triggers (Research-Based)

**1. Volume-Based Triggers**:
```python
# Absolute threshold
if new_docs_since_last_cluster > 100:
    trigger_recluster()

# Percentage threshold (more scalable)
if new_docs_since_last_cluster / total_docs > 0.05:  # 5% corpus change
    trigger_recluster()

# Hybrid approach
trigger_threshold = max(100, 0.05 * total_docs, 0.1 * avg_cluster_size)
```

**2. Drift-Based Triggers** (Most Sophisticated):
```python
# Silhouette score degradation
if current_silhouette < (baseline_silhouette - 0.15):  # 15% drop
    trigger_recluster()

# High unassigned rate
if unassigned_rate_7day_avg > 0.30:  # 30% can't assign
    trigger_recluster()

# Cluster size imbalance (Coefficient of Variation)
cluster_sizes = [c.size for c in clusters]
cv = np.std(cluster_sizes) / np.mean(cluster_sizes)
if cv > 1.5:  # High variability
    trigger_recluster()
```

**3. Time-Based Triggers**:
- **Real-time systems**: Every 6-12 hours
- **Document management**: Daily or weekly
- **Archival systems**: Monthly

### Sampling Strategy for Large Datasets

When `n_samples > 50,000`:

**Stratified Sampling** (Recommended):
```python
def stratified_sample(documents, target_size=50000):
    # Sample proportionally from each existing cluster
    samples = []
    for cluster_id in unique_clusters:
        cluster_docs = documents[documents.cluster_id == cluster_id]
        n_samples = int(target_size * len(cluster_docs) / len(documents))
        samples.extend(cluster_docs.sample(n_samples))
    
    # Add random sample from unassigned
    unassigned = documents[documents.cluster_id == -1]
    samples.extend(unassigned.sample(min(5000, len(unassigned))))
    return samples
```

**Reservoir Sampling** (For streaming):
```python
def reservoir_sample(stream, k=50000):
    reservoir = []
    for i, item in enumerate(stream):
        if i < k:
            reservoir.append(item)
        else:
            j = random.randint(0, i)
            if j < k:
                reservoir[j] = item
    return reservoir
```

**Sampling Quality Metrics**:
- Mark ClusterRun as `is_sampled=True` in metadata
- Store `sampling_ratio` and `sampling_method`
- Validate: `sampled_silhouette_score > 0.9 * full_silhouette_score`

### Cluster Lineage & Evolution Tracking

**Mapping Old → New Clusters**:
```python
def compute_cluster_mapping(old_clusters, new_clusters):
    """
    Compute best mapping from old cluster IDs to new cluster IDs
    using Hungarian algorithm or simple majority vote
    """
    mapping = {}
    for old_id in old_clusters.unique():
        old_docs = old_clusters[old_clusters == old_id].index
        new_assignments = new_clusters[old_docs]
        # Majority vote
        mapping[old_id] = new_assignments.mode()[0]
    return mapping

# Detect splits and merges
splits = [old_id for old_id in mapping if mapping.values().count(mapping[old_id]) == 1]
merges = [new_id for new_id in mapping.values() if list(mapping.values()).count(new_id) > 1]
```

**Visualization of Cluster Evolution**:
- Sankey diagram showing cluster flow old → new
- Highlight split/merge events
- Track cluster "lifespan" across multiple runs

## Drift detection & metrics

Track per-run metrics:

- **silhouette score** (when applicable): Range [-1, 1], higher is better (>0.5 good, >0.7 excellent)
- **Davies-Bouldin index**: Lower is better, 0 is perfect (typically 0.5-2.0 range)
- **Calinski-Harabasz index** (Variance Ratio Criterion): Higher is better
- **unassigned/noise rate** (fraction of points not assigned during incremental assignment)
- **cluster size distribution**: coefficient of variation, Gini coefficient
- **inertia** (for KMeans): Within-cluster sum of squares

Trigger re-cluster when:

- silhouette drops by > delta (e.g., 0.15)
- unassigned_rate > threshold (e.g., 0.30)
- new_docs_count > threshold (e.g., 5% of corpus)

### Comprehensive Metrics Guide

#### 1. Silhouette Coefficient (Best for Interpretation)

**Formula**: For each sample i:
- a(i) = mean distance to samples in same cluster
- b(i) = mean distance to samples in nearest other cluster
- s(i) = (b(i) - a(i)) / max(a(i), b(i))
- Overall score = mean of all s(i)

**Interpretation**:
- `1.0`: Perfect separation (dense, well-separated clusters)
- `0.5-0.7`: Good clustering
- `0.25-0.5`: Weak structure, overlapping clusters
- `0.0`: Overlapping clusters
- `<0`: Misclassified samples

**Advantages**:
- Intuitive interpretation
- No need for ground truth
- Per-sample scores available (find misclassified points)
- Works with any distance metric

**Disadvantages**:
- O(n²) complexity - expensive for large datasets
- Biased toward convex clusters
- Not suitable for density-based clusters (DBSCAN/HDBSCAN)

**Usage**:
```python
from sklearn.metrics import silhouette_score, silhouette_samples

# Overall score
score = silhouette_score(embeddings, labels, metric='euclidean')

# Per-sample scores (find outliers)
sample_scores = silhouette_samples(embeddings, labels)
outliers = np.where(sample_scores < 0)[0]  # Likely misclassified
```

**Thresholds**:
- Alert if `score < 0.3` (poor clustering)
- Trigger re-cluster if `score drops > 0.15` from baseline

#### 2. Davies-Bouldin Index (Fast Alternative)

**Formula**: 
- DB = (1/k) * Σ max(R_ij) for i≠j
- R_ij = (S_i + S_j) / M_ij
- S_i = avg distance within cluster i
- M_ij = distance between cluster centroids

**Interpretation**:
- `0.0`: Perfect (minimum)
- `<1.0`: Excellent separation
- `1.0-2.0`: Good clustering
- `>2.0`: Poor separation

**Advantages**:
- Fast: O(n) after centroids computed
- Simple to understand
- Good for KMeans validation

**Disadvantages**:
- Requires centroids (not suitable for HDBSCAN)
- Euclidean space only
- Less intuitive than silhouette

**Usage**:
```python
from sklearn.metrics import davies_bouldin_score

db_score = davies_bouldin_score(embeddings, labels)
# Lower is better
```

#### 3. Calinski-Harabasz Index (Variance Ratio Criterion)

**Formula**:
- CH = [SSB / (k-1)] / [SSW / (n-k)]
- SSB = between-cluster dispersion
- SSW = within-cluster dispersion

**Interpretation**:
- Higher = better
- Typical range: 100-10,000+ (dataset dependent)
- Use for comparing different k values

**Advantages**:
- Very fast to compute
- Higher scores = better defined clusters
- Good for elbow method (finding optimal k)

**Disadvantages**:
- Not bounded (hard to interpret absolute values)
- Favors convex, balanced clusters

**Usage**:
```python
from sklearn.metrics import calinski_harabasz_score

ch_score = calinski_harabasz_score(embeddings, labels)
# Compare across different n_clusters
```

#### 4. Inertia (KMeans specific)

**Formula**: Σ min(||x - μ_j||²) for all points x

**Interpretation**:
- Lower = more compact clusters
- Use elbow method to find optimal k

**Advantages**:
- Built-in to KMeans
- Fast (computed during clustering)

**Disadvantages**:
- Always decreases with more clusters
- Not normalized
- Only for KMeans

#### 5. Custom Metrics for Document Clustering

**Cluster Coherence** (Topic Quality):
```python
def cluster_topic_coherence(cluster_docs, top_keywords):
    """
    Measure how well keywords represent cluster documents
    Using cosine similarity between keyword embeddings and doc embeddings
    """
    keyword_embedding = np.mean([embed(word) for word in top_keywords], axis=0)
    doc_embeddings = [embed(doc) for doc in cluster_docs]
    coherence = np.mean([cosine_similarity(keyword_embedding, doc) 
                         for doc in doc_embeddings])
    return coherence
```

**Cluster Purity** (if labels available):
```python
def cluster_purity(true_labels, pred_labels):
    """
    Fraction of cluster members belonging to dominant true class
    """
    contingency_matrix = np.zeros((n_clusters, n_classes))
    for pred, true in zip(pred_labels, true_labels):
        contingency_matrix[pred, true] += 1
    return np.sum(np.max(contingency_matrix, axis=1)) / len(true_labels)
```

**Cluster Stability** (across re-runs):
```python
def cluster_stability(run1_labels, run2_labels):
    """
    Adjusted Rand Index: measures agreement between two clusterings
    """
    from sklearn.metrics import adjusted_rand_score
    return adjusted_rand_score(run1_labels, run2_labels)
```

### Drift Detection System

**Multi-Signal Approach**:
```python
class ClusterDriftDetector:
    def __init__(self, baseline_metrics):
        self.baseline = baseline_metrics
        self.alert_thresholds = {
            'silhouette_drop': 0.15,
            'unassigned_rate': 0.30,
            'new_docs_pct': 0.05,
            'cluster_imbalance': 1.5,  # CV threshold
        }
    
    def check_drift(self, current_metrics):
        alerts = []
        
        # Silhouette degradation
        if (self.baseline['silhouette'] - current_metrics['silhouette']) > \
           self.alert_thresholds['silhouette_drop']:
            alerts.append('silhouette_degradation')
        
        # High unassigned rate
        if current_metrics['unassigned_rate'] > self.alert_thresholds['unassigned_rate']:
            alerts.append('high_unassigned_rate')
        
        # Volume growth
        if current_metrics['new_docs_pct'] > self.alert_thresholds['new_docs_pct']:
            alerts.append('corpus_growth')
        
        # Cluster imbalance
        cv = self.compute_cluster_cv(current_metrics['cluster_sizes'])
        if cv > self.alert_thresholds['cluster_imbalance']:
            alerts.append('cluster_imbalance')
        
        return alerts
    
    def compute_cluster_cv(self, sizes):
        return np.std(sizes) / np.mean(sizes) if np.mean(sizes) > 0 else 0
```

**Monitoring Dashboard Metrics**:
- 7-day rolling average of silhouette score (line chart)
- Unassigned rate per day (bar chart)
- Cluster size distribution over time (stacked area chart)
- Alert timeline (event markers)

### Optimal Number of Clusters (k)

**Elbow Method**:
```python
def find_optimal_k(embeddings, k_range=range(2, 20)):
    inertias = []
    silhouettes = []
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42)
        labels = kmeans.fit_predict(embeddings)
        inertias.append(kmeans.inertia_)
        silhouettes.append(silhouette_score(embeddings, labels))
    
    # Find elbow using derivative
    kneedle = KneeLocator(k_range, inertias, curve='convex', direction='decreasing')
    optimal_k_inertia = kneedle.knee
    
    # Find peak silhouette
    optimal_k_silhouette = k_range[np.argmax(silhouettes)]
    
    return optimal_k_inertia, optimal_k_silhouette, (inertias, silhouettes)
```

**Gap Statistic** (Most Rigorous):
- Compare inertia with random data
- Select k where gap is maximized
- Computationally expensive but robust

## Storage & Qdrant interactions

- Store document chunk embeddings as points in Qdrant with payload including `document_id`, `chunk_index`, and optionally `cluster_id` and `cluster_run_id`.
- Optionally create a separate Qdrant collection for cluster centroids (each centroid stored as a point with payload {cluster_id, cluster_run_id}). This enables ANN retrieval of nearest cluster.
- When re-clustering, you may either rebuild centroid collection or upsert centroid points.

### Qdrant Schema Design

**Main Collection** (`documents`):
```python
{
    "id": "chunk_{document_id}_{chunk_index}",  # UUID string
    "vector": [0.1, 0.2, ...],  # 384-dim for all-MiniLM-L6-v2
    "payload": {
        "document_id": 123,
        "chunk_index": 0,
        "chunk_content": "...",
        "cluster_id": 2,  # Optional: current cluster assignment
        "cluster_run_id": "run_abc123",  # Optional: which run assigned this
        "last_updated": "2025-11-02T10:30:00Z"
    }
}
```

**Centroid Collection** (`cluster_centroids`):
```python
{
    "id": "centroid_{cluster_run_id}_{cluster_id}",
    "vector": [0.15, 0.22, ...],  # Computed centroid
    "payload": {
        "cluster_run_id": "run_abc123",
        "cluster_id": 2,
        "cluster_size": 150,
        "created_at": "2025-11-02T10:00:00Z",
        "keywords": ["machine", "learning", "model"],
        "representative_docs": [123, 456, 789]  # Top-3 closest to centroid
    }
}
```

### Qdrant Operations

**1. Fast Cluster Assignment** (ANN Search):
```python
def assign_to_cluster(new_embedding, cluster_run_id):
    # Search in centroid collection
    results = qdrant_client.search(
        collection_name="cluster_centroids",
        query_vector=new_embedding,
        query_filter={
            "must": [
                {"key": "cluster_run_id", "match": {"value": cluster_run_id}}
            ]
        },
        limit=2  # Get top 2 for confidence check
    )
    
    if not results:
        return -1  # No clusters found
    
    # Check assignment confidence
    nearest = results[0]
    if len(results) > 1:
        second_nearest = results[1]
        # Assign if nearest is significantly closer (>20% difference)
        if nearest.score / second_nearest.score > 1.2:
            return nearest.payload['cluster_id']
    else:
        # Single cluster or very confident
        if nearest.score > 0.7:  # Cosine similarity threshold
            return nearest.payload['cluster_id']
    
    return -1  # Unassigned / low confidence
```

**2. Batch Centroid Update**:
```python
def update_centroids_in_qdrant(cluster_run_id, new_centroids):
    """
    Efficiently update multiple centroids after incremental assignment
    """
    points = []
    for cluster_id, centroid_data in new_centroids.items():
        points.append({
            "id": f"centroid_{cluster_run_id}_{cluster_id}",
            "vector": centroid_data['vector'].tolist(),
            "payload": {
                "cluster_run_id": cluster_run_id,
                "cluster_id": cluster_id,
                "cluster_size": centroid_data['size'],
                "last_updated": datetime.utcnow().isoformat()
            }
        })
    
    # Upsert in batch (efficient)
    qdrant_client.upsert(
        collection_name="cluster_centroids",
        points=points
    )
```

**3. Bulk Document Cluster Assignment**:
```python
def bulk_assign_clusters(documents, cluster_run_id):
    """
    Assign multiple documents efficiently using batch search
    """
    # Extract embeddings from Qdrant
    doc_ids = [d['id'] for d in documents]
    points = qdrant_client.retrieve(
        collection_name="documents",
        ids=doc_ids,
        with_vectors=True
    )
    
    # Batch search against centroids
    assignments = []
    for point in points:
        cluster_id = assign_to_cluster(point.vector, cluster_run_id)
        assignments.append({
            'document_id': point.payload['document_id'],
            'cluster_id': cluster_id
        })
    
    # Update payloads in batch
    qdrant_client.set_payload(
        collection_name="documents",
        payload={"cluster_id": cluster_id, "cluster_run_id": cluster_run_id},
        points=[a['document_id'] for a in assignments if a['cluster_id'] != -1]
    )
    
    return assignments
```

### Qdrant Performance Optimizations

**1. Index Configuration**:
```python
# When creating collection
qdrant_client.create_collection(
    collection_name="cluster_centroids",
    vectors_config={
        "size": 384,
        "distance": "Cosine"  # Best for normalized embeddings
    },
    hnsw_config={
        "m": 16,  # Number of edges per node (balance speed/quality)
        "ef_construct": 100,  # Quality during indexing
    },
    optimizers_config={
        "indexing_threshold": 10000,  # When to trigger indexing
    }
)

# For search
search_params = {
    "hnsw_ef": 128,  # Higher = more accurate but slower
    "exact": False   # Use ANN, not exact search
}
```

**2. Payload Indexing**:
```python
# Create indexes for fast filtering
qdrant_client.create_payload_index(
    collection_name="documents",
    field_name="cluster_run_id",
    field_schema="keyword"  # Exact match
)

qdrant_client.create_payload_index(
    collection_name="documents", 
    field_name="cluster_id",
    field_schema="integer"
)
```

**3. Memory vs Disk**:
- **Centroids**: Keep in memory (small, <10k clusters)
- **Documents**: On-disk with SSD recommended
- **Cache**: Use Qdrant's built-in MMAP for hot data

### Alternative: Faiss for Centroids

For even faster centroid search (<1ms) when >1000 clusters:

```python
import faiss

class FaissCentroidIndex:
    def __init__(self, dimension=384):
        self.dimension = dimension
        # Use IVF for very large # of clusters
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine after L2 norm)
        
    def add_centroids(self, centroids):
        # Normalize for cosine similarity
        faiss.normalize_L2(centroids)
        self.index.add(centroids)
    
    def search(self, query_vector, k=1):
        faiss.normalize_L2(query_vector.reshape(1, -1))
        distances, indices = self.index.search(query_vector.reshape(1, -1), k)
        return indices[0], distances[0]

# Usage
centroid_index = FaissCentroidIndex()
centroid_index.add_centroids(cluster_centroids_array)
cluster_id, distance = centroid_index.search(new_doc_embedding, k=1)
```

### Data Consistency Patterns

**Option 1: Qdrant as Source of Truth**
- Store `cluster_id` in Qdrant payload
- DB stores ClusterRun metadata only
- Pro: Fast queries, single source
- Con: Complex to query by cluster from DB

**Option 2: Hybrid (Recommended)**
- Qdrant: Vectors + temporary `cluster_id` cache
- DB: Authoritative cluster assignments in `document_clusters` table
- Sync: Update DB after Qdrant assignment, expire Qdrant cache weekly
- Pro: Best of both worlds
- Con: Synchronization complexity

**Option 3: DB as Source of Truth**
- Qdrant: Vectors only
- DB: All cluster assignments
- Qdrant payload: Read-only cache refreshed nightly
- Pro: Simple consistency
- Con: Two queries for cluster + similarity

## Frontend UX recommendations

- When user requests clustering: show a job id and progress, don't block UI.
- Display saved cluster runs in a list with name/created_at/metrics. Allow selecting run to visualize.
- Show live assignment status for newly uploaded docs (assigned/unassigned). Allow user to request re-cluster.
- Provide comparison view between two cluster runs (lineage, merge/split highlights).

## Implementation roadmap (prioritized)

### Phase 1: Persistence Foundation (Week 1)
1. **Add ClusterRun model** to `models.py`:
   ```python
   class ClusterRun(Base):
       __tablename__ = "cluster_runs"
       id = Column(String, primary_key=True)  # UUID
       owner_id = Column(Integer, ForeignKey('users.id'))
       name = Column(String, nullable=False)
       slug = Column(String, unique=True)
       algorithm = Column(String)  # kmeans, hdbscan
       params = Column(JSON)  # n_clusters, min_cluster_size, etc.
       status = Column(String)  # pending, running, completed, failed
       created_at = Column(DateTime, default=datetime.utcnow)
       started_at = Column(DateTime)
       finished_at = Column(DateTime)
       n_points = Column(Integer)
       n_clusters = Column(Integer)
       metrics = Column(JSON)  # silhouette, db_index, etc.
       is_sampled = Column(Boolean, default=False)
       sampling_ratio = Column(Float)
   ```

2. **Add ClusterSummary table** (one-to-many with ClusterRun):
   ```python
   class ClusterSummary(Base):
       __tablename__ = "cluster_summaries"
       id = Column(Integer, primary_key=True)
       cluster_run_id = Column(String, ForeignKey('cluster_runs.id'))
       cluster_id = Column(Integer)  # 0, 1, 2, ..., -1 for noise
       size = Column(Integer)
       centroid = Column(JSON)  # List[float] - 384 dims
       keywords = Column(JSON)  # List[str]
       representative_doc_ids = Column(JSON)  # List[int]
       intra_cluster_distance = Column(Float)
   ```

3. **Modify `POST /api/clustering/generate`**:
   - Create ClusterRun with status='pending'
   - Return `cluster_run_id` immediately
   - Queue background job (Celery/RQ or simple threading)

4. **Implement background worker**:
   - Use existing `clustering_service.generate_clusters()`
   - Add result persistence logic
   - Update ClusterRun status='completed' + metrics

### Phase 2: Retrieval & Visualization (Week 2)
5. **Add `GET /api/clustering/{cluster_run_id}` endpoint**:
   - Return ClusterRun metadata
   - Include status for polling

6. **Add `GET /api/clustering/{cluster_run_id}/result` endpoint**:
   - Return full ClusterResult (points + summaries)
   - Support pagination: `?limit=1000&offset=0`
   - Add filters: `?cluster_id=2` for single cluster

7. **Frontend integration**:
   - Job submission + progress polling UI
   - List saved cluster runs (table with name, date, n_clusters, metrics)
   - Visualization reuse existing scatter plot

### Phase 3: Centroid Storage & Fast Assignment (Week 3)
8. **Create Qdrant centroid collection**:
   ```python
   qdrant_client.create_collection(
       collection_name="cluster_centroids",
       vectors_config={"size": 384, "distance": "Cosine"}
   )
   ```

9. **Add centroid upsert logic** after clustering:
   ```python
   def store_centroids(cluster_run_id, summaries):
       points = [
           {
               "id": f"centroid_{cluster_run_id}_{s.cluster_id}",
               "vector": s.centroid,
               "payload": {
                   "cluster_run_id": cluster_run_id,
                   "cluster_id": s.cluster_id,
                   "size": s.size,
                   "keywords": s.keywords
               }
           }
           for s in summaries if s.cluster_id != -1
       ]
       qdrant_client.upsert(collection_name="cluster_centroids", points=points)
   ```

10. **Implement `POST /api/clustering/{cluster_run_id}/assign` endpoint**:
    - Input: `{document_id: 123}` or `{embedding: [...]}`
    - Fetch embedding from Qdrant if document_id provided
    - ANN search in centroids collection
    - Return `{cluster_id: 2, confidence: 0.87}`

11. **Add MiniBatchKMeans incremental update**:
    ```python
    def incremental_update_centroids(cluster_run_id, new_docs_batch):
        # Load existing centroids from DB
        summaries = get_cluster_summaries(cluster_run_id)
        centroids = np.array([s.centroid for s in summaries])
        
        # Initialize MiniBatchKMeans with existing centroids
        kmeans = MiniBatchKMeans(
            n_clusters=len(centroids),
            init=centroids,
            n_init=1,
            batch_size=256
        )
        
        # Partial fit on new batch
        new_embeddings = get_embeddings(new_docs_batch)
        kmeans.partial_fit(new_embeddings)
        
        # Update centroids in DB and Qdrant
        update_centroids(cluster_run_id, kmeans.cluster_centers_)
    ```

### Phase 4: Metrics & Drift Detection (Week 4)
12. **Add metrics computation** to clustering service:
    ```python
    def compute_cluster_metrics(embeddings, labels):
        from sklearn.metrics import (
            silhouette_score,
            davies_bouldin_score,
            calinski_harabasz_score
        )
        
        return {
            "silhouette_score": silhouette_score(embeddings, labels),
            "davies_bouldin_index": davies_bouldin_score(embeddings, labels),
            "calinski_harabasz_index": calinski_harabasz_score(embeddings, labels),
            "n_noise": np.sum(labels == -1),
            "cluster_sizes": [np.sum(labels == i) for i in range(max(labels)+1)]
        }
    ```

13. **Create ClusterMetric tracking table**:
    ```python
    class ClusterMetric(Base):
        __tablename__ = "cluster_metrics"
        id = Column(Integer, primary_key=True)
        cluster_run_id = Column(String, ForeignKey('cluster_runs.id'))
        timestamp = Column(DateTime, default=datetime.utcnow)
        metric_name = Column(String)  # silhouette, unassigned_rate, etc.
        value = Column(Float)
    ```

14. **Implement drift detector**:
    ```python
    class ClusterDriftMonitor:
        def check_and_alert(self, cluster_run_id):
            metrics = get_recent_metrics(cluster_run_id, days=7)
            baseline = get_baseline_metrics(cluster_run_id)
            
            alerts = []
            if metrics['silhouette'] < baseline['silhouette'] - 0.15:
                alerts.append('silhouette_degradation')
            if metrics['unassigned_rate'] > 0.30:
                alerts.append('high_unassigned_rate')
            
            if alerts:
                self.trigger_recluster(cluster_run_id, reason=alerts)
    ```

15. **Add `POST /api/clustering/{cluster_run_id}/recluster` endpoint**:
    - Validate permissions
    - Create new ClusterRun with incremented version
    - Compute cluster lineage mapping
    - Queue background job

### Phase 5: Advanced Features (Week 5+)
16. **Optimal k finder** (`GET /api/clustering/suggest-k`):
    - Run elbow method + silhouette analysis
    - Return recommended k with confidence scores

17. **Cluster comparison view**:
    - `GET /api/clustering/compare?run1=abc&run2=def`
    - Return cluster mapping, splits, merges
    - Adjusted Rand Index between runs

18. **Scheduled re-clustering**:
    - Cron job or Celery beat
    - Check drift conditions daily
    - Auto-trigger if needed

19. **Cluster export**:
    - `GET /api/clustering/{run_id}/export?format=csv`
    - Include document IDs, cluster assignments, keywords
    - Support JSON, CSV, Excel formats

20. **Advanced visualization**:
    - Cluster hierarchy dendrogram (for HDBSCAN)
    - Time series of cluster evolution
    - Interactive 3D scatter (three.js)

## Safety, validation and limits

- Enforce `MAX_CLUSTER_POINTS` config; if exceeded, sample and mark the run as sampled (include in metadata).
- Validate clustering params (n_clusters bounds, min_cluster_size bounds).
- Rate limit clustering generation per-user.

### Production Safety Guardrails

**1. Resource Limits**:
```python
# config.py
CLUSTERING_LIMITS = {
    "MAX_CLUSTER_POINTS": 100000,  # Sample if exceeded
    "MAX_CLUSTERS_KMEANS": 50,     # Prevent explosion
    "MIN_CLUSTERS": 2,
    "MAX_DIMENSIONS": 1024,        # Embedding dimension limit
    "MIN_CLUSTER_SIZE_HDBSCAN": 5,
    "MAX_CLUSTER_SIZE_HDBSCAN": 500,
    "TIMEOUT_SECONDS": 300,        # 5 min max
    "MAX_CONCURRENT_JOBS_PER_USER": 2
}

# Validation
def validate_cluster_request(request: ClusterRequest, corpus_size: int):
    if request.algorithm == "kmeans":
        if not (2 <= request.n_clusters <= CLUSTERING_LIMITS["MAX_CLUSTERS_KMEANS"]):
            raise ValueError(f"n_clusters must be between 2 and {MAX_CLUSTERS_KMEANS}")
        if request.n_clusters > corpus_size:
            raise ValueError("n_clusters cannot exceed corpus size")
    
    elif request.algorithm == "hdbscan":
        if not (5 <= request.min_cluster_size <= CLUSTERING_LIMITS["MAX_CLUSTER_SIZE_HDBSCAN"]):
            raise ValueError("min_cluster_size out of bounds")
    
    # Check corpus size
    if corpus_size > CLUSTERING_LIMITS["MAX_CLUSTER_POINTS"]:
        warnings.warn(f"Corpus size {corpus_size} exceeds limit. Sampling to {MAX_CLUSTER_POINTS}.")
```

**2. Sampling When Over Limit**:
```python
def safe_cluster_large_corpus(documents, request):
    if len(documents) > MAX_CLUSTER_POINTS:
        # Stratified sampling
        sampled_docs = stratified_sample(
            documents, 
            target_size=MAX_CLUSTER_POINTS
        )
        
        # Cluster on sample
        result = cluster_documents(sampled_docs, request)
        
        # Mark as sampled
        result.metadata['is_sampled'] = True
        result.metadata['sampling_ratio'] = len(sampled_docs) / len(documents)
        result.metadata['original_size'] = len(documents)
        
        # Optional: Assign non-sampled docs to clusters
        if request.assign_remaining:
            assign_remainder(result, documents - sampled_docs)
        
        return result
    else:
        return cluster_documents(documents, request)
```

**3. Rate Limiting**:
```python
from functools import wraps
import time
from collections import defaultdict

# In-memory rate limiter (use Redis for production)
rate_limit_store = defaultdict(list)

def rate_limit_clustering(max_requests=5, window_seconds=3600):
    """Allow max_requests clustering jobs per window_seconds per user"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request, current_user, *args, **kwargs):
            user_id = current_user.id
            now = time.time()
            
            # Clean old requests
            rate_limit_store[user_id] = [
                ts for ts in rate_limit_store[user_id] 
                if now - ts < window_seconds
            ]
            
            # Check limit
            if len(rate_limit_store[user_id]) >= max_requests:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Max {max_requests} clustering jobs per hour."
                )
            
            # Record request
            rate_limit_store[user_id].append(now)
            
            return await func(request, current_user, *args, **kwargs)
        return wrapper
    return decorator

# Usage
@router.post("/generate")
@rate_limit_clustering(max_requests=5, window_seconds=3600)
async def generate_clusters(request, current_user, db):
    ...
```

**4. Timeout Protection**:
```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds):
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Clustering exceeded {seconds}s timeout")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

# Usage
try:
    with timeout(CLUSTERING_LIMITS["TIMEOUT_SECONDS"]):
        result = clustering_service.generate_clusters(...)
except TimeoutError:
    # Mark run as failed
    update_cluster_run_status(run_id, status='failed', error='timeout')
```

**5. Concurrent Job Limits**:
```python
async def check_user_active_jobs(user_id, db):
    active_jobs = await db.execute(
        select(ClusterRun)
        .where(ClusterRun.owner_id == user_id)
        .where(ClusterRun.status.in_(['pending', 'running']))
    )
    count = len(active_jobs.scalars().all())
    
    if count >= CLUSTERING_LIMITS["MAX_CONCURRENT_JOBS_PER_USER"]:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum {MAX_CONCURRENT_JOBS_PER_USER} concurrent jobs allowed"
        )
```

**6. Memory Management**:
```python
def estimate_memory_usage(n_samples, n_features, algorithm):
    """
    Rough memory estimates:
    - KMeans: O(n * d + k * d)
    - HDBSCAN: O(n^2) for distance matrix (with optimization: O(n log n))
    - UMAP: O(n * d + n * k) where k is n_neighbors
    """
    bytes_per_float = 4  # float32
    
    if algorithm == "kmeans":
        # Data + centroids + labels
        memory_mb = (n_samples * n_features * bytes_per_float + 
                     50 * n_features * bytes_per_float +  # Max 50 clusters
                     n_samples * 4) / (1024 * 1024)
    elif algorithm == "hdbscan":
        # Approximation with optimizations
        memory_mb = (n_samples * n_features * bytes_per_float * 2) / (1024 * 1024)
    
    return memory_mb

# Before clustering
estimated_mb = estimate_memory_usage(len(documents), embedding_dim, algorithm)
if estimated_mb > 4096:  # 4GB limit
    raise ValueError(f"Estimated memory {estimated_mb:.0f}MB exceeds limit")
```

**7. Input Validation**:
```python
def validate_documents_for_clustering(documents, min_docs=10):
    if len(documents) < min_docs:
        raise ValueError(f"Need at least {min_docs} documents for clustering")
    
    # Check for empty documents
    empty_docs = [d for d in documents if not d.chunks]
    if len(empty_docs) > len(documents) * 0.5:
        raise ValueError("More than 50% of documents have no content")
    
    # Check embedding availability
    missing_embeddings = []
    for doc in documents[:100]:  # Sample check
        for chunk in doc.chunks:
            if not chunk.qdrant_point_id:
                missing_embeddings.append(doc.id)
                break
    
    if len(missing_embeddings) > 10:
        raise ValueError(f"Many documents missing embeddings: {missing_embeddings[:10]}")
```

**8. Graceful Degradation**:
```python
async def robust_clustering(request, documents):
    try:
        # Try optimal settings
        return await generate_clusters(request, documents)
    except MemoryError:
        # Fallback: Sample more aggressively
        logger.warning("MemoryError, sampling to 50k points")
        sampled = random.sample(documents, min(50000, len(documents)))
        return await generate_clusters(request, sampled)
    except TimeoutError:
        # Fallback: Use faster algorithm
        logger.warning("Timeout, switching to MiniBatchKMeans")
        request.algorithm = "minibatch_kmeans"
        request.batch_size = 1024
        return await generate_clusters(request, documents)
    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        # Return default clustering (all in one cluster)
        return create_default_clustering(documents)
```

**9. User Quota System**:
```python
class UserQuota(Base):
    __tablename__ = "user_quotas"
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    max_cluster_runs = Column(Integer, default=10)  # Total saved runs
    max_points_per_run = Column(Integer, default=50000)
    max_concurrent_jobs = Column(Integer, default=2)

def check_quota(user_id, db):
    quota = db.query(UserQuota).filter_by(user_id=user_id).first()
    if not quota:
        quota = UserQuota(user_id=user_id)  # Default quota
    
    # Check saved runs
    saved_runs = db.query(ClusterRun).filter_by(
        owner_id=user_id, 
        status='completed'
    ).count()
    
    if saved_runs >= quota.max_cluster_runs:
        raise HTTPException(
            status_code=403,
            detail=f"Quota exceeded: {saved_runs}/{quota.max_cluster_runs} saved runs"
        )
```

**10. Error Recovery**:
```python
# Store intermediate state for recovery
class ClusterRunCheckpoint(Base):
    __tablename__ = "cluster_run_checkpoints"
    id = Column(Integer, primary_key=True)
    cluster_run_id = Column(String, ForeignKey('cluster_runs.id'))
    step = Column(String)  # 'embedding_fetch', 'clustering', 'reduction', 'storage'
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# Resumable clustering
async def resumable_clustering(cluster_run_id, request, documents):
    checkpoints = load_checkpoints(cluster_run_id)
    
    if 'embeddings' not in checkpoints:
        embeddings = await fetch_embeddings(documents)
        save_checkpoint(cluster_run_id, 'embeddings', embeddings)
    else:
        embeddings = checkpoints['embeddings']
    
    if 'cluster_labels' not in checkpoints:
        labels = perform_clustering(embeddings, request)
        save_checkpoint(cluster_run_id, 'cluster_labels', labels)
    else:
        labels = checkpoints['cluster_labels']
    
    # ... continue with remaining steps
```

## Tests to add

### Unit Tests

**1. Clustering Algorithm Tests**:
```python
# tests/unit/test_clustering_service.py
import pytest
import numpy as np
from app.services.clustering_service import clustering_service

def test_kmeans_clustering():
    # Create synthetic data
    embeddings = np.random.randn(100, 384)
    labels = clustering_service._kmeans_clustering(embeddings, n_clusters=5)
    
    assert len(labels) == 100
    assert len(set(labels)) == 5
    assert all(0 <= label < 5 for label in labels)

def test_hdbscan_clustering():
    embeddings = np.random.randn(100, 384)
    labels = clustering_service._hdbscan_clustering(embeddings, min_cluster_size=5)
    
    assert len(labels) == 100
    assert -1 in labels  # Should have noise points

def test_umap_reduction():
    embeddings = np.random.randn(100, 384)
    reduced = clustering_service._umap_reduction(embeddings)
    
    assert reduced.shape == (100, 2)
    assert not np.any(np.isnan(reduced))

def test_tsne_reduction():
    embeddings = np.random.randn(100, 384)
    reduced = clustering_service._tsne_reduction(embeddings)
    
    assert reduced.shape == (100, 2)
```

**2. Centroid Update Tests**:
```python
def test_centroid_update_incremental():
    # Initial centroid
    C_old = np.array([1.0, 2.0, 3.0])
    n = 10
    
    # New point
    x = np.array([2.0, 3.0, 4.0])
    
    # Update formula
    C_new = (n * C_old + x) / (n + 1)
    
    expected = np.array([1.0909, 2.0909, 3.0909])
    np.testing.assert_array_almost_equal(C_new, expected, decimal=4)

def test_minibatch_kmeans_partial_fit():
    from sklearn.cluster import MiniBatchKMeans
    
    # Initial clustering
    X_init = np.random.randn(100, 10)
    kmeans = MiniBatchKMeans(n_clusters=3, random_state=42, batch_size=50)
    kmeans.fit(X_init)
    initial_centroids = kmeans.cluster_centers_.copy()
    
    # Partial fit with new data
    X_new = np.random.randn(50, 10)
    kmeans.partial_fit(X_new)
    updated_centroids = kmeans.cluster_centers_
    
    # Centroids should have changed
    assert not np.allclose(initial_centroids, updated_centroids)
```

**3. Metric Computation Tests**:
```python
from sklearn.metrics import silhouette_score, davies_bouldin_score

def test_silhouette_score_calculation():
    X = np.array([[1, 1], [2, 2], [10, 10], [11, 11]])
    labels = np.array([0, 0, 1, 1])
    
    score = silhouette_score(X, labels)
    assert 0.9 < score < 1.0  # Should be very good

def test_davies_bouldin_score_calculation():
    X = np.array([[1, 1], [2, 2], [10, 10], [11, 11]])
    labels = np.array([0, 0, 1, 1])
    
    score = davies_bouldin_score(X, labels)
    assert score < 1.0  # Lower is better
```

**4. Assignment Threshold Tests**:
```python
def test_assignment_confidence():
    centroid = np.array([0.5, 0.5, 0.5])
    new_point = np.array([0.6, 0.6, 0.6])  # Close to centroid
    
    distance = np.linalg.norm(new_point - centroid)
    threshold = 0.5
    
    assert distance < threshold  # Should assign

def test_cosine_similarity_assignment():
    from sklearn.metrics.pairwise import cosine_similarity
    
    centroid = np.array([[1.0, 0.0, 0.0]])
    point1 = np.array([[0.9, 0.1, 0.0]])  # Very similar
    point2 = np.array([[0.0, 1.0, 0.0]])  # Orthogonal
    
    sim1 = cosine_similarity(centroid, point1)[0][0]
    sim2 = cosine_similarity(centroid, point2)[0][0]
    
    assert sim1 > 0.8
    assert sim2 < 0.2
```

### Integration Tests

**5. End-to-End Clustering Flow**:
```python
# tests/integration/test_clustering_integration.py
import pytest
from app.services.clustering_service import clustering_service
from app.models.models import Document, User
from app.schemas.schemas import ClusterRequest

@pytest.mark.asyncio
async def test_full_clustering_workflow(test_db, test_user):
    # Create test documents
    docs = []
    for i in range(50):
        doc = Document(
            filename=f"test_doc_{i}.pdf",
            owner_id=test_user.id,
            # ... other fields
        )
        test_db.add(doc)
    test_db.commit()
    
    # Generate clusters
    request = ClusterRequest(
        algorithm="kmeans",
        n_clusters=5,
        reduction_method="umap",
        level="document"
    )
    
    result = await clustering_service.generate_clusters(request, test_user, test_db)
    
    # Assertions
    assert result.n_clusters == 5
    assert len(result.points) == 50
    assert len(result.summaries) == 5
    assert all(s.keywords for s in result.summaries)

@pytest.mark.asyncio
async def test_incremental_assignment(test_db, cluster_run):
    # Create new document
    new_doc = Document(filename="new.pdf", owner_id=test_user.id)
    test_db.add(new_doc)
    test_db.commit()
    
    # Assign to cluster
    cluster_id = await assign_document_to_cluster(new_doc.id, cluster_run.id)
    
    assert cluster_id in [0, 1, 2, 3, 4, -1]  # Valid cluster or unassigned
```

**6. Qdrant Integration Tests**:
```python
@pytest.mark.asyncio
async def test_qdrant_centroid_storage(qdrant_client, cluster_run):
    # Store centroids
    centroids = [
        {"id": "c1", "vector": [0.1] * 384, "payload": {"cluster_id": 0}},
        {"id": "c2", "vector": [0.2] * 384, "payload": {"cluster_id": 1}},
    ]
    
    qdrant_client.upsert(collection_name="cluster_centroids", points=centroids)
    
    # Retrieve
    results = qdrant_client.search(
        collection_name="cluster_centroids",
        query_vector=[0.15] * 384,
        limit=1
    )
    
    assert len(results) == 1
    assert results[0].payload["cluster_id"] in [0, 1]

@pytest.mark.asyncio
async def test_batch_document_retrieval():
    doc_ids = ["doc_1", "doc_2", "doc_3"]
    points = qdrant_client.retrieve(
        collection_name="documents",
        ids=doc_ids,
        with_vectors=True
    )
    
    assert len(points) == 3
    assert all(len(p.vector) == 384 for p in points)
```

**7. Drift Detection Tests**:
```python
def test_silhouette_drift_detection():
    baseline_silhouette = 0.65
    current_silhouette = 0.45  # Significant drop
    
    drift_detector = ClusterDriftDetector({"silhouette": baseline_silhouette})
    alerts = drift_detector.check_drift({"silhouette": current_silhouette})
    
    assert "silhouette_degradation" in alerts

def test_unassigned_rate_trigger():
    current_metrics = {
        "unassigned_rate": 0.35,  # 35% unassigned
        "new_docs_pct": 0.02
    }
    
    drift_detector = ClusterDriftDetector({})
    alerts = drift_detector.check_drift(current_metrics)
    
    assert "high_unassigned_rate" in alerts
```

### API Endpoint Tests

**8. API Tests**:
```python
# tests/api/test_clustering_api.py
from fastapi.testclient import TestClient

def test_generate_clusters_endpoint(client, auth_headers):
    response = client.post(
        "/api/clustering/generate",
        json={
            "algorithm": "kmeans",
            "n_clusters": 5,
            "reduction_method": "umap",
            "level": "document"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "cluster_run_id" in data

def test_get_cluster_result(client, auth_headers, cluster_run_id):
    response = client.get(
        f"/api/clustering/{cluster_run_id}/result",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "points" in data
    assert "summaries" in data

def test_assign_document_to_cluster(client, auth_headers, cluster_run_id):
    response = client.post(
        f"/api/clustering/{cluster_run_id}/assign",
        json={"document_id": 123},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "cluster_id" in data
    assert "confidence" in data
```

### Performance Tests

**9. Scalability Tests**:
```python
@pytest.mark.slow
def test_clustering_performance_1k_documents():
    import time
    
    embeddings = np.random.randn(1000, 384)
    
    start = time.time()
    labels = clustering_service._kmeans_clustering(embeddings, n_clusters=10)
    duration = time.time() - start
    
    assert duration < 5.0  # Should complete in < 5 seconds

@pytest.mark.slow
def test_umap_performance_10k_documents():
    embeddings = np.random.randn(10000, 384)
    
    start = time.time()
    reduced = clustering_service._umap_reduction(embeddings)
    duration = time.time() - start
    
    assert duration < 60.0  # Should complete in < 1 minute
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
from app.models.models import ClusterRun, ClusterSummary, User

@pytest.fixture
def test_user(test_db):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpw"
    )
    test_db.add(user)
    test_db.commit()
    return user

@pytest.fixture
def cluster_run(test_db, test_user):
    run = ClusterRun(
        id="test_run_123",
        owner_id=test_user.id,
        name="Test Clustering",
        algorithm="kmeans",
        params={"n_clusters": 5},
        status="completed",
        n_clusters=5,
        metrics={"silhouette": 0.65}
    )
    test_db.add(run)
    
    # Add summaries
    for i in range(5):
        summary = ClusterSummary(
            cluster_run_id=run.id,
            cluster_id=i,
            size=20,
            centroid=[0.1 * i] * 384,
            keywords=["keyword1", "keyword2"]
        )
        test_db.add(summary)
    
    test_db.commit()
    return run

@pytest.fixture
def sample_embeddings():
    return np.random.randn(100, 384).astype(np.float32)
```

### Test Coverage Goals

- **Unit tests**: >90% coverage of `clustering_service.py`
- **Integration tests**: Cover all major workflows
- **API tests**: 100% endpoint coverage
- **Performance tests**: Ensure scalability to 50k+ documents

## Example helper pseudocode (slug + name generator)

See earlier notes for a robust name/slug helper that uses top keywords and timestamp, slugifies, and retries on collisions.

```python
from datetime import datetime
import re
from slugify import slugify

def generate_cluster_run_name(summaries, algorithm):
    """
    Generate human-friendly cluster run name from top keywords
    Format: "algo-keyword1-keyword2-timestamp"
    """
    # Collect top keywords across all clusters
    all_keywords = []
    for summary in summaries:
        all_keywords.extend(summary.keywords[:2])  # Top 2 from each
    
    # Get most common
    keyword_counts = Counter(all_keywords)
    top_keywords = [word for word, _ in keyword_counts.most_common(3)]
    
    # Build name
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M")
    name_parts = [algorithm] + top_keywords + [timestamp]
    name = " ".join(name_parts)
    
    return name

def generate_unique_slug(name, db_session, max_retries=10):
    """
    Generate URL-safe unique slug, retry with suffix if collision
    """
    base_slug = slugify(name, max_length=60)
    slug = base_slug
    
    for i in range(max_retries):
        # Check if slug exists
        exists = db_session.query(ClusterRun).filter_by(slug=slug).first()
        if not exists:
            return slug
        
        # Add numeric suffix
        slug = f"{base_slug}-{i+1}"
    
    # Fallback: use UUID
    return f"{base_slug}-{uuid.uuid4().hex[:8]}"

# Usage
name = generate_cluster_run_name(summaries, "kmeans")
slug = generate_unique_slug(name, db)
# Example: "kmeans-machine-learning-model-20251102-1430"
```

---

## Additional Research Findings & Best Practices

### 1. Industry Standards & Benchmarks

**Document Clustering Performance**:
- **Small corpus** (<1k docs): Any algorithm works, prioritize interpretability
- **Medium corpus** (1k-50k): KMeans with k-means++, UMAP preprocessing
- **Large corpus** (>50k): MiniBatchKMeans, consider hierarchical approaches
- **Expected quality**: Silhouette 0.4-0.6 typical for text, 0.6+ is excellent

**Real-world Applications**:
- **News aggregation**: 10-30 clusters, hourly updates
- **Document management**: 5-15 clusters, daily/weekly updates
- **Research databases**: 20-100 clusters, monthly updates
- **Customer support**: 5-10 categories, real-time assignment

### 2. Embedding Considerations

**Best Models for Document Clustering**:
1. **all-MiniLM-L6-v2** (current): 384 dims, fast, good for general text
2. **all-mpnet-base-v2**: 768 dims, higher quality, slower
3. **multilingual-e5-base**: 768 dims, best for non-English
4. **OpenAI text-embedding-3-small**: 1536 dims, commercial quality

**Normalization**:
- Always L2-normalize embeddings before cosine similarity
- MinMaxScaler can help with KMeans (optional)
- StandardScaler rarely helps (embeddings pre-normalized)

### 3. Visualization Best Practices

**UMAP Parameters for Beautiful Plots**:
```python
# For tight, distinct clusters
reducer = umap.UMAP(
    n_neighbors=15,
    min_dist=0.1,
    metric='cosine',
    random_state=42
)

# For more spread, exploring structure
reducer = umap.UMAP(
    n_neighbors=30,
    min_dist=0.3,
    spread=1.0,
    metric='cosine'
)
```

**Interactive Visualization Libraries**:
- **Plotly**: Best for web-based interactive scatter plots
- **Bokeh**: Good for large datasets (WebGL)
- **D3.js**: Maximum customization
- **Three.js**: 3D visualizations

### 4. Alternative Approaches

**Hierarchical Clustering for Exploration**:
```python
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.cluster import AgglomerativeClustering

# Build hierarchy
linkage_matrix = linkage(embeddings, method='ward')

# Plot dendrogram
dendrogram(linkage_matrix, truncate_mode='level', p=5)

# Cut at optimal level
clusterer = AgglomerativeClustering(
    n_clusters=None,
    distance_threshold=optimal_threshold
)
```

**Topic Modeling as Alternative**:
- **LDA** (Latent Dirichlet Allocation): Interpretable topics
- **NMF** (Non-negative Matrix Factorization): Cleaner topics
- **BERTopic**: Modern, embedding-based topic modeling
- Use when keywords/topics more important than document grouping

**Neural Clustering**:
- **Deep Embedded Clustering (DEC)**: Learn embeddings + clusters jointly
- **AutoEncoders**: Reduce dimensions before clustering
- Overkill for <100k documents

### 5. Production Monitoring

**Key Metrics Dashboard**:
1. **Clustering Quality Trend**:
   - Silhouette score (7-day rolling avg)
   - Davies-Bouldin index trend
   - Cluster count evolution

2. **Operational Metrics**:
   - Clustering job duration (p50, p95, p99)
   - Success/failure rate
   - Queue depth (pending jobs)
   - Memory usage peaks

3. **User Behavior**:
   - Cluster runs per day
   - Re-cluster frequency
   - Assignment confidence distribution

4. **Data Quality**:
   - Unassigned document rate
   - Cluster size imbalance (Gini coefficient)
   - Singleton clusters (size=1)

**Alerting Thresholds**:
```python
ALERTS = {
    "silhouette_critical": 0.25,      # < 0.25 = poor quality
    "unassigned_rate_warning": 0.20,  # > 20%
    "unassigned_rate_critical": 0.40, # > 40%
    "job_duration_p95": 300,          # > 5 minutes
    "failure_rate": 0.10,             # > 10% failures
    "singleton_cluster_rate": 0.30    # > 30% size-1 clusters
}
```

### 6. Cost Optimization

**Compute Cost Reduction**:
1. **Batch processing**: Cluster nightly instead of real-time (90% cost savings)
2. **Sampling**: Use 10k sample for >100k docs (3x speedup)
3. **PCA preprocessing**: Reduce 768→50 dims before UMAP (2x speedup)
4. **Caching**: Store reduced embeddings, reuse across runs

**Storage Cost**:
- **Centroids only**: ~200KB per run (5 clusters × 384 dims × 100 runs = 20MB)
- **Full results**: ~50MB per run (10k docs × 2D coords + metadata)
- **Recommendation**: Keep centroids forever, expire full results after 30 days

### 7. Common Pitfalls & Solutions

**Problem**: Empty clusters in KMeans
**Solution**: Use `n_init=10` for multiple initializations, or `init='k-means++'`

**Problem**: HDBSCAN finds only noise (-1 labels)
**Solution**: Decrease `min_cluster_size` or increase `min_samples`

**Problem**: Clusters look random / no structure
**Solution**: Check embedding quality, try different embedding model, verify normalization

**Problem**: Slow clustering on large corpus
**Solution**: Use MiniBatchKMeans, sample to 50k, consider PCA to 50 dims first

**Problem**: Different results each run
**Solution**: Set `random_state=42` everywhere, use deterministic algorithms

**Problem**: Memory errors
**Solution**: Use batch processing, sample data, reduce embedding dimensions

### 8. Future Enhancements

**Advanced Features to Consider**:
1. **Active learning**: Let users label some clusters, refine automatically
2. **Constrained clustering**: User-specified must-link/cannot-link constraints
3. **Multi-view clustering**: Combine text + metadata (tags, dates, authors)
4. **Temporal clustering**: Track cluster evolution over time (GIF animations)
5. **Federated clustering**: Cluster across multiple user corpora with privacy
6. **Explanation UI**: "Why is this document in this cluster?" with attribution
7. **Cluster merging/splitting UI**: Manual refinement tools

---

## References & Further Reading

### Academic Papers
1. **KMeans++**: Arthur & Vassilvitskii (2007) - "k-means++: The Advantages of Careful Seeding"
2. **HDBSCAN**: Campello et al. (2013) - "Density-Based Clustering Based on Hierarchical Density Estimates"
3. **UMAP**: McInnes & Healy (2018) - "UMAP: Uniform Manifold Approximation and Projection"
4. **t-SNE**: van der Maaten & Hinton (2008) - "Visualizing Data using t-SNE"
5. **MiniBatchKMeans**: Sculley (2010) - "Web-Scale K-Means Clustering"

### Documentation
- Scikit-learn Clustering: https://scikit-learn.org/stable/modules/clustering.html
- HDBSCAN Docs: https://hdbscan.readthedocs.io/
- UMAP Documentation: https://umap-learn.readthedocs.io/
- Qdrant Docs: https://qdrant.tech/documentation/

### Tools & Libraries
- **scikit-learn**: Core clustering algorithms
- **hdbscan**: Advanced density-based clustering
- **umap-learn**: Fast dimensionality reduction
- **kneed**: Elbow detection for optimal k
- **yellowbrick**: Visualization for model selection

### Blogs & Tutorials
- Google ML Guide: Text Clustering Best Practices
- Towards Data Science: "Complete Guide to KMeans Clustering"
- UMAP Documentation: "How UMAP Works"
- Pinecone Blog: "Vector Database Clustering Patterns"

---

**Document Version**: 1.1 (Research-Enhanced)  
**Last Updated**: November 2, 2025  
**Author**: AI Assistant with comprehensive research  
**Status**: Implementation-ready with production best practices
