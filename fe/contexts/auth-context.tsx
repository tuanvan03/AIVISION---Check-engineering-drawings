"use client"

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
} from "react"
import { useRouter } from "next/navigation"
import { authService } from "@/lib/api/auth-service"
import type { UserResponse, LoginRequest, RegisterRequest } from "@/types/api"

// ---------- Types ----------

interface AuthState {
  user: UserResponse | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

interface AuthContextValue extends AuthState {
  login: (data: LoginRequest) => Promise<string | undefined>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  clearError: () => void
}

// ---------- Context ----------

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

// ---------- Broadcast Channel (cross-tab sync) ----------

const CHANNEL_NAME = "ai-vision-auth"
type AuthBroadcastEvent =
  | { type: "LOGIN"; user: UserResponse }
  | { type: "LOGOUT" }
  | { type: "SESSION_EXPIRED" }

function getBroadcastChannel(): BroadcastChannel | null {
  if (typeof window === "undefined") return null
  try {
    return new BroadcastChannel(CHANNEL_NAME)
  } catch {
    return null
  }
}

// ---------- Provider ----------

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true, // Start loading until session is validated
    error: null,
  })

  const channelRef = useRef<BroadcastChannel | null>(null)
  const validationPromiseRef = useRef<Promise<void> | null>(null)

  // ---------- Core actions ----------

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }))
  }, [])

  /**
   * Validate session by calling GET /api/v1/users/me
   */
  const validateSession = useCallback(async (): Promise<void> => {
    // Deduplicate concurrent validation calls
    if (validationPromiseRef.current) return validationPromiseRef.current

    validationPromiseRef.current = (async () => {
      try {
        const user = await authService.getCurrentUser()
        setState({
          user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        })
      } catch (error: any) {
        // 401 or any error means not authenticated
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        })
      }
    })()

    try {
      await validationPromiseRef.current
    } finally {
      validationPromiseRef.current = null
    }
  }, [])

  const login = useCallback(
    async (data: LoginRequest): Promise<string | undefined> => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }))
      try {
        const response = await authService.login(data)
        authService.invalidateUserCache()

        setState({
          user: response.user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        })

        // Broadcast login event to other tabs
        channelRef.current?.postMessage({
          type: "LOGIN",
          user: response.user,
        } satisfies AuthBroadcastEvent)

        return response.redirect_url
      } catch (error: any) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: error.message || "Đăng nhập thất bại",
        }))
        throw error
      }
    },
    []
  )

  const register = useCallback(
    async (data: RegisterRequest): Promise<void> => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }))
      try {
        await authService.register(data)
        authService.invalidateUserCache()

        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: null,
        }))
      } catch (error: any) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: error.message || "Đăng ký thất bại",
        }))
        throw error
      }
    },
    []
  )

  const logout = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }))

    try {
      await authService.logout()
    } catch (error) {
      console.error("Logout API error (continuing with local cleanup):", error)
    }

    // Always clear local state regardless of API success/failure
    authService.invalidateUserCache()
    sessionStorage.clear()

    setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    })

    // Broadcast logout event to other tabs
    channelRef.current?.postMessage({
      type: "LOGOUT",
    } satisfies AuthBroadcastEvent)
  }, [])

  const refreshUser = useCallback(async () => {
    try {
      authService.invalidateUserCache()
      const user = await authService.getCurrentUser()
      setState((prev) => ({
        ...prev,
        user,
        isAuthenticated: true,
        error: null,
      }))
    } catch (error: any) {
      // If 401, clear session
      setState((prev) => ({
        ...prev,
        user: null,
        isAuthenticated: false,
        error: error.message || "Phiên đăng nhập hết hạn",
      }))
    }
  }, [])

  // ---------- BroadcastChannel listener (cross-tab sync) ----------

  useEffect(() => {
    channelRef.current = getBroadcastChannel()

    if (channelRef.current) {
      channelRef.current.onmessage = (event: MessageEvent<AuthBroadcastEvent>) => {
        const { type } = event.data

        switch (type) {
          case "LOGIN": {
            const { user } = event.data
            setState((prev) => ({
              ...prev,
              user,
              isAuthenticated: true,
              error: null,
            }))
            break
          }
          case "LOGOUT":
          case "SESSION_EXPIRED": {
            authService.invalidateUserCache()
            sessionStorage.clear()
            setState({
              user: null,
              isAuthenticated: false,
              isLoading: false,
              error: null,
            })
            break
          }
        }
      }
    }

    return () => {
      channelRef.current?.close()
      channelRef.current = null
    }
  }, [])

  // ---------- Validate session on mount ----------

  useEffect(() => {
    validateSession()
  }, [validateSession])

  // ---------- Render ----------

  const value: AuthContextValue = {
    ...state,
    login,
    register,
    logout,
    refreshUser,
    clearError,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// ---------- Hook ----------

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
