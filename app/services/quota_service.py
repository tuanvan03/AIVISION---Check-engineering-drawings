from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.quota import QuotaUsage

class QuotaExceededError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Bạn đã sử dụng hết hạn mức phân tích hôm nay. Hạn mức sẽ được đặt lại vào lúc 00:00 ngày mai."
        )

class QuotaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_today_usage(self, user_id: int) -> QuotaUsage:
        """Lấy thông tin quota ngày hôm nay của user. Nếu chưa có, tạo mới."""
        today = datetime.now(timezone.utc).date()
        
        stmt = select(QuotaUsage).where(
            QuotaUsage.user_id == user_id,
            QuotaUsage.usage_date == today
        )
        result = await self.db.execute(stmt)
        usage = result.scalar_one_or_none()
        
        if not usage:
            usage = QuotaUsage(
                user_id=user_id,
                usage_date=today,
                request_count=0,
                max_requests=10
            )
            self.db.add(usage)
            await self.db.commit()
            await self.db.refresh(usage)
            
        return usage

    async def check_and_increment(self, user_id: int) -> dict:
        """Kiểm tra quota và tăng count. Dùng DB lock để tránh race condition."""
        today = datetime.now(timezone.utc).date()
        
        stmt = select(QuotaUsage).where(
            QuotaUsage.user_id == user_id,
            QuotaUsage.usage_date == today
        ).with_for_update()
        
        result = await self.db.execute(stmt)
        usage = result.scalar_one_or_none()
        
        if not usage:
            usage = QuotaUsage(user_id=user_id, usage_date=today, request_count=0, max_requests=10)
            self.db.add(usage)
            await self.db.flush()
            
        if usage.request_count >= usage.max_requests:
            await self.db.rollback()
            raise QuotaExceededError()
            
        usage.request_count += 1
        await self.db.commit()
        
        return {
            "used": usage.request_count,
            "max": usage.max_requests,
            "remaining": usage.max_requests - usage.request_count
        }

    async def get_remaining(self, user_id: int) -> dict:
        """Lấy số lượng request còn lại."""
        usage = await self.get_today_usage(user_id)
        return {
            "used": usage.request_count,
            "max": usage.max_requests,
            "remaining": max(0, usage.max_requests - usage.request_count)
        }

    async def reset_quota(self, user_id: int):
        """Admin đặt lại quota."""
        usage = await self.get_today_usage(user_id)
        usage.request_count = 0
        await self.db.commit()
        
    async def set_max_requests(self, user_id: int, max_requests: int):
        """Admin set hạn mức tuỳ chỉnh cho tài khoản."""
        usage = await self.get_today_usage(user_id)
        usage.max_requests = max_requests
        await self.db.commit()
