from fastapi import APIRouter, Request, Depends, HTTPException, status
from app.core.config import settings
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.quota_service import QuotaService

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="app/templates")

async def get_optional_user(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user = await get_current_user(request, db)
        return user
    except HTTPException:
        return None

@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request, user: User = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    quota_info = None
    if not user.is_admin:
        quota_service = QuotaService(db)
        usage = await quota_service.get_today_usage(user.id)
        quota_info = {"used": usage.request_count, "max": usage.max_requests, "remaining": max(0, usage.max_requests - usage.request_count)}
        
    return templates.TemplateResponse(request, "app/main.html", context={"user": user, "quota": quota_info})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: User = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request, "auth/login.html", context={"auth_mode": settings.AUTH_MODE})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user: User = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request, "auth/register.html")

@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, user: User = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    quota_info = None
    if not user.is_admin:
        quota_service = QuotaService(db)
        usage = await quota_service.get_today_usage(user.id)
        quota_info = {"used": usage.request_count, "max": usage.max_requests, "remaining": max(0, usage.max_requests - usage.request_count)}
        
    return templates.TemplateResponse(request, "app/history.html", context={"user": user, "quota": quota_info})

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, user: User = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    quota_info = None
    if not user.is_admin:
        quota_service = QuotaService(db)
        usage = await quota_service.get_today_usage(user.id)
        quota_info = {"used": usage.request_count, "max": usage.max_requests, "remaining": max(0, usage.max_requests - usage.request_count)}
        
    return templates.TemplateResponse(request, "account/profile.html", context={"user": user, "quota": quota_info})

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request, user: User = Depends(get_optional_user)):
    if not user or not user.is_admin:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request, "admin/dashboard.html", context={"user": user})

@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request, user: User = Depends(get_optional_user)):
    if not user or not user.is_admin:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request, "admin/users.html", context={"user": user})

@router.get("/admin/logs", response_class=HTMLResponse)
async def admin_logs_page(request: Request, user: User = Depends(get_optional_user)):
    if not user or not user.is_admin:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request, "admin/logs.html", context={"user": user})
