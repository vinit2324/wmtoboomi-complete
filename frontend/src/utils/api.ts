import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:7201';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// API functions
export const customersApi = {
  list: () => api.get('/api/customers'),
  get: (id: string) => api.get(`/api/customers/${id}`),
  create: (data: { customerName: string; settings?: unknown }) => 
    api.post('/api/customers', data),
  update: (id: string, data: unknown) => api.put(`/api/customers/${id}`, data),
  delete: (id: string) => api.delete(`/api/customers/${id}`),
  testBoomi: (id: string) => api.post(`/api/customers/${id}/test-boomi`),
  testLlm: (id: string) => api.post(`/api/customers/${id}/test-llm`),
};

export const projectsApi = {
  list: (customerId?: string) => 
    api.get('/api/projects', { params: customerId ? { customerId } : {} }),
  get: (id: string) => api.get(`/api/projects/${id}`),
  upload: (customerId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('customerId', customerId);
    return api.post('/api/projects', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  parse: (id: string) => api.post(`/api/projects/${id}/parse`),
  analyze: (id: string) => api.post(`/api/projects/${id}/analyze`),
  delete: (id: string) => api.delete(`/api/projects/${id}`),
  getFileTree: (id: string) => api.get(`/api/projects/${id}/files`),
  getFileContent: (projectId: string, filePath: string) => 
    api.get(`/api/projects/${projectId}/files/${filePath}`, { responseType: 'text' }),
};

export const conversionsApi = {
  list: (projectId: string) => 
    api.get('/api/conversions', { params: { projectId } }),
  get: (id: string) => api.get(`/api/conversions/${id}`),
  convert: (data: { projectId: string; sourceName: string; sourceType: string }) =>
    api.post('/api/conversions', data),
  convertAll: (projectId: string, customerId: string) =>
    api.post('/api/conversions/convert-all', { projectId, customerId }),
  push: (id: string) => api.post(`/api/conversions/${id}/push`),
  pushAll: (projectId: string, customerId: string) =>
    api.post('/api/conversions/push-all', null, { params: { projectId, customerId } }),
};

export const mappingsApi = {
  list: (projectId: string) => 
    api.get('/api/mappings', { params: { projectId } }),
  get: (id: string) => api.get(`/api/mappings/${id}`),
  create: (data: unknown) => api.post('/api/mappings', data),
  update: (id: string, data: unknown) => api.put(`/api/mappings/${id}`, data),
  delete: (id: string) => api.delete(`/api/mappings/${id}`),
  suggest: (id: string) => api.post(`/api/mappings/${id}/suggest`),
};

export const aiApi = {
  chat: (data: {
    customerId: string;
    projectId?: string;
    message: string;
    conversationHistory?: unknown[];
    includeContext?: boolean;
  }) => api.post('/api/ai/chat', data),
  generateGroovy: (customerId: string, data: {
    javaCode: string;
    serviceName: string;
    description?: string;
  }) => api.post('/api/ai/generate-groovy', data, { params: { customerId } }),
  mapWmPublic: (customerId: string, data: {
    serviceName: string;
    context?: string;
  }) => api.post('/api/ai/map-wmpublic', data, { params: { customerId } }),
};

export const logsApi = {
  list: (params?: {
    customerId?: string;
    projectId?: string;
    level?: string;
    category?: string;
    limit?: number;
    offset?: number;
  }) => api.get('/api/logs', { params }),
};

export const healthApi = {
  check: () => api.get('/api/health'),
};
