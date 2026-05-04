import time
import json
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api_request")
logger.setLevel(logging.INFO)
# Basic console handler for JSON-like logs
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        
        # Don't log bodies, but log basic request info
        log_dict = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_ms": round(process_time, 2)
        }
        
        if hasattr(request.state, "user_id"):
             log_dict["user_id"] = request.state.user_id
             
        logger.info(json.dumps(log_dict))
        
        return response
