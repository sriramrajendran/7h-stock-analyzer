"""
Pydantic models for the Stock Recommendation Engine
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class Recommendation(BaseModel):
    """Enhanced stock recommendation model"""
    symbol: str = Field(..., description="Stock ticker symbol")
    company: str = Field(..., description="Company name")
    price: float = Field(..., description="Current stock price")
    change_pct: float = Field(..., description="Price change percentage")
    rsi: float = Field(..., description="RSI indicator value")
    macd: float = Field(..., description="MACD indicator value")
    sma_20: float = Field(..., description="20-day SMA")
    sma_50: float = Field(..., description="50-day SMA")
    recommendation: str = Field(..., description="Recommendation type")
    score: float = Field(..., description="Recommendation score")
    reasoning: str = Field(..., description="Recommendation reasoning")
    fundamental: Dict[str, Any] = Field(default_factory=dict, description="Fundamental data")
    timestamp: str = Field(..., description="Analysis timestamp")
    
    # Enhanced fields for spec_lambda_enhance.md
    target_price: Optional[float] = Field(None, description="Target price based on recommendation type")
    stop_loss: Optional[float] = Field(None, description="Stop loss price for risk management")
    confidence_level: Optional[str] = Field(None, description="Confidence level (High/Medium/Low)")
    technical_indicators: List[str] = Field(default_factory=list, description="Technical indicators used")
    price_chart_url: Optional[str] = Field(None, description="URL to price chart image")
    days_to_target: Optional[int] = Field(None, description="Days taken to reach target (recon data)")
    target_met: Optional[bool] = Field(None, description="Whether target price was met (recon data)")
    stop_loss_hit: Optional[bool] = Field(None, description="Whether stop loss was hit (recon data)")


class AnalysisResponse(BaseModel):
    """Response model for stock analysis"""
    success: bool
    recommendations: List[Recommendation]
    timestamp: str
    count: int


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: str
    version: str
    region: Optional[str] = None


class RunNowResponse(BaseModel):
    """Manual run response model"""
    status: str
    recommendations: int
    timestamp: str


class HistoricalData(BaseModel):
    """Historical recommendations data model"""
    timestamp: str
    date: str
    count: int
    recommendations: List[Recommendation]


class LatestData(BaseModel):
    """Latest recommendations data model"""
    timestamp: str
    date: str
    count: int
    recommendations: List[Recommendation]


class SummaryStats(BaseModel):
    """Summary statistics model"""
    total_days_with_data: int
    latest_recommendations: int
    previous_day_recommendations: int
    latest_date: Optional[str]
    available_dates: List[str]


class RecommendationsSummary(BaseModel):
    """Recommendations summary response model"""
    summary: SummaryStats
    latest_data: LatestData


class NotificationConfig(BaseModel):
    """Notification configuration model"""
    token_configured: bool
    user_configured: bool
    test_sent: bool
    test_successful: bool


class ConfigValidation(BaseModel):
    """Configuration validation model"""
    s3_configured: bool
    pushover_configured: bool
    symbols_loaded: bool
    symbol_count: int
    environment: str


class ReconData(BaseModel):
    """Reconciliation data for recommendations"""
    symbol: str
    original_recommendation: str
    original_price: float
    target_price: Optional[float]
    stop_loss: Optional[float]
    current_price: float
    days_elapsed: int
    target_met: bool
    stop_loss_hit: bool
    recon_date: str
    original_timestamp: str


class ConfigUpdateRequest(BaseModel):
    """Configuration update request model"""
    config_type: str
    symbols: List[str]
    backup: bool = True


class ConfigValidationRequest(BaseModel):
    """Symbol validation request model"""
    symbols: List[str]


class PurgeRequest(BaseModel):
    """Purge old recommendations request model"""
    days_threshold: int = Field(default=1000, description="Days after which to purge recommendations")
    dry_run: bool = Field(default=True, description="Run in dry-run mode without actual deletion")
