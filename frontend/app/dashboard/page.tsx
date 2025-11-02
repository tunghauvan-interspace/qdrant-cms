'use client';

import { useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import {
  getCurrentUser,
  getDocuments,
  uploadDocument,
  deleteDocument,
  previewDocument,
  semanticSearch,
  ragSearch,
  updateDocument,
  getDocumentVersions,
  rollbackToVersion,
  Document,
  DocumentPreview,
  SearchResult,
  RAGResponse,
  DocumentVersion,
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
  
  // Preview state
  const [previewData, setPreviewData] = useState<DocumentPreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  
  // Edit document state
  const [editingDocument, setEditingDocument] = useState<Document | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editDescription, setEditDescription] = useState('');
  const [editTags, setEditTags] = useState('');
  const [editIsPublic, setEditIsPublic] = useState('private');
  const [editFile, setEditFile] = useState<File | null>(null);
  const [editLoading, setEditLoading] = useState(false);
  
  // Version history state
  const [showVersionModal, setShowVersionModal] = useState(false);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [selectedDocumentForVersions, setSelectedDocumentForVersions] = useState<Document | null>(null);
  
  // UI state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);
  const [selectedDocuments, setSelectedDocuments] = useState<Set<number>>(new Set());
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [openDropdownId, setOpenDropdownId] = useState<number | null>(null);

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    // Close dropdown when clicking outside
    const handleClickOutside = (event: MouseEvent) => {
      if (openDropdownId !== null) {
        const target = event.target as HTMLElement;
        if (!target.closest('.relative')) {
          setOpenDropdownId(null);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [openDropdownId]);

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

  const showToast = (type: 'success' | 'error' | 'info', message: string) => {
    setToastMessage({ type, message });
    setTimeout(() => setToastMessage(null), 5000);
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploadLoading(true);
    setUploadError('');
    setUploadProgress(0);

    try {
      // Simulate progress (in real app, this would come from upload progress)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      await uploadDocument(uploadFile, uploadDescription, uploadTags, uploadIsPublic);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      setUploadFile(null);
      setUploadDescription('');
      setUploadTags('');
      setUploadIsPublic('private');
      await loadDocuments();
      showToast('success', 'Document uploaded and indexed successfully');
      setActiveTab('documents');
    } catch (error: any) {
      setUploadError(error.response?.data?.detail || 'Upload failed');
      showToast('error', 'Failed to upload document');
    } finally {
      setUploadLoading(false);
      setUploadProgress(0);
    }
  };

  const handleDelete = async (id: number, filename: string) => {
    // Modal confirmation will be shown via UI component
    return new Promise((resolve) => {
      const confirmed = confirm(`Delete "${filename}"? This action cannot be undone.`);
      if (!confirmed) {
        resolve(false);
        return;
      }

      deleteDocument(id)
        .then(async () => {
          await loadDocuments();
          showToast('success', 'Document deleted successfully');
          resolve(true);
        })
        .catch((error) => {
          console.error('Error deleting document:', error);
          showToast('error', 'Failed to delete document');
          resolve(false);
        });
    });
  };

  const handleBulkDelete = async () => {
    if (selectedDocuments.size === 0) return;
    
    const confirmed = confirm(`Delete ${selectedDocuments.size} document(s)? This action cannot be undone.`);
    if (!confirmed) return;

    try {
      await Promise.all(
        Array.from(selectedDocuments).map(id => deleteDocument(id))
      );
      await loadDocuments();
      setSelectedDocuments(new Set());
      showToast('success', `${selectedDocuments.size} document(s) deleted successfully`);
    } catch (error) {
      showToast('error', 'Failed to delete some documents');
    }
  };

  const toggleDocumentSelection = (id: number) => {
    const newSelection = new Set(selectedDocuments);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedDocuments(newSelection);
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

  const handlePreview = async (id: number) => {
    setPreviewLoading(true);
    try {
      const preview = await previewDocument(id);
      setPreviewData(preview);
      setShowPreviewModal(true);
    } catch (error) {
      console.error('Error loading preview:', error);
      alert('Failed to load preview. Please try again.');
    } finally {
      setPreviewLoading(false);
    }
  };

  const closePreviewModal = () => {
    setShowPreviewModal(false);
    setPreviewData(null);
  };

  const handleEditDocument = (doc: Document) => {
    setEditingDocument(doc);
    setEditDescription(doc.description || '');
    setEditTags(doc.tags.map(t => t.name).join(', '));
    setEditIsPublic(doc.is_public);
    setEditFile(null);
    setShowEditModal(true);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingDocument) return;

    setEditLoading(true);
    try {
      // If a new file is provided, upload it (overwrite)
      if (editFile) {
        // Delete old document and upload new one
        await deleteDocument(editingDocument.id);
        await uploadDocument(editFile, editDescription, editTags, editIsPublic);
        showToast('success', 'Document updated successfully with new file');
      } else {
        // Just update metadata
        await updateDocument(editingDocument.id, {
          description: editDescription,
          tags: editTags.split(',').map(t => t.trim()).filter(t => t),
          is_public: editIsPublic,
        });
        showToast('success', 'Document metadata updated successfully');
      }
      
      await loadDocuments();
      setShowEditModal(false);
      setEditingDocument(null);
    } catch (error) {
      console.error('Error updating document:', error);
      showToast('error', 'Failed to update document');
    } finally {
      setEditLoading(false);
    }
  };

  const closeEditModal = () => {
    setShowEditModal(false);
    setEditingDocument(null);
    setEditFile(null);
  };

  const handleViewVersions = async (doc: Document) => {
    setSelectedDocumentForVersions(doc);
    setVersionsLoading(true);
    setShowVersionModal(true);
    
    try {
      const versionHistory = await getDocumentVersions(doc.id);
      setVersions(versionHistory);
    } catch (error) {
      console.error('Error loading versions:', error);
      showToast('error', 'Failed to load version history');
    } finally {
      setVersionsLoading(false);
    }
  };

  const handleRollback = async (versionId: number) => {
    if (!selectedDocumentForVersions) return;
    
    if (!confirm('Are you sure you want to rollback to this version? This will create a new version with the previous state.')) {
      return;
    }

    try {
      await rollbackToVersion(selectedDocumentForVersions.id, versionId);
      showToast('success', 'Document rolled back successfully');
      await loadDocuments();
      setShowVersionModal(false);
    } catch (error) {
      console.error('Error rolling back:', error);
      showToast('error', 'Failed to rollback document');
    }
  };

  const closeVersionModal = () => {
    setShowVersionModal(false);
    setSelectedDocumentForVersions(null);
    setVersions([]);
  };

  const toggleDropdown = (docId: number) => {
    setOpenDropdownId(openDropdownId === docId ? null : docId);
  };


  // Calculate statistics using useMemo for performance
  const statistics = useMemo(() => {
    const stats = documents.reduce((acc, doc) => {
      acc.total += 1;
      acc.size += doc.file_size;
      if (doc.is_public === 'public') {
        acc.public += 1;
      } else {
        acc.private += 1;
      }
      doc.tags.forEach(tag => acc.tags.add(tag.name));
      return acc;
    }, {
      total: 0,
      public: 0,
      private: 0,
      size: 0,
      tags: new Set<string>()
    });
    
    return stats;
  }, [documents]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center animate-scale-in">
          <div className="spinner w-8 h-8 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }


  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Toast Notifications */}
      {toastMessage && (
        <div className={`fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg animate-slide-in-down flex items-center space-x-3 ${
          toastMessage.type === 'success' ? 'bg-green-50 border border-green-200' :
          toastMessage.type === 'error' ? 'bg-red-50 border border-red-200' :
          'bg-blue-50 border border-blue-200'
        }`}>
          {toastMessage.type === 'success' && (
            <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          )}
          {toastMessage.type === 'error' && (
            <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          )}
          {toastMessage.type === 'info' && (
            <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          )}
          <p className={`text-sm font-medium ${
            toastMessage.type === 'success' ? 'text-green-800' :
            toastMessage.type === 'error' ? 'text-red-800' :
            'text-blue-800'
          }`}>{toastMessage.message}</p>
          <button onClick={() => setToastMessage(null)} className="ml-2">
            <svg className="w-4 h-4 text-gray-400 hover:text-gray-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      )}

      {/* Persistent Sidebar - Collapsible */}
      <aside className={`fixed inset-y-0 left-0 bg-white border-r border-gray-200 flex flex-col z-20 hidden lg:flex transition-all duration-300 ${
        sidebarCollapsed ? 'w-20' : 'w-64'
      }`}>
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          {!sidebarCollapsed && (
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-md flex-shrink-0">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-base font-bold text-gray-900">Qdrant CMS</h1>
                <p className="text-xs text-gray-500">Document System</p>
              </div>
            </div>
          )}
          {sidebarCollapsed && (
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-md mx-auto">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {sidebarCollapsed ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
              )}
            </svg>
          </button>
        </div>

        {/* Sidebar Navigation */}
        <nav className="flex-1 p-3 overflow-y-auto">
          <div className="space-y-1">
            {[
              { id: 'documents', label: 'Documents', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', description: 'Manage your files' },
              { id: 'upload', label: 'Upload', icon: 'M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12', description: 'Add new content' },
              { id: 'search', label: 'Vector Search', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z', description: 'Semantic search' },
              { id: 'rag', label: 'AI Query', icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z', description: 'Ask questions' },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id as any)}
                className={`w-full flex items-center p-3 rounded-lg transition-all group relative ${
                  activeTab === item.id
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
                aria-label={`Navigate to ${item.label}`}
                aria-current={activeTab === item.id ? 'page' : undefined}
                title={sidebarCollapsed ? item.label : ''}
              >
                <svg className={`w-5 h-5 ${sidebarCollapsed ? 'mx-auto' : 'mr-3'} flex-shrink-0 ${activeTab === item.id ? 'text-white' : 'text-gray-500 group-hover:text-gray-700'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
                </svg>
                {!sidebarCollapsed && (
                  <div className="text-left flex-1">
                    <div className="text-sm font-medium">{item.label}</div>
                    <div className={`text-xs mt-0.5 ${activeTab === item.id ? 'text-indigo-100' : 'text-gray-500'}`}>{item.description}</div>
                  </div>
                )}
                {activeTab === item.id && !sidebarCollapsed && (
                  <div className="w-1 h-8 bg-white rounded-full absolute right-2"></div>
                )}
              </button>
            ))}
          </div>
        </nav>

        {/* Sidebar Footer - User Info */}
        <div className="p-3 border-t border-gray-200">
          {!sidebarCollapsed ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3 flex-1 min-w-0">
                <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{user?.username}</p>
                  <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                aria-label="Logout"
                title="Logout"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          ) : (
            <button
              onClick={handleLogout}
              className="w-full p-3 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors flex items-center justify-center"
              aria-label="Logout"
              title="Logout"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          )}
        </div>
      </aside>

      {/* Main Content Area - CMS Standard Layout */}
      <div className={`flex-1 transition-all duration-300 ${sidebarCollapsed ? 'lg:pl-20' : 'lg:pl-64'}`}>
        {/* Fixed Header for Mobile/Tablet */}
        <header className="sticky top-0 z-10 bg-white border-b border-gray-200 lg:hidden">
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">Qdrant CMS</h1>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="btn btn-danger"
              aria-label="Logout"
            >
              Logout
            </button>
          </div>
          {/* Mobile Navigation */}
          <nav className="px-4 pb-2 overflow-x-auto">
            <div className="flex space-x-2">
              {[
                { id: 'documents', label: 'Documents', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
                { id: 'upload', label: 'Upload', icon: 'M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12' },
                { id: 'search', label: 'Search', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' },
                { id: 'rag', label: 'AI Query', icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z' },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as any)}
                  className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap ${
                    activeTab === item.id
                      ? 'bg-indigo-50 text-indigo-600'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
                  </svg>
                  {item.label}
                </button>
              ))}
            </div>
          </nav>
        </header>

        {/* Top Bar with Global Search - Hidden on search/rag tabs to avoid duplication */}
        {activeTab !== 'search' && activeTab !== 'rag' && (
          <div className="sticky top-0 z-10 bg-white border-b border-gray-200 px-6 py-4 hidden lg:block">
            <div className="flex items-center justify-between gap-4">
              {/* Global Search Bar */}
              <div className="flex-1 max-w-2xl">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && searchQuery && (setActiveTab('search'), handleSearch(e as any))}
                    placeholder="Search documents with AI... (Ctrl+K)"
                    className="block w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery('')}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    >
                      <svg className="h-5 w-5 text-gray-400 hover:text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setActiveTab('upload')}
                  className="btn btn-primary text-sm flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Upload Document
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <main className="p-4 sm:p-6">
          {/* Page Header with Breadcrumb */}
          <div className="mb-4">
            <div className="flex items-center text-sm text-gray-500 mb-2">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              <span>Dashboard</span>
              <svg className="w-4 h-4 mx-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span className="text-gray-900 font-medium">
                {activeTab === 'documents' && 'My Documents'}
                {activeTab === 'upload' && 'Upload'}
                {activeTab === 'search' && 'Vector Search'}
                {activeTab === 'rag' && 'AI Query'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">
                {activeTab === 'documents' && 'Library Overview'}
                {activeTab === 'upload' && 'Upload Document'}
                {activeTab === 'search' && 'Vector Search'}
                {activeTab === 'rag' && 'AI Query'}
              </h2>
              {activeTab === 'documents' && selectedDocuments.size > 0 && (
                <button
                  onClick={handleBulkDelete}
                  className="btn btn-danger text-sm flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Delete Selected ({selectedDocuments.size})
                </button>
              )}
            </div>
          </div>

        {/* Documents Tab */}
        {activeTab === 'documents' && (
          <div className="space-y-6 animate-fade-in">
            {/* Statistics Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Documents</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{statistics.total}</p>
                  </div>
                  <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Public Docs</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{statistics.public}</p>
                  </div>
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Private Docs</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{statistics.private}</p>
                  </div>
                  <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Size</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">
                      {(statistics.size / (1024 * 1024)).toFixed(1)}
                      <span className="text-lg font-normal text-gray-600"> MB</span>
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            {/* Documents List */}
            <div>
              <div className="card overflow-hidden">
                {documents.length === 0 ? (
                  <div className="text-center py-16 px-4">
                    <div className="mx-auto w-20 h-20 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl flex items-center justify-center mb-4">
                      <svg className="w-10 h-10 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No documents uploaded yet</h3>
                    <p className="text-gray-600 mb-6 max-w-sm mx-auto">Click <strong>Upload Document</strong> to add your first file and start managing your content with AI-powered search.</p>
                    <button
                      onClick={() => setActiveTab('upload')}
                      className="btn btn-primary inline-flex items-center"
                    >
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      Upload Document
                    </button>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="w-12 px-4 py-3">
                            <input
                              type="checkbox"
                              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                              checked={selectedDocuments.size === documents.length}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedDocuments(new Set(documents.map(d => d.id)));
                                } else {
                                  setSelectedDocuments(new Set());
                                }
                              }}
                              aria-label="Select all documents"
                            />
                          </th>
                          <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                            Document
                          </th>
                          <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider hidden md:table-cell">
                            Details
                          </th>
                          <th scope="col" className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {documents.map((doc) => (
                          <tr key={doc.id} className={`hover:bg-gray-50 transition-colors ${selectedDocuments.has(doc.id) ? 'bg-indigo-50' : ''}`}>
                            <td className="px-4 py-4">
                              <input
                                type="checkbox"
                                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                                checked={selectedDocuments.has(doc.id)}
                                onChange={() => toggleDocumentSelection(doc.id)}
                                aria-label={`Select ${doc.original_filename}`}
                              />
                            </td>
                            <td className="px-4 py-4">
                              <div className="flex items-center space-x-3">
                                <div className="flex-shrink-0">
                                  <div className="w-10 h-10 bg-gradient-to-br from-indigo-100 to-indigo-200 rounded-lg flex items-center justify-center shadow-sm">
                                    <svg className="w-5 h-5 text-indigo-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                  </div>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-semibold text-gray-900 truncate">
                                    {doc.original_filename}
                                  </p>
                                  <div className="flex items-center space-x-2 mt-1">
                                    <span className="badge bg-indigo-100 text-indigo-700 text-xs">
                                      {doc.file_type.toUpperCase()}
                                    </span>
                                    <span className={`badge text-xs ${doc.is_public === 'public' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                                      {doc.is_public === 'public' ? 'Public' : 'Private'}
                                    </span>
                                  </div>
                                  {doc.description && (
                                    <p className="text-xs text-gray-500 mt-1 line-clamp-1">{doc.description}</p>
                                  )}
                                </div>
                              </div>
                            </td>
                            <td className="px-4 py-4 hidden md:table-cell">
                              <div className="space-y-2">
                                <div className="flex items-center text-xs text-gray-600">
                                  <svg className="w-4 h-4 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                                  </svg>
                                  {(doc.file_size / 1024).toFixed(1)} KB
                                </div>
                                <div className="flex items-center text-xs text-gray-600">
                                  <svg className="w-4 h-4 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                  </svg>
                                  {new Date(doc.upload_date).toLocaleDateString()}
                                </div>
                                {doc.tags.length > 0 && (
                                  <div className="flex flex-wrap gap-1">
                                    {doc.tags.slice(0, 3).map((tag) => (
                                      <span key={tag.id} className="badge bg-gray-100 text-gray-600 text-xs">
                                        #{tag.name}
                                      </span>
                                    ))}
                                    {doc.tags.length > 3 && (
                                      <span className="text-xs text-gray-500">+{doc.tags.length - 3}</span>
                                    )}
                                  </div>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-4 text-right">
                              <div className="flex items-center justify-end gap-2">
                                {/* Primary Actions - Always Visible */}
                                <button
                                  onClick={() => handlePreview(doc.id)}
                                  disabled={previewLoading}
                                  className="p-2 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                                  aria-label={`View ${doc.original_filename}`}
                                  title="View Document"
                                >
                                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() => handleEditDocument(doc)}
                                  className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                  aria-label={`Edit ${doc.original_filename}`}
                                  title="Edit Document"
                                >
                                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                  </svg>
                                </button>
                                
                                {/* More Actions Dropdown */}
                                <div className="relative">
                                  <button
                                    onClick={() => toggleDropdown(doc.id)}
                                    className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                                    aria-label="More actions"
                                    title="More Actions"
                                  >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                                    </svg>
                                  </button>
                                  
                                  {/* Dropdown Menu */}
                                  {openDropdownId === doc.id && (
                                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10 animate-scale-in">
                                      <div className="py-1">
                                        <button
                                          onClick={() => {
                                            handleViewVersions(doc);
                                            setOpenDropdownId(null);
                                          }}
                                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                                        >
                                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                          </svg>
                                          Version History
                                        </button>
                                        <button
                                          onClick={() => {
                                            navigator.clipboard.writeText(doc.original_filename);
                                            showToast('success', 'Filename copied to clipboard');
                                            setOpenDropdownId(null);
                                          }}
                                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                                        >
                                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                          </svg>
                                          Copy Filename
                                        </button>
                                        <div className="border-t border-gray-200 my-1"></div>
                                        <button
                                          onClick={() => {
                                            handleDelete(doc.id, doc.original_filename);
                                            setOpenDropdownId(null);
                                          }}
                                          className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center"
                                        >
                                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                          </svg>
                                          Delete
                                        </button>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div className="animate-fade-in">
            <div className="max-w-3xl">
              <div className="card p-6 sm:p-8">
                <form onSubmit={handleUpload} className="space-y-6">
                  {uploadError && (
                    <div className="rounded-lg bg-red-50 border border-red-200 p-4 animate-slide-in-down" role="alert">
                      <div className="flex items-center">
                        <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                        <p className="text-sm font-medium text-red-800">{uploadError}</p>
                      </div>
                    </div>
                  )}

                  <div>
                    <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700 mb-2">
                      Document File
                    </label>
                    <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-indigo-400 transition-colors">
                      <div className="space-y-1 text-center">
                        <svg
                          className="mx-auto h-12 w-12 text-gray-400"
                          stroke="currentColor"
                          fill="none"
                          viewBox="0 0 48 48"
                          aria-hidden="true"
                        >
                          <path
                            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                            strokeWidth={2}
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                        <div className="flex text-sm text-gray-600">
                          <label
                            htmlFor="file-upload"
                            className="relative cursor-pointer rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500"
                          >
                            <span>Upload a file</span>
                            <input
                              id="file-upload"
                              name="file-upload"
                              type="file"
                              accept=".pdf,.docx,.doc"
                              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                              className="sr-only"
                              required
                            />
                          </label>
                          <p className="pl-1">or drag and drop</p>
                        </div>
                        <p className="text-xs text-gray-500">PDF or DOCX up to 50MB</p>
                        {uploadFile && !uploadLoading && (
                          <p className="text-sm font-medium text-indigo-600 mt-2 flex items-center">
                            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            {uploadFile.name}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Upload Progress */}
                  {uploadLoading && uploadProgress > 0 && (
                    <div className="rounded-lg bg-indigo-50 border border-indigo-200 p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-indigo-900">Uploading and indexing...</span>
                        <span className="text-sm font-semibold text-indigo-600">{uploadProgress}%</span>
                      </div>
                      <div className="w-full bg-indigo-200 rounded-full h-2.5">
                        <div 
                          className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-indigo-700 mt-2">Processing document with AI embeddings...</p>
                    </div>
                  )}

                  <div>
                    <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                      Description <span className="text-gray-500 font-normal">(optional)</span>
                    </label>
                    <textarea
                      id="description"
                      name="description"
                      value={uploadDescription}
                      onChange={(e) => setUploadDescription(e.target.value)}
                      rows={3}
                      className="input w-full"
                      placeholder="Add a description for this document..."
                    />
                  </div>

                  <div>
                    <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-2">
                      Tags <span className="text-gray-500 font-normal">(optional)</span>
                    </label>
                    <input
                      id="tags"
                      name="tags"
                      type="text"
                      value={uploadTags}
                      onChange={(e) => setUploadTags(e.target.value)}
                      placeholder="e.g., report, finance, 2024"
                      className="input w-full"
                    />
                    <p className="mt-1 text-xs text-gray-500">Separate tags with commas</p>
                  </div>

                  <div>
                    <label htmlFor="access-level" className="block text-sm font-medium text-gray-700 mb-2">
                      Access Level
                    </label>
                    <select
                      id="access-level"
                      name="access-level"
                      value={uploadIsPublic}
                      onChange={(e) => setUploadIsPublic(e.target.value)}
                      className="input w-full"
                    >
                      <option value="private">Private - Only you can access</option>
                      <option value="public">Public - Anyone can access</option>
                    </select>
                  </div>

                  <div className="flex gap-3">
                    <button
                      type="submit"
                      disabled={uploadLoading || !uploadFile}
                      className="btn btn-primary flex-1 py-3 flex items-center justify-center"
                    >
                      {uploadLoading ? (
                        <>
                          <span className="spinner mr-2"></span>
                          Uploading...
                        </>
                      ) : (
                        <>
                          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                          Upload Document
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setUploadFile(null);
                        setUploadDescription('');
                        setUploadTags('');
                        setUploadError('');
                      }}
                      className="btn btn-secondary px-6"
                    >
                      Clear
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="animate-fade-in">
            <div className="space-y-6">
              <div className="card p-6">
                <form onSubmit={handleSearch} className="space-y-4">
                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="What are you looking for?"
                      className="input flex-1"
                      required
                      aria-label="Search query"
                    />
                    <button
                      type="submit"
                      disabled={searchLoading}
                      className="btn btn-primary flex items-center px-6"
                    >
                      {searchLoading ? (
                        <>
                          <span className="spinner mr-2"></span>
                          Searching...
                        </>
                      ) : (
                        <>
                          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                          </svg>
                          Search
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>

              {searchResults.length > 0 && (
                <div className="space-y-4 animate-slide-in-up">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Found {searchResults.length} {searchResults.length === 1 ? 'result' : 'results'}
                    </h3>
                    <button
                      onClick={() => {
                        setSearchResults([]);
                        setSearchQuery('');
                      }}
                      className="text-sm text-indigo-600 hover:text-indigo-700"
                    >
                      Clear results
                    </button>
                  </div>
                  {searchResults.map((result, idx) => (
                    <div key={idx} className="card p-5 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <h4 className="font-semibold text-gray-900">{result.filename}</h4>
                          </div>
                          <div className="flex items-center space-x-3 text-xs text-gray-500 mb-3">
                            <span className="flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                              Relevance: {(result.score * 100).toFixed(1)}%
                            </span>
                            <span className="w-full bg-gray-200 rounded-full h-1.5 max-w-[100px]">
                              <div 
                                className="bg-indigo-600 h-1.5 rounded-full" 
                                style={{ width: `${result.score * 100}%` }}
                              ></div>
                            </span>
                          </div>
                        </div>
                      </div>
                      <p className="text-sm text-gray-700 leading-relaxed bg-gray-50 p-3 rounded-lg">
                        {result.chunk_content}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {searchQuery && searchResults.length === 0 && !searchLoading && (
                <div className="card p-12 text-center">
                  <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
                  <p className="text-gray-500">Try adjusting your search query</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* RAG Tab */}
        {activeTab === 'rag' && (
          <div className="animate-fade-in">
            <div className="space-y-6">
              <div className="card p-6">
                <form onSubmit={handleRAG} className="space-y-4">
                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={ragQuery}
                      onChange={(e) => setRagQuery(e.target.value)}
                      placeholder="Ask a question about your documents..."
                      className="input flex-1"
                      required
                      aria-label="RAG query"
                    />
                    <button
                      type="submit"
                      disabled={ragLoading}
                      className="btn btn-primary flex items-center px-6"
                    >
                      {ragLoading ? (
                        <>
                          <span className="spinner mr-2"></span>
                          Processing...
                        </>
                      ) : (
                        <>
                          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          Ask
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>

              {ragResponse && (
                <div className="space-y-4 animate-slide-in-up">
                  <div className="card p-6 border-l-4 border-indigo-500">
                    <div className="flex items-start space-x-3 mb-4">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                          <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">Answer</h3>
                        <p className="text-gray-700 leading-relaxed whitespace-pre-line">{ragResponse.answer}</p>
                      </div>
                    </div>
                  </div>

                  {ragResponse.sources.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                        <svg className="w-5 h-5 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Sources ({ragResponse.sources.length})
                      </h3>
                      <div className="space-y-3">
                        {ragResponse.sources.map((source, idx) => (
                          <div key={idx} className="card p-4 hover:shadow-md transition-shadow">
                            <div className="flex items-start space-x-3">
                              <div className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                                <span className="text-sm font-semibold text-gray-600">{idx + 1}</span>
                              </div>
                              <div className="flex-1">
                                <p className="font-medium text-sm text-indigo-600 mb-2">
                                  {source.filename}
                                </p>
                                <p className="text-sm text-gray-700 leading-relaxed bg-gray-50 p-3 rounded">
                                  {source.chunk_content.substring(0, 200)}...
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <button
                    onClick={() => {
                      setRagResponse(null);
                      setRagQuery('');
                    }}
                    className="text-sm text-indigo-600 hover:text-indigo-700"
                  >
                    Ask another question
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
        </main>
      </div>

      {/* Preview Modal */}
      {showPreviewModal && previewData && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col animate-scale-in">
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Document Preview</h2>
                  <p className="text-sm text-gray-600">{previewData.original_filename}</p>
                </div>
              </div>
              <button
                onClick={closePreviewModal}
                className="w-10 h-10 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                aria-label="Close preview"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <span className="badge bg-indigo-100 text-indigo-800">
                      {previewData.file_type.toUpperCase()}
                    </span>
                    <span className="text-sm text-gray-600">
                      {previewData.preview_length.toLocaleString()} characters
                    </span>
                  </div>
                </div>
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <pre className="whitespace-pre-wrap text-sm text-gray-800 leading-relaxed font-sans">
                    {previewData.content}
                  </pre>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50 rounded-b-2xl">
              <button
                onClick={closePreviewModal}
                className="btn btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Document Modal */}
      {showEditModal && editingDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col animate-scale-in">
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h2 className="text-xl font-bold text-gray-900">Edit Document</h2>
                  <p className="text-sm text-gray-600">{editingDocument.original_filename}</p>
                </div>
                <button
                  onClick={() => {
                    handleViewVersions(editingDocument);
                    closeEditModal();
                  }}
                  className="px-3 py-1.5 text-sm text-purple-600 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors flex items-center"
                  title="View version history"
                >
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  History
                </button>
              </div>
              <button
                onClick={closeEditModal}
                className="w-10 h-10 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                aria-label="Close edit modal"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6">
              <form onSubmit={handleSaveEdit} className="space-y-4">
                <div>
                  <label htmlFor="edit-description" className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    id="edit-description"
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Document description"
                  />
                </div>

                <div>
                  <label htmlFor="edit-tags" className="block text-sm font-medium text-gray-700 mb-2">
                    Tags (comma separated)
                  </label>
                  <input
                    id="edit-tags"
                    type="text"
                    value={editTags}
                    onChange={(e) => setEditTags(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="tag1, tag2, tag3"
                  />
                </div>

                <div>
                  <label htmlFor="edit-visibility" className="block text-sm font-medium text-gray-700 mb-2">
                    Visibility
                  </label>
                  <select
                    id="edit-visibility"
                    value={editIsPublic}
                    onChange={(e) => setEditIsPublic(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="private">Private</option>
                    <option value="public">Public</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="edit-file" className="block text-sm font-medium text-gray-700 mb-2">
                    Replace File (Optional)
                  </label>
                  <input
                    id="edit-file"
                    type="file"
                    accept=".pdf,.docx,.doc"
                    onChange={(e) => setEditFile(e.target.files?.[0] || null)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Upload a new file to replace the current one. Leave empty to update only metadata.
                  </p>
                </div>
              </form>
            </div>

            {/* Modal Footer */}
            <div className="flex justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50 rounded-b-2xl">
              <button
                onClick={closeEditModal}
                className="btn btn-secondary"
                disabled={editLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                className="btn btn-primary"
                disabled={editLoading}
              >
                {editLoading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Version History Modal */}
      {showVersionModal && selectedDocumentForVersions && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col animate-scale-in">
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Version History</h2>
                  <p className="text-sm text-gray-600">{selectedDocumentForVersions.original_filename}</p>
                </div>
              </div>
              <button
                onClick={closeVersionModal}
                className="w-10 h-10 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                aria-label="Close version history"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6">
              {versionsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                </div>
              ) : versions.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500">No version history available</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {versions.map((version) => (
                    <div key={version.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <span className="badge bg-purple-100 text-purple-800">
                              Version {version.version_number}
                            </span>
                            <span className="text-sm text-gray-600">
                              {new Date(version.created_at).toLocaleString()}
                            </span>
                          </div>
                          {version.change_summary && (
                            <p className="text-sm text-gray-700 mb-2">{version.change_summary}</p>
                          )}
                          {version.description && (
                            <p className="text-xs text-gray-600 mb-2">Description: {version.description}</p>
                          )}
                          {version.tags_snapshot && version.tags_snapshot.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {version.tags_snapshot.map((tag, idx) => (
                                <span key={idx} className="badge bg-gray-100 text-gray-600 text-xs">
                                  #{tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => handleRollback(version.id)}
                          className="btn btn-sm btn-secondary ml-4"
                          title="Rollback to this version"
                        >
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                          </svg>
                          Rollback
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50 rounded-b-2xl">
              <button
                onClick={closeVersionModal}
                className="btn btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
