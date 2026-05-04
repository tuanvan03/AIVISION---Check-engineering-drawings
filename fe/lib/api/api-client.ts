import { ApiError } from './error-handler';

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1';

interface FetchOptions extends RequestInit {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function fetchWithRetry(url: string, options: FetchOptions = {}): Promise<Response> {
  const { 
    timeout = 30000, 
    retries = 3, 
    retryDelay = 1000, 
    ...fetchOptions 
  } = options;

  let lastError: any;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      const response = await fetch(url, {
        ...fetchOptions,
        credentials: 'include', // Important for cookies
        signal: controller.signal as any,
      });
      
      clearTimeout(timeoutId);

      // Handle 429 Too Many Requests
      if (response.status === 429 && attempt < retries) {
        const retryAfter = response.headers.get('Retry-After');
        const delay = retryAfter ? parseInt(retryAfter) * 1000 : retryDelay * Math.pow(2, attempt);
        if (process.env.NODE_ENV === 'development') console.log(`Retry attempt ${attempt + 1} for ${url} after ${delay}ms`);
        await sleep(delay);
        continue;
      }

      // Retry on 5xx errors if GET request
      if (response.status >= 500 && attempt < retries && (!options.method || options.method.toUpperCase() === 'GET')) {
        const delay = retryDelay * Math.pow(2, attempt); // Exponential backoff
        if (process.env.NODE_ENV === 'development') console.log(`Retry attempt ${attempt + 1} for ${url} after ${delay}ms`);
        await sleep(delay);
        continue;
      }

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch (e) {
          errorData = { detail: response.statusText };
        }
        throw new ApiError(`Request failed: ${response.status}`, response.status, errorData);
      }

      return response;
    } catch (error: any) {
      lastError = error;
      
      // Retry on network errors or timeouts for GET requests
      const isNetworkError = error.name === 'TypeError' || error.message === 'Failed to fetch';
      const isTimeoutError = error.name === 'AbortError';
      const isGetRequest = !options.method || options.method.toUpperCase() === 'GET';

      if ((isNetworkError || isTimeoutError) && attempt < retries && isGetRequest) {
        const delay = retryDelay * Math.pow(2, attempt);
        if (process.env.NODE_ENV === 'development') console.log(`Retry attempt ${attempt + 1} for ${url} after ${delay}ms`);
        await sleep(delay);
        continue;
      }
      
      // If we shouldn't retry, break the loop
      if (attempt >= retries || !isGetRequest) {
        break;
      }
    }
  }

  throw lastError;
}

export const apiClient = {
  async get<T>(path: string, options?: FetchOptions): Promise<T> {
    const response = await fetchWithRetry(`${BASE_URL}${path}`, {
      ...options,
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
    return response.json();
  },

  async post<T>(path: string, data?: any, options?: FetchOptions): Promise<T> {
    const isFormData = data instanceof FormData;
    const headers: Record<string, string> = { ...options?.headers as Record<string, string> };
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetchWithRetry(`${BASE_URL}${path}`, {
      ...options,
      method: 'POST',
      headers,
      body: isFormData ? data : JSON.stringify(data),
    });
    return response.json();
  },

  async put<T>(path: string, data?: any, options?: FetchOptions): Promise<T> {
    const isFormData = data instanceof FormData;
    const headers: Record<string, string> = { ...options?.headers as Record<string, string> };
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetchWithRetry(`${BASE_URL}${path}`, {
      ...options,
      method: 'PUT',
      headers,
      body: isFormData ? data : JSON.stringify(data),
    });
    return response.json();
  },

  async delete(path: string, options?: FetchOptions): Promise<void> {
    await fetchWithRetry(`${BASE_URL}${path}`, {
      ...options,
      method: 'DELETE',
    });
  },
};
