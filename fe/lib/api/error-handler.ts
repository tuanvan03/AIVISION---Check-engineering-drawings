export class ApiError extends Error {
  status?: number;
  data?: any;

  constructor(message: string, status?: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export function handleApiError(error: any): string {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 401:
        return 'Session expired. Please log in again.';
      case 403:
        return 'Access denied. You do not have permission.';
      case 404:
        return 'Resource not found.';
      case 422:
        if (error.data && Array.isArray(error.data.detail)) {
          return error.data.detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join(', ');
        }
        return 'Validation error. Please check your inputs.';
      case 429:
        return 'Too many requests. Please try again later.';
      case 500:
        return 'Something went wrong. Please try again later.';
      default:
        return error.message || 'An unexpected error occurred.';
    }
  }

  if (error.name === 'TypeError' || error.message.includes('NetworkError') || error.message.includes('fetch')) {
    return 'Network error. Please check your connection.';
  }

  if (error.name === 'AbortError') {
    return 'Request timed out. Please try again.';
  }

  return error.message || 'Unknown error occurred.';
}
