from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserProfileResponse, UpdateProfileRequest, QuotaInfoResponse
from app.schemas.auth import ChangePasswordRequest, SetPasswordRequest
from app.services.auth_service import AuthService
from app.services.quota_service import QuotaService

router = APIRouter(prefix="/api/v1/users", tags=["Users"])

@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    quota_service = QuotaService(db)
    quota_info = None
    if not current_user.is_admin:
        usage = await quota_service.get_today_usage(current_user.id)
        quota_info = QuotaInfoResponse(
            used=usage.request_count,
            max=usage.max_requests,
            remaining=max(0, usage.max_requests - usage.request_count)
        )
        
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role,
        avatar_url=current_user.avatar_url,
        quota=quota_info
    )

@router.put("/me", response_model=UserProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    await auth_service.update_profile(current_user.id, request.display_name, request.avatar_url)
    
    updated_user = await auth_service.get_user_by_id(current_user.id)
    return await get_me(updated_user, db)

@router.post("/me/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    await auth_service.change_password(current_user.id, request.current_password, request.new_password)
    return {"message": "Đổi mật khẩu thành công"}

@router.post("/me/set-password")
async def set_password(
    request: SetPasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.password_hash:
        raise HTTPException(status_code=400, detail="Tài khoản này đã có mật khẩu. Hãy dùng chức năng đổi mật khẩu.")
        
    auth_service = AuthService(db)
    await auth_service.set_password(current_user.id, request.new_password)
    return {"message": "Thiết lập mật khẩu thành công"}
