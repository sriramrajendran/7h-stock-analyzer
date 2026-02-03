"""
Lambda entry point with FastAPI and EventBridge support
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from typing import List, Dict, Any
import os
import json
from datetime import datetime
from dataclasses import dataclass

from app.engine.modular_recommender import run_modular_analysis, run_single_analysis
from app.api.single_analysis import router as analysis_router
# Removed complex security import - using simple auth
from app.services.s3_store import persist_results
from app.services.pushover import send_push_notification
from app.services.config_manager import (
    load_config_from_s3, update_config_in_s3, get_all_configs,
    validate_symbols, sync_configs_to_local
)
from app.logging_middleware import CostOptimizedLoggingMiddleware, StructuredErrorLoggingMiddleware
from app.simple_auth import verify_api_key
from app.logger import get_logger

logger = get_logger()

@dataclass
class RunNowResponse:
    status: str
    recommendations: int
    timestamp: str

@dataclass
class HealthResponse:
    status: str
    timestamp: str
    version: str

@dataclass
class ConfigUpdateRequest:
    config_type: str
    symbols: List[str]
    backup: bool = True

@dataclass
class ConfigValidationRequest:
    symbols: List[str]


app = FastAPI(
    title="Stock Recommendation Engine",
    description="Modular serverless stock analysis API",
    version="2.0.0"
)

# Include API routers
app.include_router(analysis_router)
# Removed complex security router - using simple API key auth

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:57544", "http://127.0.0.1:57544"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add cost-optimized logging middleware
app.add_middleware(CostOptimizedLoggingMiddleware)
app.add_middleware(StructuredErrorLoggingMiddleware)


@app.get("/recon/summary")
def get_recon_summary(auth: bool = verify_api_key):
    """Get reconciliation summary showing profit/stop loss performance"""
    try:
        from app.services.recon_service import ReconService
        recon_service = ReconService()
        summary = recon_service.get_recon_summary(days=30)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recon summary: {str(e)}")


@app.get("/recon/daily/{date}")
def get_daily_recon(date: str, auth: bool = verify_api_key):
    """Get daily reconciliation data for specific date (YYYY-MM-DD)"""
    try:
        from app.services.recon_service import ReconService
        recon_service = ReconService()
        
        # Get specific daily recon file
        recon_key = f'recon/daily/{date}.json'
        response = recon_service.s3_client.get_object(
            Bucket=recon_service.bucket_name,
            Key=recon_key
        )
        return json.loads(response['Body'].read().decode('utf-8'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get daily recon: {str(e)}")


@app.post("/recon/run")
def run_reconciliation(auth: bool = verify_api_key):
    """Manual trigger for daily reconciliation"""
    try:
        from app.services.recon_service import run_daily_reconciliation
        result = run_daily_reconciliation()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run reconciliation: {str(e)}")


@app.get("/health")
def health_check():
    """Health check endpoint - optimized for minimal cost"""
    # In production, skip timestamp generation to reduce computation
    if os.getenv('ENVIRONMENT') == 'prod':
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00.000000",  # Static timestamp in prod
            "version": "1.0.0"
        }
    else:
        # In dev, provide accurate timestamp for debugging
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }


@app.post("/run-now")
def run_now(auth: bool = verify_api_key):
    """Manual trigger for stock analysis using modular engine"""
    try:
        # Run the modular recommendation engine
        recommendations = run_modular_analysis()
        
        # Persist results to S3
        persist_results(recommendations)
        
        # Send Pushover notification
        send_push_notification(recommendations)
        
        return {
            "status": "success",
            "recommendations": len(recommendations),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/recommendations")
def get_recommendations(auth: bool = verify_api_key):
    """Get latest recommendations from S3"""
    try:
        from app.services.s3_store import get_latest_results
        return get_latest_results()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@app.get("/history/dates")
def get_available_dates(auth: bool = verify_api_key):
    """Get list of available dates with historical recommendations"""
    try:
        from app.services.s3_store import get_available_dates
        dates = get_available_dates()
        return {
            "dates": dates,
            "count": len(dates)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available dates: {str(e)}")


@app.get("/history/{date}")
def get_historical_recommendations(date: str, auth: bool = verify_api_key):
    """Get historical recommendations for a specific date (YYYY-MM-DD)"""
    try:
        from app.services.s3_store import get_historical_results
        return get_historical_results(date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get historical data: {str(e)}")


@app.get("/config/{config_type}")
def get_config(config_type: str, auth: bool = verify_api_key):
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
def get_all_configurations(auth: bool = verify_api_key):
    """Get all configurations"""
    try:
        result = get_all_configs()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configurations: {str(e)}")


@app.post("/config/update")
def update_configuration(request: ConfigUpdateRequest, auth: bool = verify_api_key):
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
def validate_symbols_endpoint(request: ConfigValidationRequest, auth: bool = verify_api_key):
    """Validate stock symbols"""
    try:
        result = validate_symbols(request.symbols)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate symbols: {str(e)}")


@app.post("/config/sync")
def sync_configurations(auth: bool = verify_api_key):
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
            logger.info("EventBridge cron trigger detected", trigger_type="cron")
            
            # Check if this is the weekly reconciliation trigger
            resources = event.get("resources", [])
            if any("StockAnalyzerWeeklyRecon" in resource for resource in resources):
                logger.info("Weekly reconciliation trigger detected")
                
                # Run reconciliation
                from app.services.recon_service import run_daily_reconciliation
                recon_result = run_daily_reconciliation()
                
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "status": "weekly reconciliation executed",
                        "reconciled_count": recon_result.get("reconciled_count", 0),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                }
            else:
                # Regular stock analysis trigger
                logger.info("Stock analysis trigger detected")
                
                # Run the modular recommendation engine
                recommendations = run_modular_analysis()
                
                # Persist results to S3
                persist_results(recommendations)
                
                # Send Pushover notification
                send_push_notification(recommendations)
                
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "status": "stock analysis executed",
                        "count": len(recommendations),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                }
        
        # Handle API Gateway requests
        else:
            return asgi_handler(event, context)
            
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}", error=str(e), event_source=event.get("source", "unknown"))
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
