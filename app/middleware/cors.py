from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

def setup_cors(app: FastAPI):
    if settings.APP_ENV == "development":
        allow_origins = ["*"]
    else:
        # In production, specify exact domains
        allow_origins = [
            f"http://{settings.APP_HOST}:{settings.APP_PORT}",
        ]
        
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    )
