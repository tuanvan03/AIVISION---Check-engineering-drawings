from datetime import datetime
from typing import List, Optional
from sqlalchemy import BigInteger, String, Enum, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(Enum('user', 'admin', name='role_enum'), default='user', nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    oauth_provider: Mapped[Optional[str]] = mapped_column(Enum('google', 'github', name='oauth_provider_enum'), nullable=True)
    oauth_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    quota_usages: Mapped[List["QuotaUsage"]] = relationship("QuotaUsage", back_populates="user", cascade="all, delete-orphan")
    analysis_histories: Mapped[List["AnalysisHistory"]] = relationship("AnalysisHistory", back_populates="user", cascade="all, delete-orphan")
    activity_logs: Mapped[List["ActivityLog"]] = relationship("ActivityLog", back_populates="user")
    sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_email', 'email'),
        Index('idx_role', 'role'),
        Index('idx_oauth', 'oauth_provider', 'oauth_id'),
    )

    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'
