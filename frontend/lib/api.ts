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

// Auth APIs
export const login = async (data: LoginData) => {
  const formData = new FormData();
  formData.append('username', data.username);
  formData.append('password', data.password);
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

export const deleteDocument = async (id: number) => {
  const response = await api.delete(`/api/documents/${id}`);
  return response.data;
};

export const getTags = async () => {
  const response = await api.get('/api/documents/tags/all');
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
