import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Structured error extraction
    const status = error.response?.status;
    const detail = error.response?.data?.detail || error.message;

    if (status === 429) {
      console.warn('[API Client] Request rate limited (debounce):', detail);
    } else {
      console.error(`[API Client] Error (${status}):`, detail);
    }

    return Promise.reject(error);
  }
);

export async function request<T>(endpoint: string, options: any = {}): Promise<T> {
  try {
    const res = await apiClient({
      url: endpoint,
      method: options.method || 'GET',
      data: options.body ? (typeof options.body === 'string' ? JSON.parse(options.body) : options.body) : undefined,
      ...options,
    });
    return res.data;
  } catch (error) {
    throw error;
  }
}

