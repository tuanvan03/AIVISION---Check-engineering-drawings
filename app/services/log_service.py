from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from app.models.log import ActivityLog
from app.core.config import settings

class LogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, event_type: str, severity: str, user_id: Optional[int] = None, ip_address: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Tạo bản ghi log mới."""
        new_log = ActivityLog(
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            ip_address=ip_address,
            details=details,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(new_log)
        await self.db.commit()
        await self.db.refresh(new_log)
        return new_log

    async def query_logs(self, limit: int = 50, offset: int = 0, **filters) -> List[ActivityLog]:
        """Truy vấn log với các điều kiện."""
        stmt = select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit).offset(offset)
        
        # Áp dụng filters nếu có
        if filters.get("user_id") is not None:
            stmt = stmt.where(ActivityLog.user_id == filters["user_id"])
        if filters.get("event_type"):
            stmt = stmt.where(ActivityLog.event_type == filters["event_type"])
        if filters.get("severity"):
            stmt = stmt.where(ActivityLog.severity == filters["severity"])
            
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def export_csv(self, date_from: datetime, date_to: datetime):
        """Export logs trong khoảng thời gian ra dạng generator cho file CSV."""
        stmt = select(ActivityLog).where(
            ActivityLog.created_at >= date_from,
            ActivityLog.created_at <= date_to
        ).order_by(ActivityLog.created_at.desc())
        
        yield "id,user_id,event_type,severity,ip_address,created_at,details\n"
        
        result = await self.db.execute(stmt)
        for log in result.scalars():
            yield f"{log.id},{log.user_id},{log.event_type},{log.severity},{log.ip_address},{log.created_at},{log.details}\n"

    async def cleanup_old_logs(self, days: int = 90):
        """Xoá các log cũ hơn số ngày chỉ định."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = delete(ActivityLog).where(ActivityLog.created_at < cutoff_date)
        await self.db.execute(stmt)
        await self.db.commit()
