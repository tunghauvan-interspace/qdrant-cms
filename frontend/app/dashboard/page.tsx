'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  getCurrentUser,
  getDocuments,
  uploadDocument,
  deleteDocument,
  semanticSearch,
  ragSearch,
  Document,
  SearchResult,
  RAGResponse,
} from '@/lib/api';

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'documents' | 'upload' | 'search' | 'rag'>('documents');
  
  // Upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploadTags, setUploadTags] = useState('');
  const [uploadIsPublic, setUploadIsPublic] = useState('private');
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  
  // RAG state
  const [ragQuery, setRagQuery] = useState('');
  const [ragResponse, setRagResponse] = useState<RAGResponse | null>(null);
  const [ragLoading, setRagLoading] = useState(false);

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
      await loadDocuments();
    } catch (error) {
      localStorage.removeItem('token');
      router.push('/login');
    } finally {
      setLoading(false);
    }
  };

  const loadDocuments = async () => {
    try {
      const docs = await getDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error('Error loading documents:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploadLoading(true);
    setUploadError('');

    try {
      await uploadDocument(uploadFile, uploadDescription, uploadTags, uploadIsPublic);
      setUploadFile(null);
      setUploadDescription('');
      setUploadTags('');
      setUploadIsPublic('private');
      await loadDocuments();
      setActiveTab('documents');
    } catch (error: any) {
      setUploadError(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploadLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      await deleteDocument(id);
      await loadDocuments();
    } catch (error) {
      console.error('Error deleting document:', error);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery) return;

    setSearchLoading(true);
    try {
      const results = await semanticSearch(searchQuery);
      setSearchResults(results);
    } catch (error) {
      console.error('Error searching:', error);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleRAG = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ragQuery) return;

    setRagLoading(true);
    try {
      const response = await ragSearch(ragQuery);
      setRagResponse(response);
    } catch (error) {
      console.error('Error with RAG:', error);
    } finally {
      setRagLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Qdrant CMS/DMS</h1>
          <div className="flex items-center space-x-4">
            <span className="text-gray-700">Welcome, {user?.username}</span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('documents')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'documents'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              My Documents
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'upload'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Upload
            </button>
            <button
              onClick={() => setActiveTab('search')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'search'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Semantic Search
            </button>
            <button
              onClick={() => setActiveTab('rag')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'rag'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              RAG Query
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Documents Tab */}
        {activeTab === 'documents' && (
          <div className="px-4 py-6 sm:px-0">
            <h2 className="text-2xl font-bold mb-4">My Documents</h2>
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {documents.length === 0 ? (
                  <li className="px-4 py-4">
                    <p className="text-gray-500">No documents yet. Upload your first document!</p>
                  </li>
                ) : (
                  documents.map((doc) => (
                    <li key={doc.id} className="px-4 py-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center">
                            <p className="text-sm font-medium text-indigo-600 truncate">
                              {doc.original_filename}
                            </p>
                            <span className="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                              {doc.file_type}
                            </span>
                            <span className="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                              {doc.is_public}
                            </span>
                          </div>
                          {doc.description && (
                            <p className="mt-1 text-sm text-gray-500">{doc.description}</p>
                          )}
                          <div className="mt-1 flex items-center space-x-2">
                            <p className="text-xs text-gray-500">
                              Size: {(doc.file_size / 1024).toFixed(2)} KB
                            </p>
                            <p className="text-xs text-gray-500">
                              Uploaded: {new Date(doc.upload_date).toLocaleDateString()}
                            </p>
                            {doc.tags.length > 0 && (
                              <div className="flex space-x-1">
                                {doc.tags.map((tag) => (
                                  <span
                                    key={tag.id}
                                    className="px-2 py-0.5 text-xs rounded bg-gray-200 text-gray-700"
                                  >
                                    {tag.name}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        <div>
                          <button
                            onClick={() => handleDelete(doc.id)}
                            className="ml-4 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </li>
                  ))
                )}
              </ul>
            </div>
          </div>
        )}

        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div className="px-4 py-6 sm:px-0">
            <h2 className="text-2xl font-bold mb-4">Upload Document</h2>
            <div className="bg-white shadow sm:rounded-lg p-6">
              <form onSubmit={handleUpload} className="space-y-4">
                {uploadError && (
                  <div className="rounded-md bg-red-50 p-4">
                    <div className="text-sm text-red-800">{uploadError}</div>
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    File (PDF or DOCX)
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.docx,.doc"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="mt-1 block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Description (optional)
                  </label>
                  <textarea
                    value={uploadDescription}
                    onChange={(e) => setUploadDescription(e.target.value)}
                    rows={3}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Tags (comma-separated, optional)
                  </label>
                  <input
                    type="text"
                    value={uploadTags}
                    onChange={(e) => setUploadTags(e.target.value)}
                    placeholder="report, finance, 2024"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Access Level
                  </label>
                  <select
                    value={uploadIsPublic}
                    onChange={(e) => setUploadIsPublic(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                  >
                    <option value="private">Private</option>
                    <option value="public">Public</option>
                  </select>
                </div>
                <div>
                  <button
                    type="submit"
                    disabled={uploadLoading || !uploadFile}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    {uploadLoading ? 'Uploading...' : 'Upload Document'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="px-4 py-6 sm:px-0">
            <h2 className="text-2xl font-bold mb-4">Semantic Search</h2>
            <div className="bg-white shadow sm:rounded-lg p-6">
              <form onSubmit={handleSearch} className="mb-6">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Enter your search query..."
                    className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                    required
                  />
                  <button
                    type="submit"
                    disabled={searchLoading}
                    className="px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    {searchLoading ? 'Searching...' : 'Search'}
                  </button>
                </div>
              </form>

              {searchResults.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Search Results</h3>
                  {searchResults.map((result, idx) => (
                    <div key={idx} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-medium text-indigo-600">{result.filename}</p>
                          <p className="text-sm text-gray-500">
                            Relevance: {(result.score * 100).toFixed(2)}%
                          </p>
                        </div>
                      </div>
                      <p className="text-sm text-gray-700 mt-2">{result.chunk_content}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* RAG Tab */}
        {activeTab === 'rag' && (
          <div className="px-4 py-6 sm:px-0">
            <h2 className="text-2xl font-bold mb-4">RAG Query</h2>
            <div className="bg-white shadow sm:rounded-lg p-6">
              <form onSubmit={handleRAG} className="mb-6">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={ragQuery}
                    onChange={(e) => setRagQuery(e.target.value)}
                    placeholder="Ask a question about your documents..."
                    className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                    required
                  />
                  <button
                    type="submit"
                    disabled={ragLoading}
                    className="px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    {ragLoading ? 'Processing...' : 'Ask'}
                  </button>
                </div>
              </form>

              {ragResponse && (
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="text-lg font-medium mb-2">Answer</h3>
                    <p className="text-gray-700 whitespace-pre-line">{ragResponse.answer}</p>
                  </div>

                  {ragResponse.sources.length > 0 && (
                    <div>
                      <h3 className="text-lg font-medium mb-2">Sources</h3>
                      <div className="space-y-2">
                        {ragResponse.sources.map((source, idx) => (
                          <div key={idx} className="border rounded-lg p-3">
                            <p className="font-medium text-sm text-indigo-600">
                              {source.filename}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                              {source.chunk_content.substring(0, 200)}...
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
