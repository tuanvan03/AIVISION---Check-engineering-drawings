from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime

class UploadResponse(BaseModel):
    task_id: str
    message: str
    predicted_drawing_type: Optional[str] = None
    prediction_confidence: Optional[float] = None
    prediction_reasoning: Optional[str] = None
    is_confident: bool = False
    dxf_metadata: Optional[Dict[str, Any]] = None

class ConfirmTypeRequest(BaseModel):
    drawing_type: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    task_id: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress_step: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class HistoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    task_id: str
    filename: str
    status: str
    high_errors: int
    medium_errors: int
    low_errors: int
    created_at: datetime
    error_message: Optional[str] = None

class HistoryListResponse(BaseModel):
    items: List[HistoryItemResponse]
    total: int
    page: int
    page_size: int

class AnalysisResultResponse(BaseModel):
    conclusion: str
    details: List[Dict[str, Any]]
