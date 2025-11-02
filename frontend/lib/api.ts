import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface LoginData {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
}

export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  upload_date: string;
  owner_id: number;
  description: string | null;
  is_public: string;
  tags: Tag[];
  last_modified?: string;
  version?: number;
}

export interface Tag {
  id: number;
  name: string;
}

export interface SearchResult {
  document_id: number;
  filename: string;
  chunk_content: string;
  score: number;
  document: Document;
}

export interface RAGResponse {
  answer: string;
  sources: SearchResult[];
}

export interface DocumentPreview {
  document_id: number;
  original_filename: string;
  file_type: string;
  content: string;
  preview_length: number;
}

export interface DocumentUpdate {
  description?: string;
  tags?: string[];
  is_public?: string;
}

export interface DocumentVersion {
  id: number;
  document_id: number;
  version_number: number;
  description?: string;
  tags_snapshot?: string[];
  is_public_snapshot: string;
  created_at: string;
  created_by_id: number;
  change_summary?: string;
}

export interface DocumentShare {
  id: number;
  document_id: number;
  user_id: number;
  permission: string;
  shared_at: string;
  shared_by_id: number;
  user: {
    id: number;
    username: string;
    email: string;
  };
}

export interface RecentView {
  id: number;
  action: string;
  timestamp: string;
  user_id?: number;
}

export interface DocumentStats {
  document_id: number;
  total_views: number;
  total_downloads: number;
  total_search_hits: number;
  unique_viewers: number;
  recent_views: RecentView[];
}

export interface DocumentFavorite {
  id: number;
  document_id: number;
  user_id: number;
  created_at: string;
}

// Auth APIs
export const login = async (data: LoginData, rememberMe: boolean = false) => {
  const formData = new FormData();
  formData.append('username', data.username);
  formData.append('password', data.password);
  formData.append('remember_me', rememberMe.toString());
  const response = await api.post('/api/auth/login', formData);
  return response.data;
};

export const register = async (data: RegisterData) => {
  const response = await api.post('/api/auth/register', data);
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get('/api/auth/me');
  return response.data;
};

// Document APIs
export const uploadDocument = async (file: File, description: string, tags: string, isPublic: string) => {
  const formData = new FormData();
  formData.append('file', file);
  if (description) formData.append('description', description);
  if (tags) formData.append('tags', tags);
  formData.append('is_public', isPublic);
  
  const response = await api.post('/api/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getDocuments = async (skip: number = 0, limit: number = 20) => {
  const response = await api.get(`/api/documents/?skip=${skip}&limit=${limit}`);
  return response.data;
};

export const getDocument = async (id: number) => {
  const response = await api.get(`/api/documents/${id}`);
  return response.data;
};

export const updateDocument = async (id: number, data: DocumentUpdate) => {
  const response = await api.put(`/api/documents/${id}`, data);
  return response.data;
};

export const deleteDocument = async (id: number) => {
  const response = await api.delete(`/api/documents/${id}`);
  return response.data;
};

export const previewDocument = async (id: number) => {
  const response = await api.get(`/api/documents/${id}/preview`);
  return response.data;
};

export const getTags = async () => {
  const response = await api.get('/api/documents/tags/all');
  return response.data;
};

// Version APIs
export const getDocumentVersions = async (id: number) => {
  const response = await api.get(`/api/documents/${id}/versions`);
  return response.data;
};

export const rollbackToVersion = async (docId: number, versionId: number) => {
  const response = await api.post(`/api/documents/${docId}/versions/${versionId}/rollback`);
  return response.data;
};

// Share APIs
export const shareDocument = async (docId: number, userId: number, permission: string) => {
  const response = await api.post(`/api/documents/${docId}/share`, {
    user_id: userId,
    permission,
  });
  return response.data;
};

export const getDocumentShares = async (docId: number) => {
  const response = await api.get(`/api/documents/${docId}/shares`);
  return response.data;
};

export const removeDocumentShare = async (shareId: number) => {
  const response = await api.delete(`/api/documents/shares/${shareId}`);
  return response.data;
};

export const getSharedDocuments = async () => {
  const response = await api.get('/api/documents/shared-with-me');
  return response.data;
};

// Analytics APIs
export const trackDocumentView = async (docId: number) => {
  const response = await api.post(`/api/documents/${docId}/analytics/view`);
  return response.data;
};

export const trackDocumentDownload = async (docId: number) => {
  const response = await api.post(`/api/documents/${docId}/analytics/download`);
  return response.data;
};

export const getDocumentAnalytics = async (docId: number, days: number = 30) => {
  const response = await api.get(`/api/documents/${docId}/analytics?days=${days}`);
  return response.data;
};

export const getPopularDocuments = async (limit: number = 10, days: number = 30) => {
  const response = await api.get(`/api/documents/analytics/popular?limit=${limit}&days=${days}`);
  return response.data;
};

// Favorite APIs
export const addToFavorites = async (docId: number) => {
  const response = await api.post(`/api/documents/${docId}/favorite`);
  return response.data;
};

export const removeFromFavorites = async (docId: number) => {
  const response = await api.delete(`/api/documents/${docId}/favorite`);
  return response.data;
};

export const getFavorites = async () => {
  const response = await api.get('/api/documents/favorites');
  return response.data;
};

// Bulk Operations APIs
export const bulkUpdateDocuments = async (documentIds: number[], updates: DocumentUpdate) => {
  const response = await api.post('/api/documents/bulk/update', {
    document_ids: documentIds,
    updates,
  });
  return response.data;
};

export const bulkShareDocuments = async (documentIds: number[], userId: number, permission: string) => {
  const response = await api.post('/api/documents/bulk/share', {
    document_ids: documentIds,
    user_id: userId,
    permission,
  });
  return response.data;
};

// Export APIs
export const exportDocumentsJSON = async (documentIds: number[]) => {
  const response = await api.post('/api/documents/export/json', {
    document_ids: documentIds,
    format: 'json',
  });
  return response.data;
};

export const exportDocumentsZIP = async (documentIds: number[]) => {
  const response = await api.post('/api/documents/export/zip', {
    document_ids: documentIds,
    format: 'zip',
  }, {
    responseType: 'blob',
  });
  return response.data;
};

export const exportDocumentsCSV = async (documentIds: number[]) => {
  const response = await api.post('/api/documents/export/csv', {
    document_ids: documentIds,
    format: 'csv',
  }, {
    responseType: 'blob',
  });
  return response.data;
};

// Search APIs
export const semanticSearch = async (query: string, topK: number = 5) => {
  const response = await api.post('/api/search/semantic', { query, top_k: topK });
  return response.data;
};

export const ragSearch = async (query: string, topK: number = 3) => {
  const response = await api.post('/api/search/rag', { query, top_k: topK });
  return response.data;
};

export default api;
