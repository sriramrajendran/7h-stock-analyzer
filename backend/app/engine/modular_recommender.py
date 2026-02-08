"""
Modular Stock Analysis Engine - Orchestrates all modules for complete analysis
"""

import os
import logging
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

from app.modules import DataLoader, IndicatorEngine, SignalEngine, RecommendationEngine
from app.services.config_manager import load_config_from_s3

logger = logging.getLogger(__name__)

class ModularStockAnalyzer:
    """Main orchestrator for the modular stock analysis system"""
    
    def __init__(self, s3_bucket: str = None, use_cache: bool = False):
        self.s3_bucket = s3_bucket or os.getenv('S3_BUCKET_NAME', '7h-stock-analyzer-dev')
        self.use_cache = use_cache  # Disabled for debugging
        
        # Initialize all modules
        self.data_loader = DataLoader(s3_bucket=self.s3_bucket, use_s3_cache=self.use_cache)
        self.indicator_engine = IndicatorEngine()
        self.signal_engine = SignalEngine()
        self.recommendation_engine = RecommendationEngine()
        
        logger.info("Modular Stock Analyzer initialized (cache disabled for debugging)")
    
    def analyze_universe(self, tickers: List[str] = None, period: str = "1y") -> List[Dict]:
        """Complete analysis pipeline for a universe of stocks"""
        try:
            # Load tickers from configuration if not provided
            if not tickers:
                tickers = self._load_default_tickers()
            
            if not tickers:
                logger.warning("No tickers provided for analysis")
                return []
            
            logger.info(f"Starting analysis for {len(tickers)} tickers")
            
            # Step 1: Data Loading
            logger.info("Step 1: Loading OHLCV data...")
            data_dict = self.data_loader.fetch_universe(tickers, period)
            
            if not data_dict:
                logger.error("No data loaded")
                return []
            
            logger.info(f"Loaded data for {len(data_dict)} tickers")
            
            # Step 2: Indicator Computation
            logger.info("Step 2: Computing technical indicators...")
            enhanced_data = {}
            
            for ticker, df in data_dict.items():
                try:
                    df_with_indicators = self.indicator_engine.compute_all_indicators(df)
                    if not df_with_indicators.empty:
                        enhanced_data[ticker] = df_with_indicators
                except Exception as e:
                    logger.error(f"Error computing indicators for {ticker}: {str(e)}")
                    continue
            
            logger.info(f"Computed indicators for {len(enhanced_data)} tickers")
            
            # Step 3: Signal Generation
            logger.info("Step 3: Generating trading signals...")
            signal_data = {}
            
            for ticker, df in enhanced_data.items():
                try:
                    df_with_signals = self.signal_engine.generate_signals(df)
                    if not df_with_signals.empty:
                        signal_data[ticker] = df_with_signals
                except Exception as e:
                    logger.error(f"Error generating signals for {ticker}: {str(e)}")
                    continue
            
            logger.info(f"Generated signals for {len(signal_data)} tickers")
            
            # Step 4: Recommendation Generation
            logger.info("Step 4: Generating recommendations...")
            recommendations = self.recommendation_engine.batch_recommendations(signal_data)
            
            logger.info(f"Generated {len(recommendations)} recommendations")
            
            # Step 5: Add metadata
            for rec in recommendations:
                rec['analysis_metadata'] = {
                    'analysis_period': period,
                    'data_points': len(signal_data.get(rec['symbol'], pd.DataFrame())),
                    'cache_used': self.use_cache,
                    'analysis_timestamp': datetime.utcnow().isoformat()
                }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in analysis pipeline: {str(e)}")
            return []
    
    def analyze_single_ticker(self, ticker: str, period: str = "1y") -> Dict:
        """Analyze a single ticker"""
        try:
            ticker = ticker.upper().strip()
            logger.info(f"Analyzing single ticker: {ticker}")
            
            # Step 1: Load data
            df = self.data_loader.fetch_single_ticker(ticker, period)
            if df.empty:
                logger.warning(f"No data found for {ticker}")
                return self._empty_analysis(ticker)
            
            # Step 2: Compute indicators
            df_indicators = self.indicator_engine.compute_all_indicators(df)
            if df_indicators.empty:
                logger.warning(f"Failed to compute indicators for {ticker}")
                return self._empty_analysis(ticker)
            
            # Step 3: Generate signals
            df_signals = self.signal_engine.generate_signals(df_indicators)
            if df_signals.empty:
                logger.warning(f"Failed to generate signals for {ticker}")
                return self._empty_analysis(ticker)
            
            # Step 4: Generate recommendation
            recommendation = self.recommendation_engine.generate_recommendations(df_signals, ticker)
            
            # Add detailed analysis data
            recommendation['detailed_analysis'] = {
                'indicator_summary': self.indicator_engine.get_indicator_summary(df_signals),
                'signal_summary': self.signal_engine.get_signal_summary(df_signals),
                'signal_history': self.signal_engine.get_signal_history(df_signals).to_dict('records') if len(df_signals) > 1 else [],
                'data_validation': self.indicator_engine.validate_indicators(df_signals)
            }
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {str(e)}")
            return self._empty_analysis(ticker)
    
    def get_cache_statistics(self) -> Dict:
        """Get cache statistics"""
        return self.data_loader.get_cache_stats()
    
    def clear_cache(self, ticker: str = None) -> bool:
        """Clear cache"""
        return self.data_loader.clear_cache(ticker)
    
    def _load_default_tickers(self) -> List[str]:
        """Load default tickers from configuration"""
        try:
            # Try to load from S3 configuration (portfolio first, then watchlist)
            config_result = load_config_from_s3('portfolio')
            if config_result.get('success') and config_result.get('symbols'):
                logger.info(f"Loaded {len(config_result['symbols'])} tickers from portfolio config")
                return config_result['symbols']
            
            # Fallback to watchlist
            config_result = load_config_from_s3('watchlist')
            if config_result.get('success') and config_result.get('symbols'):
                logger.info(f"Loaded {len(config_result['symbols'])} tickers from watchlist config")
                return config_result['symbols']
            
            # Fallback to default list
            default_tickers = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA',
                'JPM', 'V', 'JNJ', 'WMT', 'PG', 'UNH', 'MA', 'HD'
            ]
            
            logger.info(f"Using default ticker list: {len(default_tickers)} tickers")
            return default_tickers
            
        except Exception as e:
            logger.error(f"Error loading default tickers: {str(e)}")
            return []
    
    def _empty_analysis(self, ticker: str) -> Dict:
        """Return empty analysis result"""
        return {
            'symbol': ticker,
            'recommendation': 'Hold',
            'score': 0.0,
            'confidence_level': 'Low',
            'reasoning': 'Analysis failed - insufficient data or technical error',
            'timestamp': datetime.utcnow().isoformat(),
            'detailed_analysis': {
                'indicator_summary': {},
                'signal_summary': {},
                'signal_history': [],
                'data_validation': {}
            }
        }

# Global instance for Lambda usage
_analyzer_instance = None

def get_analyzer() -> ModularStockAnalyzer:
    """Get or create analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ModularStockAnalyzer()
    return _analyzer_instance

def run_modular_analysis(tickers: List[str] = None, period: str = "1y") -> List[Dict]:
    """Run complete modular analysis - main entry point for Lambda"""
    analyzer = get_analyzer()
    return analyzer.analyze_universe(tickers, period)

def run_single_analysis(ticker: str, period: str = "1y") -> Dict:
    """Run single ticker analysis"""
    analyzer = get_analyzer()
    return analyzer.analyze_single_ticker(ticker, period)
