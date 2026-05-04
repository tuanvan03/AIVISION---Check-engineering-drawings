from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from app.dependencies.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.models.analysis import AnalysisHistory
from app.services.auth_service import AuthService
from app.services.quota_service import QuotaService
from app.services.log_service import LogService
from app.schemas.admin import (
    StatsResponse, AdminUserListResponse, AdminUserDetailResponse,
    UpdateUserRoleRequest, UpdateQuotaRequest, LogQueryParams, LogListResponse
)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

def _day_range(days_ago: int = 0):
    """Return (start, end) datetime for a day offset from today (UTC)."""
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_ago)
    end = start + timedelta(days=1)
    return start, end

@router.get("/stats", response_model=StatsResponse, dependencies=[Depends(require_admin)])
async def get_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    today_start, _ = _day_range(0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0

    analyses_today = (await db.execute(
        select(func.count(AnalysisHistory.id)).where(AnalysisHistory.created_at >= today_start)
    )).scalar() or 0

    analyses_this_month = (await db.execute(
        select(func.count(AnalysisHistory.id)).where(AnalysisHistory.created_at >= month_start)
    )).scalar() or 0

    active_users_7d = (await db.execute(
        select(func.count(func.distinct(AnalysisHistory.user_id)))
        .where(AnalysisHistory.created_at >= week_ago)
    )).scalar() or 0

    return StatsResponse(
        total_users=total_users,
        active_users_7d=active_users_7d,
        analyses_today=analyses_today,
        analyses_this_month=analyses_this_month,
    )

@router.get("/stats/chart", dependencies=[Depends(require_admin)])
async def get_stats_chart(db: AsyncSession = Depends(get_db)):
    labels = []
    data = []
    for i in range(30, -1, -1):
        day_start, day_end = _day_range(i)
        count = (await db.execute(
            select(func.count(AnalysisHistory.id)).where(
                AnalysisHistory.created_at >= day_start,
                AnalysisHistory.created_at < day_end,
            )
        )).scalar() or 0
        labels.append(day_start.strftime("%Y-%m-%d"))
        data.append(count)
    return {"labels": labels, "data": data}

@router.get("/users", dependencies=[Depends(require_admin)])
async def list_users(
    search: str = None, 
    page: int = Query(1, ge=1), 
    page_size: int = Query(20, ge=1),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).order_by(User.created_at.desc())
    if search:
        stmt = stmt.where(User.email.ilike(f"%{search}%") | User.display_name.ilike(f"%{search}%"))
        
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return [AdminUserListResponse.model_validate(u) for u in users]

@router.post("/users/{user_id}/lock", dependencies=[Depends(require_admin)])
async def lock_user(user_id: int, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    await auth_service.lock_user(user_id)
    return {"message": "Đã khoá tài khoản"}

@router.post("/users/{user_id}/unlock", dependencies=[Depends(require_admin)])
async def unlock_user(user_id: int, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    await auth_service.unlock_user(user_id)
    return {"message": "Đã mở khoá tài khoản"}

@router.put("/users/{user_id}/role", dependencies=[Depends(require_admin)])
async def change_role(user_id: int, request: UpdateUserRoleRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    await auth_service.change_role(user_id, request.role)
    return {"message": "Đã đổi quyền"}

@router.put("/users/{user_id}/quota", dependencies=[Depends(require_admin)])
async def update_quota(user_id: int, request: UpdateQuotaRequest, db: AsyncSession = Depends(get_db)):
    quota_service = QuotaService(db)
    await quota_service.set_max_requests(user_id, request.max_requests)
    return {"message": "Đã cập nhật quota"}

@router.get("/logs", dependencies=[Depends(require_admin)])
async def get_logs(
    user_id: int = None,
    event_type: str = None,
    severity: str = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1),
    db: AsyncSession = Depends(get_db)
):
    log_service = LogService(db)
    filters = {}
    if user_id: filters["user_id"] = user_id
    if event_type: filters["event_type"] = event_type
    if severity: filters["severity"] = severity
    
    logs = await log_service.query_logs(limit=page_size, offset=(page-1)*page_size, **filters)
    return [LogListResponse.model_validate(l) for l in logs]

@router.get("/logs/export", dependencies=[Depends(require_admin)])
async def export_logs(
    date_from: str = Query(...), 
    date_to: str = Query(...), 
    db: AsyncSession = Depends(get_db)
):
    log_service = LogService(db)
    try:
        from_dt = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
        to_dt = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO 8601")
        
    async def log_generator():
        async for chunk in log_service.export_csv(from_dt, to_dt):
            yield chunk

    return StreamingResponse(
        log_generator(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=logs_{date_from[:10]}.csv"}
    )
