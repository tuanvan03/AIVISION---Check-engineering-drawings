import { apiClient } from './api-client';
import { handleApiError } from './error-handler';
import { 
  LoginRequest, 
  LoginResponse, 
  RegisterRequest, 
  RegisterResponse,
  UserResponse 
} from '../../types/api';

// Cache for getCurrentUser to avoid redundant requests
let currentUserCache: { data: UserResponse; timestamp: number } | null = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

export const authService = {
  async login(data: LoginRequest): Promise<LoginResponse> {
    try {
      return await apiClient.post<LoginResponse>('/auth/login', data);
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async register(data: RegisterRequest): Promise<RegisterResponse> {
    try {
      return await apiClient.post<RegisterResponse>('/auth/register', data);
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
      // We don't throw here to ensure local state can be cleaned up even if API fails
    }
  },

  async getCurrentUser(): Promise<UserResponse> {
    // Check cache first
    if (currentUserCache && (Date.now() - currentUserCache.timestamp) < CACHE_DURATION) {
      return currentUserCache.data;
    }

    try {
      const user = await apiClient.get<UserResponse>('/users/me');
      currentUserCache = { data: user, timestamp: Date.now() };
      return user;
    } catch (error: any) {
      // Don't cache 401 errors - user might login again
      if (error instanceof (await import('./error-handler')).ApiError && error.status === 401) {
        currentUserCache = null;
      }
      throw new Error(handleApiError(error));
    }
  },

  invalidateUserCache(): void {
    currentUserCache = null;
  },

  /**
   * Initiate Google OAuth login
   */
  initiateGoogleLogin(): void {
    window.location.href = `${process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1'}/auth/google`;
  },

  /**
   * Initiate GitHub OAuth login
   */
  initiateGitHubLogin(): void {
    window.location.href = `${process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1'}/auth/github`;
  },
};
