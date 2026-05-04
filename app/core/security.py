from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt
import hashlib
from app.core.config import settings

def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(user_id: int, role: str, expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    
    to_encode = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_ws_token(user_id: int, ttl_seconds: int = 60) -> str:
    """
    Create a short-lived JWT exclusively for WebSocket authentication.
    TTL defaults to 60 seconds — just enough to complete the WS handshake.
    The token only contains 'sub' (no role) to minimize exposure.
    """
    expire = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    to_encode = {
        "sub": str(user_id),
        "type": "ws",  # Mark as WS-only token
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
