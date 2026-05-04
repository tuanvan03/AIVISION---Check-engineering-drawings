export interface UserResponse {
  id: number;
  email: string;
  display_name: string;
  role: string;
  avatar_url?: string | null;
  quota?: {
    used: number;
    max: number;
    remaining: number;
  };
}

export interface LoginRequest {
  email: string;
  password?: string;
}

export interface LoginResponse {
  user: UserResponse;
  redirect_url: string;
}

export interface RegisterRequest {
  email: string;
  password?: string;
  confirm_password?: string;
  display_name: string;
}

export interface RegisterResponse {
  id: number;
  email: string;
  display_name: string;
  role: string;
}

export interface ErrorResponse {
  detail: string | ValidationError[];
}

export interface ValidationError {
  loc: string[];
  msg: string;
  type: string;
}

export interface OAuthCallbackParams {
  code: string;
  state: string;
}
