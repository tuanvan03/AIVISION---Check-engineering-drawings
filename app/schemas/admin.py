from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional, Any, Dict
from datetime import datetime

class AdminUserListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    display_name: str
    role: str
    is_active: bool
    created_at: datetime

class AdminUserDetailResponse(AdminUserListResponse):
    oauth_provider: Optional[str] = None
    
class UpdateUserRoleRequest(BaseModel):
    role: str

class UpdateQuotaRequest(BaseModel):
    max_requests: int

class LogQueryParams(BaseModel):
    user_id: Optional[int] = None
    event_type: Optional[str] = None
    severity: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 50
    offset: int = 0

class LogListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: Optional[int] = None
    event_type: str
    severity: str
    ip_address: Optional[str] = None
    created_at: datetime
    details: Optional[Dict[str, Any]] = None

class StatsResponse(BaseModel):
    total_users: int = 0
    active_users_7d: int = 0
    analyses_today: int = 0
    analyses_this_month: int = 0

