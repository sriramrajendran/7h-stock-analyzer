"""
Data models for the Stock Recommendation Engine
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Recommendation:
    """Enhanced stock recommendation model"""
    symbol: str
    company: str
    price: float
    change_pct: float
    rsi: float
    macd: float
    sma_20: float
    sma_50: float
    recommendation: str
    score: float = 0.0
    reasoning: str = ""
    fundamental: Dict[str, Any] = None
    timestamp: str = ""
    
    # Enhanced fields for spec_lambda_enhance.md
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    confidence_level: Optional[str] = None
    technical_indicators: List[str] = None
    price_chart_url: Optional[str] = None
    days_to_target: Optional[int] = None
    target_met: Optional[bool] = None
    stop_loss_hit: Optional[bool] = None


@dataclass
class AnalysisResponse:
    """Response model for stock analysis"""
    success: bool
    recommendations: List[Recommendation]
    timestamp: str
    count: int


@dataclass
class ErrorResponse:
    """Error response model"""
    error: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class HealthResponse:
    """Health check response model"""
    status: str
    timestamp: str
    version: str
    region: Optional[str] = None


@dataclass
class RunNowResponse:
    """Manual run response model"""
    status: str
    recommendations: int
    timestamp: str


@dataclass
class HistoricalData:
    """Historical recommendations data model"""
    timestamp: str
    date: str
    count: int
    recommendations: List[Recommendation]


@dataclass
class LatestData:
    """Latest recommendations data model"""
    timestamp: str
    date: str
    count: int
    recommendations: List[Recommendation]


@dataclass
class SummaryStats:
    """Summary statistics model"""
    total_days_with_data: int
    latest_recommendations: int
    previous_day_recommendations: int
    latest_date: Optional[str]
    available_dates: List[str]


class RecommendationsSummary:
    """Recommendations summary response model"""
    summary: SummaryStats
    latest_data: LatestData


@dataclass
class NotificationConfig:
    """Notification configuration model"""
    token_configured: bool
    user_configured: bool
    test_sent: bool
    test_successful: bool


@dataclass
class ConfigValidation:
    """Configuration validation model"""
    s3_configured: bool
    pushover_configured: bool
    symbols_loaded: bool
    symbol_count: int
    environment: str


@dataclass
class ReconData:
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


@dataclass
class ConfigUpdateRequest:
    """Configuration update request model"""
    config_type: str
    symbols: List[str]
    backup: bool = True


@dataclass
class ConfigValidationRequest:
    """Symbol validation request model"""
    symbols: List[str]


@dataclass
class PurgeRequest:
    """Purge old recommendations request model"""
    days_threshold: int = 1000
    dry_run: bool = True
