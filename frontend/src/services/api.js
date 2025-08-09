import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// API service for all backend communication
export const api = {
  // Dashboard APIs
  async getDashboardData() {
    const [candidatesRes, jobsRes] = await Promise.all([
      axios.get(`${API}/candidates`),
      axios.get(`${API}/jobs`)
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
    const response = await axios.post(`${API}/resume`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  async getCandidates() {
    const response = await axios.get(`${API}/candidates`);
    return response.data;
  },

  async getCandidate(candidateId) {
    const response = await axios.get(`${API}/candidates/${candidateId}`);
    return response.data;
  },

  // Job APIs
  async createJob(jobData) {
    const response = await axios.post(`${API}/job`, jobData);
    return response.data;
  },

  async getJobs() {
    const response = await axios.get(`${API}/jobs`);
    return response.data;
  },

  async getJob(jobId) {
    const response = await axios.get(`${API}/jobs/${jobId}`);
    return response.data;
  },

  // Search API
  async searchCandidates(jobId, k = 10) {
    const response = await axios.get(`${API}/search?job_id=${jobId}&k=${k}`);
    return response.data;
  },

  // Status API
  async createStatusCheck(clientName) {
    const response = await axios.post(`${API}/status`, { client_name: clientName });
    return response.data;
  },

  async getStatusChecks() {
    const response = await axios.get(`${API}/status`);
    return response.data;
  }
};

export default api;