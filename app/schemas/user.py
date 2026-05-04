from pydantic import BaseModel, ConfigDict
from typing import Optional

class QuotaInfoResponse(BaseModel):
    used: int
    max: int
    remaining: int

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    display_name: str
    role: str
    avatar_url: Optional[str] = None
    quota: Optional[QuotaInfoResponse] = None

class UpdateProfileRequest(BaseModel):
    display_name: str
    avatar_url: Optional[str] = None
