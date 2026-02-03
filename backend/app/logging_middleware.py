"""
Cost-optimized logging middleware for FastAPI
"""

import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.logger import get_logger

logger = get_logger()

class CostOptimizedLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for cost-optimized API logging"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",  # Exclude health checks from detailed logging
            "/metrics",  # Exclude metrics endpoints
            "/history/dates",  # Exclude frequently polled endpoints
            "/config"  # Exclude config endpoints
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip all processing for health checks to minimize Lambda execution time
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log API call with cost optimization
        logger.log_api_call(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_agent=request.headers.get("user-agent", "unknown"),
            client_ip=request.client.host if request.client else "unknown"
        )
        
        return response

class StructuredErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured error logging"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            # Log structured error information
            logger.error(
                f"Unhandled error in {request.method} {request.url.path}",
                error=str(e),
                endpoint=request.url.path,
                method=request.method,
                user_agent=request.headers.get("user-agent", "unknown"),
                client_ip=request.client.host if request.client else "unknown"
            )
            raise
