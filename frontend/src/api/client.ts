import axios, { AxiosError, AxiosInstance } from 'axios';
import { getInitData } from '@/utils/telegram';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Get token auth params from URL
function getTokenAuth(): { uid: string; token: string } | null {
  const params = new URLSearchParams(window.location.search);
  const uid = params.get('uid');
  const token = params.get('token');
  if (uid && token) {
    return { uid, token };
  }
  return null;
}

// Add auth header to all requests
apiClient.interceptors.request.use((config) => {
  const initData = getInitData();
  
  if (initData) {
    // Method 1: initData from inline button / menu button
    config.headers['X-Telegram-Init-Data'] = initData;
  } else {
    // Method 2: token from reply keyboard button URL
    const tokenAuth = getTokenAuth();
    if (tokenAuth) {
      config.headers['X-Telegram-Id'] = tokenAuth.uid;
      config.headers['X-Telegram-Token'] = tokenAuth.token;
    }
  }
  
  return config;
});

// Handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail: string }>) => {
    const message = error.response?.data?.detail || error.message || 'Произошла ошибка';
    console.error('API Error:', message);
    return Promise.reject(new Error(message));
  }
);

export default apiClient;

