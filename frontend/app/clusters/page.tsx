'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  getCurrentUser,
  generateClusters,
  getClusterStats,
  ClusterRequest,
  ClusterResult,
  ClusterPoint,
  ClusterSummary,
} from '@/lib/api';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

// Color-blind friendly palette (Okabe-Ito)
const CLUSTER_COLORS = [
  '#E69F00', // Orange
  '#56B4E9', // Sky Blue
  '#009E73', // Bluish Green
  '#F0E442', // Yellow
  '#0072B2', // Blue
  '#D55E00', // Vermillion
  '#CC79A7', // Reddish Purple
  '#999999', // Gray
  '#7B3294', // Purple
  '#1B9E77', // Teal
  '#D95F02', // Orange-Brown
  '#7570B3', // Purple-Blue
  '#E7298A', // Magenta
  '#66A61E', // Green
  '#E6AB02', // Yellow-Brown
  '#A6761D', // Brown
];

export default function ClustersPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [clustering, setClustering] = useState(false);
  const [clusterResult, setClusterResult] = useState<ClusterResult | null>(null);
  const [selectedClusterId, setSelectedClusterId] = useState<number | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<ClusterSummary | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  
  // Clustering parameters
  const [algorithm, setAlgorithm] = useState<'kmeans' | 'hdbscan'>('kmeans');
  const [nClusters, setNClusters] = useState(5);
  const [minClusterSize, setMinClusterSize] = useState(5);
  const [reductionMethod, setReductionMethod] = useState<'umap' | 'tsne'>('umap');
  const [level, setLevel] = useState<'document' | 'chunk'>('document');
  
  // UI state
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    try {
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (error) {
      localStorage.removeItem('token');
      router.push('/login');
    } finally {
      setLoading(false);
    }
  };

  const showToast = (type: 'success' | 'error' | 'info', message: string) => {
    setToastMessage({ type, message });
    setTimeout(() => setToastMessage(null), 5000);
  };

  const handleGenerateClusters = async () => {
    setClustering(true);
    try {
      const request: ClusterRequest = {
        algorithm,
        n_clusters: algorithm === 'kmeans' ? nClusters : undefined,
        min_cluster_size: algorithm === 'hdbscan' ? minClusterSize : undefined,
        reduction_method: reductionMethod,
        level,
      };

      const result = await generateClusters(request);
      setClusterResult(result);
      
      if (result.points.length === 0) {
        showToast('info', 'No documents available for clustering. Please upload some documents first.');
      } else {
        showToast('success', `Generated ${result.n_clusters} clusters with ${result.points.length} points`);
      }
    } catch (error: any) {
      console.error('Error generating clusters:', error);
      showToast('error', error.response?.data?.detail || 'Failed to generate clusters');
    } finally {
      setClustering(false);
    }
  };

  const handlePointClick = (data: any) => {
    if (!clusterResult) return;
    
    const clusterId = data.cluster_id;
    setSelectedClusterId(clusterId);
    
    const summary = clusterResult.summaries.find(s => s.cluster_id === clusterId);
    if (summary) {
      setSelectedCluster(summary);
      setShowDetailModal(true);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

  const getClusterColor = (clusterId: number) => {
    return CLUSTER_COLORS[clusterId % CLUSTER_COLORS.length];
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white border border-gray-300 rounded-lg p-3 shadow-lg">
          <p className="font-semibold text-gray-800">Cluster {data.cluster_id}</p>
          <p className="text-sm text-gray-600">{data.filename}</p>
          {data.chunk_content && (
            <p className="text-xs text-gray-500 mt-1 max-w-xs truncate">
              {data.chunk_content}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Document Clusters</h1>
            <p className="text-sm text-gray-500">Explore topics and discover semantic relationships</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={handleBackToDashboard}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              ← Back to Dashboard
            </button>
            <span className="text-gray-700">{user?.username}</span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Clustering Controls */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Clustering Configuration</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Algorithm Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Clustering Algorithm
              </label>
              <select
                value={algorithm}
                onChange={(e) => setAlgorithm(e.target.value as 'kmeans' | 'hdbscan')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={clustering}
              >
                <option value="kmeans">K-Means</option>
                <option value="hdbscan">HDBSCAN</option>
              </select>
            </div>

            {/* Number of Clusters (K-Means) */}
            {algorithm === 'kmeans' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Number of Clusters
                </label>
                <input
                  type="number"
                  min="2"
                  max="20"
                  value={nClusters}
                  onChange={(e) => setNClusters(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={clustering}
                />
              </div>
            )}

            {/* Min Cluster Size (HDBSCAN) */}
            {algorithm === 'hdbscan' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Min Cluster Size
                </label>
                <input
                  type="number"
                  min="2"
                  max="50"
                  value={minClusterSize}
                  onChange={(e) => setMinClusterSize(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={clustering}
                />
              </div>
            )}

            {/* Reduction Method */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Visualization Method
              </label>
              <select
                value={reductionMethod}
                onChange={(e) => setReductionMethod(e.target.value as 'umap' | 'tsne')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={clustering}
              >
                <option value="umap">UMAP</option>
                <option value="tsne">t-SNE</option>
              </select>
            </div>

            {/* Clustering Level */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Clustering Level
              </label>
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value as 'document' | 'chunk')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={clustering}
              >
                <option value="document">Document Level</option>
                <option value="chunk">Chunk Level</option>
              </select>
            </div>
          </div>

          <div className="mt-6">
            <button
              onClick={handleGenerateClusters}
              disabled={clustering}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
            >
              {clustering ? (
                <>
                  <span className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
                  Generating Clusters...
                </>
              ) : (
                'Generate Clusters'
              )}
            </button>
          </div>
        </div>

        {/* Cluster Visualization */}
        {clusterResult && clusterResult.points.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Cluster Visualization</h2>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600">
                Found <strong>{clusterResult.n_clusters}</strong> clusters across{' '}
                <strong>{clusterResult.points.length}</strong> {level === 'document' ? 'documents' : 'chunks'}
              </p>
            </div>

            <ResponsiveContainer width="100%" height={500}>
              <ScatterChart
                margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" dataKey="x" name="X" />
                <YAxis type="number" dataKey="y" name="Y" />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                {clusterResult.summaries.map((summary) => (
                  <Scatter
                    key={summary.cluster_id}
                    name={`Cluster ${summary.cluster_id} (${summary.size})`}
                    data={clusterResult.points.filter(p => p.cluster_id === summary.cluster_id)}
                    fill={getClusterColor(summary.cluster_id)}
                    onClick={handlePointClick}
                    style={{ cursor: 'pointer' }}
                  />
                ))}
              </ScatterChart>
            </ResponsiveContainer>

            {/* Cluster Legend with Keywords */}
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {clusterResult.summaries.map((summary) => (
                <div
                  key={summary.cluster_id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => {
                    setSelectedCluster(summary);
                    setShowDetailModal(true);
                  }}
                  style={{ borderLeftWidth: '4px', borderLeftColor: getClusterColor(summary.cluster_id) }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">Cluster {summary.cluster_id}</h3>
                    <span className="text-sm text-gray-500">{summary.size} items</span>
                  </div>
                  {summary.keywords && summary.keywords.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {summary.keywords.slice(0, 3).map((keyword, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!clusterResult && (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="text-gray-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Clusters Generated</h3>
            <p className="text-gray-600 mb-6">
              Configure the clustering parameters above and click "Generate Clusters" to visualize your document topics.
            </p>
          </div>
        )}
      </main>

      {/* Cluster Detail Modal */}
      {showDetailModal && selectedCluster && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    Cluster {selectedCluster.cluster_id}
                  </h2>
                  <p className="text-gray-600">{selectedCluster.size} items in this cluster</p>
                </div>
                <button
                  onClick={() => setShowDetailModal(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                  aria-label="Close modal"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Keywords */}
              {selectedCluster.keywords && selectedCluster.keywords.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-semibold text-gray-900 mb-2">Topic Keywords</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedCluster.keywords.map((keyword, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Representative Documents */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Representative Documents</h3>
                <div className="space-y-3">
                  {selectedCluster.representative_docs.map((doc, idx) => (
                    <div
                      key={idx}
                      className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">{doc.filename}</h4>
                          {doc.description && (
                            <p className="text-sm text-gray-600 mt-1">{doc.description}</p>
                          )}
                          {level === 'chunk' && doc.count > 1 && (
                            <p className="text-xs text-gray-500 mt-1">{doc.count} chunks in this cluster</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setShowDetailModal(false)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-4 right-4 z-50 animate-fade-in">
          <div
            className={`rounded-lg shadow-lg p-4 ${
              toastMessage.type === 'success'
                ? 'bg-green-500 text-white'
                : toastMessage.type === 'error'
                ? 'bg-red-500 text-white'
                : 'bg-blue-500 text-white'
            }`}
          >
            <p className="font-medium">{toastMessage.message}</p>
          </div>
        </div>
      )}
    </div>
  );
}
