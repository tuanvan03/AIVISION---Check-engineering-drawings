from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.quota_service import QuotaService, QuotaExceededError

async def check_quota(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.is_admin:
        return True
        
    quota_service = QuotaService(db)
    await quota_service.check_and_increment(current_user.id)
        
    return True
