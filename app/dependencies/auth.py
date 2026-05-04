from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.dependencies.database import get_db
from app.models.user import User
from app.models.session import UserSession
from app.core.security import decode_token, hash_token
from jose import JWTError

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        # Check authorization header as fallback
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    try:
        payload = decode_token(token)
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        user_id = int(user_id_str)
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
        
    # Verify token in sessions table
    token_hash = hash_token(token)
    stmt = select(UserSession).where(UserSession.jwt_token_hash == token_hash)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
        
    stmt_user = select(User).where(User.id == user_id)
    result_user = await db.execute(stmt_user)
    user = result_user.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
        
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Tài khoản của bạn đã bị khóa")
        
    return user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập trang này")
    return current_user
