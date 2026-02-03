"""
Lambda entry point with FastAPI and EventBridge support
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import json
from datetime import datetime

from app.engine.recommender import run_engine
from app.services.s3_store import persist_results
from app.services.pushover import send_push_notification
from app.services.config_manager import (
    load_config_from_s3, update_config_in_s3, get_all_configs,
    validate_symbols, sync_configs_to_local
)


class RunNowResponse(BaseModel):
    status: str
    recommendations: int
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class ConfigUpdateRequest(BaseModel):
    config_type: str
    symbols: List[str]
    backup: bool = True


class ConfigValidationRequest(BaseModel):
    symbols: List[str]


app = FastAPI(
    title="Stock Recommendation Engine",
    description="Serverless stock analysis API",
    version="1.0.0"
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:57544", "http://127.0.0.1:57544"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )


@app.post("/run-now", response_model=RunNowResponse)
def run_now():
    """Manual trigger for stock analysis"""
    try:
        # Run the recommendation engine
        recommendations = run_engine()
        
        # Persist results to S3
        persist_results(recommendations)
        
        # Send Pushover notification
        send_push_notification(recommendations)
        
        return RunNowResponse(
            status="success",
            recommendations=len(recommendations),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/recommendations")
def get_recommendations():
    """Get latest recommendations from S3"""
    try:
        from app.services.s3_store import get_latest_results
        return get_latest_results()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@app.get("/history/{date}")
def get_historical_recommendations(date: str):
    """Get historical recommendations for a specific date (YYYY-MM-DD)"""
    try:
        from app.services.s3_store import get_historical_results
        return get_historical_results(date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get historical data: {str(e)}")


@app.get("/config/{config_type}")
def get_config(config_type: str):
    """Get configuration for a specific type"""
    try:
        result = load_config_from_s3(config_type)
        if not result['success']:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@app.get("/config")
def get_all_configurations():
    """Get all configurations"""
    try:
        result = get_all_configs()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configurations: {str(e)}")


@app.post("/config/update")
def update_configuration(request: ConfigUpdateRequest):
    """Update configuration for a specific type"""
    try:
        result = update_config_in_s3(request.config_type, request.symbols, request.backup)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@app.post("/config/validate")
def validate_symbols_endpoint(request: ConfigValidationRequest):
    """Validate stock symbols"""
    try:
        result = validate_symbols(request.symbols)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate symbols: {str(e)}")


@app.post("/config/sync")
def sync_configurations():
    """Sync configurations from S3 to local files"""
    try:
        result = sync_configs_to_local()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync configurations: {str(e)}")


# Mangum adapter for Lambda
asgi_handler = Mangum(app)


def handler(event, context):
    """
    Lambda handler function
    
    Handles both EventBridge cron triggers and API Gateway requests
    """
    try:
        # Check if this is an EventBridge cron trigger
        if event.get("source") == "aws.events":
            print("EventBridge cron trigger detected")
            
            # Run the recommendation engine
            recommendations = run_engine()
            
            # Persist results to S3
            persist_results(recommendations)
            
            # Send Pushover notification
            send_push_notification(recommendations)
            
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "cron executed",
                    "count": len(recommendations),
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
        
        # Handle API Gateway requests
        else:
            return asgi_handler(event, context)
            
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"Internal server error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
        }


if __name__ == "__main__":
    # For local testing
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
