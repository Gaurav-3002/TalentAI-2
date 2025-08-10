import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Create axios instance with interceptors
const apiClient = axios.create({
  baseURL: API
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - clear auth data
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API service for all backend communication
export const api = {
  // Set auth token for API calls
  setAuthToken(token) {
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete apiClient.defaults.headers.common['Authorization'];
    }
  },

  // Authentication APIs
  async login(email, password) {
    const response = await apiClient.post('/auth/login', { email, password });
    return response.data;
  },

  async register(userData) {
    const response = await apiClient.post('/auth/register', userData);
    return response.data;
  },

  async getCurrentUser() {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  // Profile APIs
  async getProfile() {
    const response = await apiClient.get('/profile');
    return response.data;
  },

  // Applications
  async applyToJob(jobId) {
    const response = await apiClient.post('/applications', { job_id: jobId });
    return response.data;
  },

  // User Management APIs
  async getAllUsers() {
    const response = await apiClient.get('/users');
    return response.data;
  },

  async updateUserRole(userId, newRole) {
    const response = await apiClient.put(`/users/${userId}/role?new_role=${newRole}`);
    return response.data;
  },

  // Access Log APIs
  async getAccessLogs(limit = 100, candidateId = null) {
    let url = `/access-logs?limit=${limit}`;
    if (candidateId) url += `&candidate_id=${candidateId}`;
    const response = await apiClient.get(url);
    return response.data;
  },

  async createAccessLog(candidateId, accessReason, accessDetails = null) {
    const response = await apiClient.post('/access-logs', {
      candidate_id: candidateId,
      access_reason: accessReason,
      access_details: accessDetails
    });
    return response.data;
  },

  // Dashboard APIs
  async getDashboardData(blindMode = false) {
    const [candidatesRes, jobsRes] = await Promise.all([
      apiClient.get(`/candidates?blind_mode=${blindMode}`),
      apiClient.get('/jobs')
    ]);
    
    return {
      candidates: candidatesRes.data,
      jobs: jobsRes.data,
      stats: {
        candidatesCount: candidatesRes.data.length,
        jobsCount: jobsRes.data.length
      }
    };
  },

  // Candidate APIs
  async uploadResume(formData) {
    const response = await apiClient.post('/resume', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  async getCandidates(blindMode = false) {
    const response = await apiClient.get(`/candidates?blind_mode=${blindMode}`);
    return response.data;
  },

  async getCandidate(candidateId, blindMode = false) {
    const response = await apiClient.get(`/candidates/${candidateId}?blind_mode=${blindMode}`);
    return response.data;
  },

  // Job APIs
  async createJob(jobData) {
    const response = await apiClient.post('/job', jobData);
    return response.data;
  },

  async getJobs() {
    const response = await apiClient.get('/jobs');
    return response.data;
  },

  async getJob(jobId) {
    const response = await apiClient.get(`/jobs/${jobId}`);
    return response.data;
  },

  // Search API with blind screening support
  async searchCandidates(jobId, k = 10, blindScreening = false) {
    const response = await apiClient.get(`/search?job_id=${jobId}&k=${k}&blind_screening=${blindScreening}`);
    return response.data;
  },

  // Status API (keeping for backward compatibility)
  async createStatusCheck(clientName) {
    const response = await apiClient.post('/status', { client_name: clientName });
    return response.data;
  },

  async getStatusChecks() {
    const response = await apiClient.get('/status');
    return response.data;
  }
};

export default api;