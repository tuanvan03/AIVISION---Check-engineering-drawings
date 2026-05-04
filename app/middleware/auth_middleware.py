import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

# Simple in-memory storage for brute force protection
# Format: { "ip_address": {"count": X, "lock_until": timestamp} }
FAILED_LOGIN_ATTEMPTS = {}
MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION_SECONDS = 15 * 60

logger = logging.getLogger("auth_middleware")

class BruteForceProtectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # We only apply brute force protection on the login endpoint
        if request.url.path == "/api/v1/auth/login" and request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"
            
            if client_ip in FAILED_LOGIN_ATTEMPTS:
                attempt_info = FAILED_LOGIN_ATTEMPTS[client_ip]
                
                # Check if IP is currently locked
                if attempt_info.get("lock_until") and time.time() < attempt_info["lock_until"]:
                    # Currently locked
                    return JSONResponse(
                        status_code=429,
                        content={"error": {"code": "TOO_MANY_REQUESTS", "message": "Quá nhiều lần đăng nhập thất bại. Vui lòng thử lại sau 15 phút."}}
                    )
                
                # If lock expired, reset
                if attempt_info.get("lock_until") and time.time() >= attempt_info["lock_until"]:
                    FAILED_LOGIN_ATTEMPTS[client_ip] = {"count": 0, "lock_until": None}
                    
        response = await call_next(request)
        
        # We need a way to increment failed attempts when login fails.
        # Since response is already formed, we inspect the status code for login endpoints.
        if request.url.path == "/api/v1/auth/login" and request.method == "POST":
            if response.status_code == 401 or response.status_code == 400:
                client_ip = request.client.host if request.client else "unknown"
                if client_ip not in FAILED_LOGIN_ATTEMPTS:
                    FAILED_LOGIN_ATTEMPTS[client_ip] = {"count": 1, "lock_until": None}
                else:
                    FAILED_LOGIN_ATTEMPTS[client_ip]["count"] += 1
                    
                if FAILED_LOGIN_ATTEMPTS[client_ip]["count"] >= MAX_FAILED_ATTEMPTS:
                    FAILED_LOGIN_ATTEMPTS[client_ip]["lock_until"] = time.time() + LOCK_DURATION_SECONDS
                    logger.warning(f"Event: ip_blocked. IP {client_ip} has been blocked for {LOCK_DURATION_SECONDS} seconds.")
                    
            elif response.status_code == 200:
                # Reset on successful login
                client_ip = request.client.host if request.client else "unknown"
                if client_ip in FAILED_LOGIN_ATTEMPTS:
                    FAILED_LOGIN_ATTEMPTS[client_ip] = {"count": 0, "lock_until": None}
                    
        return response
