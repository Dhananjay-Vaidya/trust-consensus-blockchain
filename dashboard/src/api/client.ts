import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/',
  timeout: 30_000,
});

apiClient.interceptors.request.use((config) => {
  config.headers['X-Request-ID'] = crypto.randomUUID();
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      console.warn('[API] Network error — backend may be offline');
    }
    return Promise.reject(error);
  },
);
