from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.dependencies.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService, AuthError
from app.schemas.auth import (
    RegisterRequest, LoginRequest, UserResponse, LoginResponse,
    ForgotPasswordRequest
)
from app.core.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Mật khẩu xác nhận không khớp")
        
    auth_service = AuthService(db)
    user = await auth_service.register(
        email=request.email,
        password=request.password,
        display_name=request.display_name
    )
    return user

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response, req: Request, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    client_ip = req.client.host if req.client else "unknown"
    
    token = await auth_service.login(email=request.email, password=request.password, ip_address=client_ip)
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.JWT_EXPIRE_HOURS * 3600,
        secure=settings.APP_ENV == "production"
    )
    
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    user = result.scalar_one()
    
    redirect_url = "/admin" if user.role == "admin" else ""
    
    return LoginResponse(
        user=UserResponse(id=user.id, email=user.email, display_name=user.display_name, role=user.role),
        redirect_url=redirect_url
    )

@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if token:
        auth_service = AuthService(db)
        await auth_service.logout(token, user_id=0)
        
    response.delete_cookie("access_token")
    return {"message": "Đăng xuất thành công"}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    return {"message": "Nếu email tồn tại, hướng dẫn đặt lại mật khẩu đã được gửi."}

@router.get("/oauth/{provider}")
async def oauth_login(provider: str):
    if settings.AUTH_MODE == "local":
        raise HTTPException(status_code=400, detail="OAuth is disabled in local mode")
    return {"message": f"Redirecting to {provider}"}

@router.get("/ws-token")
async def get_ws_token(request: Request):
    """
    Returns a short-lived JWT (60s TTL) dedicated to WebSocket authentication.
    The frontend fetches this token just before opening a WS connection and
    passes it as ?token=<ws_token> in the WebSocket URL.
    This avoids exposing the long-lived HttpOnly session token in URLs.
    """
    from jose import JWTError
    from app.core.security import decode_token, create_ws_token

    # Read the session cookie set by the login endpoint
    cookie_token = request.cookies.get("access_token")
    if not cookie_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa đăng nhập"
        )

    try:
        payload = decode_token(cookie_token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
        user_id = int(user_id_str)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")

    # Issue a fresh short-lived token scoped only for WS handshake
    ws_token = create_ws_token(user_id=user_id, ttl_seconds=60)
    return {"ws_token": ws_token}
