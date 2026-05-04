from datetime import datetime
from typing import Optional, Any
from sqlalchemy import BigInteger, String, Enum, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    details: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    severity: Mapped[str] = mapped_column(Enum('INFO', 'WARNING', 'ERROR', name='severity_enum'), default='INFO', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="activity_logs")

    __table_args__ = (
        Index('idx_log_user_id', 'user_id'),
        Index('idx_log_event_type', 'event_type'),
        Index('idx_log_severity', 'severity'),
        Index('idx_log_created_at', 'created_at'),
    )
