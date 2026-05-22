// API configuration
// In production (Docker), use empty string to make requests relative to current domain (Nginx proxy)
// In development, use localhost:8000 to connect directly to backend
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL !== undefined 
  ? import.meta.env.VITE_API_BASE_URL 
  : 'http://localhost:8000';
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL !== undefined 
  ? import.meta.env.VITE_WS_BASE_URL 
  : 'ws://localhost:8000';

// API endpoints
export const API_ENDPOINTS = {
  // Auth
  AUTH: {
    LOGIN: '/api/auth/dingtalk/login',
    CALLBACK: '/api/auth/dingtalk/callback',
    ME: '/api/auth/me',
  },
  // Contracts
  CONTRACTS: {
    LIST: '/api/contracts',
    DETAIL: (id: string) => `/api/contracts/${id}`,
    CREATE: '/api/contracts',
    REVIEWS: (id: string) => `/api/contracts/${id}/reviews`,
    APPROVE: (contractId: string, reviewId: string) =>
      `/api/contracts/${contractId}/reviews/${reviewId}/approve`,
    COMMENTS: (id: string) => `/api/contracts/${id}/comments`,
    ATTACHMENTS: (id: string) => `/api/contracts/${id}/attachments`,
  },
  // Reviews
  REVIEWS: {
    LIKE: (id: string) => `/api/reviews/${id}/like`,
  },
  // Comments
  COMMENTS: {
    LIKE: (id: string) => `/api/comments/${id}/like`,
  },
  // Attachments
  ATTACHMENTS: {
    DOWNLOAD: (id: string) => `/api/attachments/${id}/download`,
  },
  // AI
  AI: {
    SUMMARY: (contractId: string) => `/api/ai/summary/${contractId}`,
    ADVISOR: '/api/ai/advisor',
  },
};
