import axios from 'axios';

// Constants
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const TOKEN_KEY = 'rizzume_token';

// -- Public API Client --
// Used for Login, Signup, Health checks that don't need a token
export const publicApi = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// -- Private API Client --
// Automatically attaches tokens and handles 401s
export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach Token
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle 401 (Unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Check if error is 401
    if (error.response && error.response.status === 401) {
      if (typeof window !== 'undefined') {
        // Clear token
        localStorage.removeItem(TOKEN_KEY);
        // Redirect to auth page if not already there
        if (!window.location.pathname.startsWith('/auth')) {
            window.location.href = '/auth?view=login&session_expired=true';
        }
      }
    }
    return Promise.reject(error);
  }
);
