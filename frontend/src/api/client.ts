import axios, { AxiosError } from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string | Array<{ msg?: string }> }>) => {
    const payload = error.response?.data;
    let message = error.message;
    if (payload?.detail) {
      if (typeof payload.detail === 'string') {
        message = payload.detail;
      } else if (Array.isArray(payload.detail)) {
        message = payload.detail
          .map((item) => (typeof item === 'string' ? item : item?.msg ?? ''))
          .filter(Boolean)
          .join('; ');
      }
    }
    const wrapped = new Error(message || '请求失败');
    (wrapped as Error & { status?: number }).status = error.response?.status;
    return Promise.reject(wrapped);
  },
);
