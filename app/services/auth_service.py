from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.models.session import UserSession
from app.services.log_service import LogService
from app.core.security import hash_password, verify_password, create_access_token, hash_token
from app.core.config import settings

class AuthError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.log_service = LogService(db)

    async def register(self, email: str, password: str, display_name: str) -> User:
        if len(password) < 8:
            raise AuthError("Mật khẩu phải có ít nhất 8 ký tự")
            
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise AuthError("Email đã được sử dụng")
            
        new_user = User(
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
            role="user",
            is_active=True
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        
        await self.log_service.log(
            event_type="register",
            severity="INFO",
            user_id=new_user.id,
            details={"email": email}
        )
        
        return new_user

    async def register_oauth(self, provider: str, oauth_id: str, email: str, display_name: str) -> User:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            user.oauth_provider = provider
            user.oauth_id = oauth_id
            await self.db.commit()
        else:
            user = User(
                email=email,
                password_hash=None,
                display_name=display_name,
                role="user",
                is_active=True,
                oauth_provider=provider,
                oauth_id=oauth_id
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            await self.log_service.log(
                event_type="register",
                severity="INFO",
                user_id=user.id,
                details={"email": email, "oauth": provider}
            )
            
        return user

    async def login(self, email: str, password: str, ip_address: str = None) -> str:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.password_hash or not verify_password(password, user.password_hash):
            await self.log_service.log(
                event_type="login_failed",
                severity="WARNING",
                ip_address=ip_address,
                details={"email": email}
            )
            raise AuthError("Email hoặc mật khẩu không đúng", status_code=status.HTTP_401_UNAUTHORIZED)
            
        if not user.is_active:
            raise AuthError("Tài khoản của bạn đã bị khóa", status_code=status.HTTP_403_FORBIDDEN)
            
        token = create_access_token(user_id=user.id, role=user.role)
        
        # Save session
        session = UserSession(
            user_id=user.id,
            jwt_token_hash=hash_token(token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
        )
        self.db.add(session)
        await self.db.commit()
        
        await self.log_service.log(
            event_type="login_success",
            severity="INFO",
            user_id=user.id,
            ip_address=ip_address
        )
        
        return token

    async def logout(self, token: str, user_id: int):
        token_hash = hash_token(token)
        stmt = select(UserSession).where(UserSession.jwt_token_hash == token_hash)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if session:
            await self.db.delete(session)
            await self.db.commit()
            
        await self.log_service.log(
            event_type="logout",
            severity="INFO",
            user_id=user_id
        )

    async def get_user_by_id(self, user_id: int) -> User:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise AuthError("Không tìm thấy người dùng", status_code=status.HTTP_404_NOT_FOUND)
        return user

    async def change_password(self, user_id: int, current_password: str, new_password: str):
        if len(new_password) < 8:
            raise AuthError("Mật khẩu mới phải có ít nhất 8 ký tự")
            
        user = await self.get_user_by_id(user_id)
        if not user.password_hash or not verify_password(current_password, user.password_hash):
            raise AuthError("Mật khẩu hiện tại không đúng", status_code=status.HTTP_400_BAD_REQUEST)
            
        user.password_hash = hash_password(new_password)
        await self.db.commit()
        
        await self.log_service.log(
            event_type="password_changed",
            severity="INFO",
            user_id=user_id
        )

    async def set_password(self, user_id: int, new_password: str):
        if len(new_password) < 8:
            raise AuthError("Mật khẩu mới phải có ít nhất 8 ký tự")
            
        user = await self.get_user_by_id(user_id)
        user.password_hash = hash_password(new_password)
        await self.db.commit()

    async def update_profile(self, user_id: int, display_name: str, avatar_url: str = None):
        user = await self.get_user_by_id(user_id)
        user.display_name = display_name
        if avatar_url is not None:
            user.avatar_url = avatar_url
        await self.db.commit()
        
        await self.log_service.log(
            event_type="profile_updated",
            severity="INFO",
            user_id=user_id
        )

    async def lock_user(self, user_id: int):
        user = await self.get_user_by_id(user_id)
        user.is_active = False
        await self.db.commit()
        
        await self.log_service.log(
            event_type="account_locked",
            severity="WARNING",
            user_id=user_id
        )

    async def unlock_user(self, user_id: int):
        user = await self.get_user_by_id(user_id)
        user.is_active = True
        await self.db.commit()
        
        await self.log_service.log(
            event_type="account_unlocked",
            severity="INFO",
            user_id=user_id
        )

    async def change_role(self, user_id: int, new_role: str):
        if new_role not in ["user", "admin"]:
            raise AuthError("Vai trò không hợp lệ")
            
        user = await self.get_user_by_id(user_id)
        user.role = new_role
        await self.db.commit()
        
        await self.log_service.log(
            event_type="role_changed",
            severity="WARNING",
            user_id=user_id,
            details={"new_role": new_role}
        )
