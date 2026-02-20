import axios, { AxiosError, AxiosInstance } from 'axios';
import { getInitData, getTokenAuth } from '@/utils/telegram';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth header to all requests
apiClient.interceptors.request.use((config) => {
  const initData = getInitData();
  
  if (initData) {
    // Method 1: initData from inline button / menu button (not empty)
    config.headers['X-Telegram-Init-Data'] = initData;
  } else {
    // Method 2: token auth from reply keyboard button URL (cached at startup)
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
  (error: AxiosError<{ detail: unknown }>) => {
    const detail = error.response?.data?.detail;
    let message: string;
    if (typeof detail === 'string') {
      message = detail;
    } else if (Array.isArray(detail) && detail.length > 0) {
      // Pydantic validation errors — берём первое сообщение
      const first = detail[0] as { msg?: string };
      message = first?.msg || JSON.stringify(detail);
    } else if (detail != null) {
      message = JSON.stringify(detail);
    } else {
      message = error.message || 'Произошла ошибка';
    }
    console.error('API Error:', message, error.response?.status);
    return Promise.reject(new Error(message));
  }
);

export default apiClient;

