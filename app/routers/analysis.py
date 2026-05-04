from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.quota import check_quota
from app.services.analysis_service import AnalysisService
from app.schemas.analysis import (
    UploadResponse, TaskStatusResponse, HistoryListResponse, 
    HistoryItemResponse, ConfirmTypeRequest, ChatRequest, ChatResponse
)
from fastapi.responses import Response
from app.models.user import User
from app.websocket.manager import websocket_manager

router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])

# --- Static routes FIRST (must come before /{task_id} dynamic routes) ---

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    quota_ok: bool = Depends(check_quota),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(".dxf"):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file DXF")
        
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File quá lớn (tối đa 50MB)")
        
    analysis_service = AnalysisService(db)
    result = await analysis_service.upload_and_parse(
        user_id=current_user.id,
        filename=file.filename,
        file_bytes=contents
    )
    
    return UploadResponse(**result, message="Tải lên thành công, vui lòng xác nhận loại bản vẽ")

@router.get("/history", response_model=HistoryListResponse)
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    analysis_service = AnalysisService(db)
    offset = (page - 1) * page_size
    items = await analysis_service.get_history(current_user.id, limit=page_size, offset=offset)
    
    total = len(items) if len(items) < page_size else page_size * page + 1
    
    return HistoryListResponse(
        items=[HistoryItemResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size
    )

@router.delete("/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history(history_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    analysis_service = AnalysisService(db)
    await analysis_service.delete_history(history_id, current_user.id)
    return None

# --- Dynamic routes (/{task_id} prefix) ---

@router.post("/{task_id}/confirm-type")
async def confirm_type(
    task_id: str,
    request: ConfirmTypeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    analysis_service = AnalysisService(db)
    return await analysis_service.confirm_type_and_start(
        task_id, 
        request.drawing_type, 
        background_tasks, 
        websocket_manager
    )

@router.post("/{task_id}/chat", response_model=ChatResponse)
async def chat(
    task_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    analysis_service = AnalysisService(db)
    return await analysis_service.chat(task_id, request.message)

@router.get("/{task_id}/svg")
async def get_svg(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    analysis_service = AnalysisService(db)
    svg_content = await analysis_service.get_svg(task_id)
    return Response(content=svg_content, media_type="image/svg+xml")

@router.get("/{task_id}/status", response_model=TaskStatusResponse)
async def get_status(task_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    analysis_service = AnalysisService(db)
    status_info = await analysis_service.get_task_status(task_id)
    return TaskStatusResponse(**status_info)
