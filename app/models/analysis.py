from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Enum, Integer, Text, DateTime, ForeignKey, Index, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    drawing_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum('pending', 'awaiting_confirmation', 'running', 'completed', 'failed', name='status_enum'), 
        default='pending', 
        nullable=False
    )
    
    # Prediction fields
    predicted_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prediction_confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    prediction_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # AI Data fields
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Stores DXF stats
    svg_content: Mapped[Optional[str]] = mapped_column(Text(length=16777215), nullable=True) # LongText for large SVGs
    dxf_json: Mapped[Optional[str]] = mapped_column(Text(length=16777215), nullable=True)
    png_bytes: Mapped[Optional[bytes]] = mapped_column(LargeBinary(length=16777215), nullable=True) # BLOB for PNG image
    
    high_errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    medium_errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    report_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="analysis_histories")

    __table_args__ = (
        Index('idx_analysis_user_id', 'user_id'),
        Index('idx_analysis_task_id', 'task_id'),
        Index('idx_analysis_status', 'status'),
    )
