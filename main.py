"""
Main Entry Point for AI Vision Drawing Checker
This is the FastAPI entry point replacing the original Streamlit app.py.
"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from sqlalchemy import text

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.middleware.cors import setup_cors
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.auth_middleware import BruteForceProtectionMiddleware

from app.routers import auth, analysis, users, pages, admin
from app.websocket.manager import websocket_manager
from app.dependencies.auth import get_current_user

app = FastAPI(
    title="AI Vision Drawing Checker",
    description="FastAPI Backend for the Drawing Checker System",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None
)

# Setup Middlewares
setup_cors(app)
app.add_middleware(LoggingMiddleware)
app.add_middleware(BruteForceProtectionMiddleware)

# Include Routers
app.include_router(pages.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(users.router)

# Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail), "details": {}}}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": "Dữ liệu không hợp lệ.", "details": exc.errors()}}
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logging.getLogger("api_request").error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "DATABASE_ERROR", "message": "Đã xảy ra lỗi cơ sở dữ liệu. Vui lòng thử lại sau.", "details": {}}}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.getLogger("api_request").error(f"Unhandled exception: {str(exc)}")
    if settings.APP_ENV == "production":
        message = "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau."
        details = {}
    else:
        message = str(exc)
        details = {"type": type(exc).__name__}
        
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": message, "details": details}}
    )

# Mount static files
import os
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def startup_event():
    import logging
    import asyncio
    logger = logging.getLogger("startup")

    # Initialize RAGEngine singleton at startup (loads/builds ChromaDB index)
    try:
        from modules.rag_engine import get_rag_engine
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, get_rag_engine)
        logger.info("RAGEngine initialized successfully.")
    except Exception as e:
        logger.error("RAGEngine initialization failed: %s", e)

    try:
        import pkg_resources
        reqs = [req.project_name.lower() for req in pkg_resources.parse_requirements(open('requirements.txt').read())]
        if 'streamlit' in reqs:
            logger.warning("Streamlit dependency detected. Please remove from requirements.txt")
    except Exception:
        pass
        
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from app.services.log_service import LogService
        
        async def cleanup_logs_job():
            async with AsyncSessionLocal() as db:
                log_service = LogService(db)
                await log_service.cleanup_old_logs(days=30)
                await db.commit()
                
        scheduler = AsyncIOScheduler()
        scheduler.add_job(cleanup_logs_job, 'cron', hour=2, minute=0)
        scheduler.start()
        logger.info("APScheduler started: Log cleanup scheduled at 02:00 daily")
    except ImportError:
        logger.warning("APScheduler not found. Please install it to enable log cleanup.")

@app.get("/health")
async def health_check():
    """Health check endpoint to verify system status."""
    db_status = "connected"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"
        
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "rag_engine": "ready",
        "version": "1.0.0"
    }

# WebSocket Endpoint
@app.websocket("/ws/analysis/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str, token: str = None):
    # Prefer token from query param, fallback to HttpOnly cookie
    # (JS cannot read HttpOnly cookies, so the frontend passes the token via query param
    #  using a short-lived token fetched from /api/v1/auth/ws-token)
    if not token:
        token = websocket.cookies.get("access_token")

    if not token:
        await websocket.close(code=4001)
        return
    
    try:
        from app.core.security import decode_token
        from jose import JWTError
        payload = decode_token(token)
        if not payload.get("sub"):
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return
        
    await websocket_manager.connect(task_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed, otherwise just keep connection alive
    except WebSocketDisconnect:
        websocket_manager.disconnect(task_id)

if __name__ == "__main__":
    import uvicorn
    # Start the server locally
    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
