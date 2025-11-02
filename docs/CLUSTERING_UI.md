# Clustering Feature UI

## Overview
The clustering feature provides an interactive visualization interface for exploring document topics and semantic relationships.

## User Interface Components

### 1. Clustering Configuration Panel
Located at the top of the clusters page, this panel allows users to configure:

- **Algorithm Selection**: Choose between K-Means or HDBSCAN
- **Number of Clusters** (K-Means): Specify 2-20 clusters
- **Min Cluster Size** (HDBSCAN): Set minimum size for automatic detection
- **Visualization Method**: Select UMAP or t-SNE for 2D projection
- **Clustering Level**: Choose document-level or chunk-level analysis
- **Generate Button**: Initiates the clustering process

### 2. Interactive Scatter Plot
The main visualization area features:

- **Color-coded clusters**: Each cluster has a distinct color from the Okabe-Ito palette
- **Hover tooltips**: Shows document/chunk details on hover
- **Click interaction**: Click any point to open cluster details
- **Responsive layout**: Adapts to different screen sizes
- **Legend**: Displays all clusters with sizes

### 3. Cluster Summary Cards
Below the visualization, a grid of cards shows:

- **Cluster ID**: Unique identifier for each cluster
- **Size**: Number of documents/chunks in cluster
- **Keywords**: Top 3-5 extracted keywords per cluster
- **Click to expand**: Opens detailed modal

### 4. Cluster Detail Modal
When clicking a cluster, a modal shows:

- **Full keyword list**: All extracted topic keywords
- **Representative documents**: Up to 3 key documents per cluster
- **Document metadata**: Filename, description, chunk count
- **Close button**: Returns to main view

### 5. Navigation
- **Dashboard link**: Returns to main dashboard
- **User info**: Display current username
- **Logout button**: Sign out option

## Color Palette (Okabe-Ito)
The clustering visualization uses a color-blind friendly palette:

1. Orange (#E69F00)
2. Sky Blue (#56B4E9)
3. Bluish Green (#009E73)
4. Yellow (#F0E442)
5. Blue (#0072B2)
6. Vermillion (#D55E00)
7. Reddish Purple (#CC79A7)
8. Gray (#999999)
9. Additional colors for >8 clusters

## Responsive Design
- **Desktop**: Full scatter plot with sidebar
- **Tablet**: Adjusted layout with collapsible controls
- **Mobile**: Stacked layout with touch-friendly interactions

## Accessibility Features
- **Keyboard navigation**: Tab through clusters and controls
- **ARIA labels**: Screen reader support
- **High contrast**: Clear visual hierarchy
- **Color-blind safe**: Distinguishable colors for all users
- **Focus indicators**: Clear visual focus states

## Toast Notifications
Success, error, and info messages appear in bottom-right corner for:
- Cluster generation success
- Error messages
- Empty state warnings

## Empty State
When no clusters are generated, shows:
- Icon placeholder
- Instructional text
- Call-to-action message
