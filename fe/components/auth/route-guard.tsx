"use client"

import React, { useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { Loader2 } from "lucide-react"

interface ProtectedRouteProps {
  children: React.ReactNode
  /**
   * If true, this route requires authentication.
   * If false, authentication is optional (the page handles it itself).
   * @default true
   */
  requireAuth?: boolean
}

/**
 * ProtectedRoute – wraps pages that require authentication.
 * Redirects to /login?return_url=... if not authenticated.
 */
export function ProtectedRoute({
  children,
  requireAuth = true,
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    // Only redirect after loading is finished and we know user is not authenticated
    if (!isLoading && !isAuthenticated && requireAuth) {
      const returnUrl = encodeURIComponent(pathname)
      router.replace(`/login?return_url=${returnUrl}`)
    }
  }, [isLoading, isAuthenticated, requireAuth, router, pathname])

  // Show loading spinner while session is being validated
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Đang xác thực...</p>
        </div>
      </div>
    )
  }

  // If auth is required and user is not authenticated, don't render children
  // (they will be redirected by the useEffect above)
  if (requireAuth && !isAuthenticated) {
    return null
  }

  return <>{children}</>
}

// ---------- Admin Route ----------

interface AdminRouteProps {
  children: React.ReactNode
  /**
   * Custom redirect path for non-admin users
   * @default "/analysis"
   */
  redirectPath?: string
  /**
   * List of allowed roles. Defaults to ["admin"]
   */
  allowedRoles?: string[]
}

/**
 * AdminRoute – wraps admin-only pages.
 * Checks both authentication and role.
 * Redirects to /login if not authenticated, or to redirectPath if not admin.
 */
export function AdminRoute({
  children,
  redirectPath = "/analysis",
  allowedRoles = ["admin"],
}: AdminRouteProps) {
  const { user, isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (isLoading) return

    if (!isAuthenticated) {
      const returnUrl = encodeURIComponent(pathname)
      router.replace(`/login?return_url=${returnUrl}`)
      return
    }

    if (user && !allowedRoles.includes(user.role)) {
      // Log unauthorized access attempt for security monitoring
      if (process.env.NODE_ENV === "development") {
        console.warn(
          `[SECURITY] Unauthorized access attempt to ${pathname} by user ${user.email} (role: ${user.role})`
        )
      }
      router.replace(redirectPath)
    }
  }, [isLoading, isAuthenticated, user, allowedRoles, router, pathname, redirectPath])

  // Loading spinner while validating
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Đang xác thực...</p>
        </div>
      </div>
    )
  }

  // Not authenticated
  if (!isAuthenticated) return null

  // Not authorized
  if (user && !allowedRoles.includes(user.role)) return null

  return <>{children}</>
}
