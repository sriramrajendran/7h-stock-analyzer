"""
Single Stock Analysis API Endpoint
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from app.engine.modular_recommender import run_single_analysis
from app.simple_auth import verify_api_key

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.get("/{ticker}")
def analyze_single_stock(
    ticker: str,
    period: str = Query(default="1y", description="Analysis period (1y, 6mo, 3mo, 1mo)"),
    auth: bool = Depends(verify_api_key)
):
    """
    Analyze a single stock ticker
    
    - **ticker**: Stock symbol (e.g., AAPL, MSFT)
    - **period**: Historical data period for analysis
    """
    try:
        ticker = ticker.upper().strip()
        
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker symbol is required")
        
        # Simple test response first
        # Test data loading
        from app.modules.data_loader import DataLoader
        loader = DataLoader()
        df = loader.fetch_single_ticker(ticker, period)
        
        # Run single ticker analysis
        try:
            result = run_single_analysis(ticker, period)
            
            # Convert numpy types to Python types for JSON serialization
            def convert_numpy(obj):
                if hasattr(obj, 'item'):  # numpy scalar
                    return obj.item()
                elif hasattr(obj, 'tolist'):  # numpy array
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_numpy(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy(v) for v in obj]
                else:
                    return obj
            
            converted_result = convert_numpy(result)
            
            return {
                "success": True,
                "data": converted_result,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as analysis_error:
            return {
                "success": False,
                "data": {"error": str(analysis_error)},
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Run single ticker analysis (commented out for testing)
        # result = run_single_analysis(ticker, period)
        # return {
        #     "success": True,
        #     "data": result,
        #     "timestamp": datetime.utcnow().isoformat()
        # }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/{ticker}/signals")
def get_ticker_signals(ticker: str, period: str = Query(default="1y"), auth: bool = Depends(verify_api_key)):
    """Get detailed signal analysis for a ticker"""
    try:
        ticker = ticker.upper().strip()
        result = run_single_analysis(ticker, period)
        
        # Extract signal data
        signals = result.get('detailed_analysis', {}).get('signal_summary', {})
        signal_history = result.get('detailed_analysis', {}).get('signal_history', [])
        
        return {
            'ticker': ticker,
            'current_signals': signals,
            'signal_history': signal_history,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signal analysis failed: {str(e)}")

@router.get("/{ticker}/indicators")
def get_ticker_indicators(ticker: str, period: str = Query(default="1y")):
    """Get technical indicators for a ticker"""
    try:
        ticker = ticker.upper().strip()
        result = run_single_analysis(ticker, period)
        
        # Extract indicator data
        indicators = result.get('detailed_analysis', {}).get('indicator_summary', {})
        
        return {
            'ticker': ticker,
            'indicators': indicators,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indicator analysis failed: {str(e)}")
