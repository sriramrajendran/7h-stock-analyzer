"""
Enhanced recommendation engine with target prices, stop losses, and confidence levels
"""

import yfinance as yf
import pandas as pd
import numpy as np
try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    print("Warning: ta library not available, using fallback calculations")
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging
from app.models import Recommendation

logger = logging.getLogger(__name__)

class EnhancedRecommender:
    """Enhanced stock recommendation engine with advanced features"""
    
    def __init__(self):
        self.confidence_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
    
    def calculate_target_price(self, recommendation: str, current_price: float) -> float:
        """Calculate target price based on recommendation type"""
        targets = {
            'Strong Buy': current_price * 1.20,    # +20%
            'Buy': current_price * 1.10,           # +10%
            'Hold': current_price,                 # 0%
            'Sell': current_price * 0.95,          # -5%
            'Strong Sell': current_price * 0.80    # -20%
        }
        return targets.get(recommendation, current_price)
    
    def calculate_stop_loss(self, recommendation: str, current_price: float) -> float:
        """Calculate stop loss price for risk management"""
        # For buy/hold recommendations, provide stop loss
        if recommendation in ['Strong Buy', 'Buy', 'Hold']:
            return current_price * 0.95  # 5% below current price
        return None
    
    def calculate_confidence_level(self, score: float, indicators_consistency: float) -> str:
        """Calculate confidence level based on score and indicator consistency"""
        combined_score = (score + indicators_consistency) / 2
        
        if combined_score >= self.confidence_thresholds['high']:
            return 'High'
        elif combined_score >= self.confidence_thresholds['medium']:
            return 'Medium'
        else:
            return 'Low'
    
    def get_technical_indicators_used(self, data: pd.DataFrame) -> List[str]:
        """Get list of technical indicators that were significant"""
        indicators = []
        
        if TA_AVAILABLE:
            # RSI analysis
            rsi = ta.momentum.RSIIndicator(data['Close']).rsi()
            if not rsi.isna().all():
                indicators.append('RSI')
            
            # MACD analysis
            macd = ta.trend.MACD(data['Close'])
            if not macd.macd().isna().all():
                indicators.append('MACD')
            
            # SMA analysis
            sma_20 = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator()
            sma_50 = ta.trend.SMAIndicator(data['Close'], window=50).sma_indicator()
            if not sma_20.isna().all():
                indicators.append('SMA_20')
            if not sma_50.isna().all():
                indicators.append('SMA_50')
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(data['Close'])
            if not bb.bollinger_hband().isna().all():
                indicators.append('Bollinger_Bands')
            
            # Volume indicators
            if 'Volume' in data.columns:
                volume_sma = ta.volume.VolumeSMAIndicator(data['Close'], data['Volume'])
                if not volume_sma.volume_sma().isna().all():
                    indicators.append('Volume_SMA')
        else:
            # Fallback indicators
            indicators = ['RSI', 'MACD', 'SMA_20', 'SMA_50', 'Bollinger_Bands']
        
        return indicators
    
    def analyze_stock(self, symbol: str) -> Recommendation:
        """Analyze a single stock and return enhanced recommendation"""
        try:
            # Get stock data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1y")
            
            if data.empty:
                raise ValueError(f"No data found for {symbol}")
            
            # Get current price and change
            current_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2]
            change_pct = ((current_price - prev_price) / prev_price) * 100
            
            # Calculate technical indicators
            if TA_AVAILABLE:
                rsi = ta.momentum.RSIIndicator(data['Close']).rsi().iloc[-1]
                macd = ta.trend.MACD(data['Close']).macd().iloc[-1]
                sma_20 = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator().iloc[-1]
                sma_50 = ta.trend.SMAIndicator(data['Close'], window=50).sma_indicator().iloc[-1]
            else:
                # Fallback calculations using basic pandas
                rsi = 50.0  # Neutral RSI fallback
                macd = 0.0  # Neutral MACD fallback
                sma_20 = data['Close'].rolling(20).mean().iloc[-1]
                sma_50 = data['Close'].rolling(50).mean().iloc[-1]
            
            # Calculate recommendation score
            score = self._calculate_score(rsi, macd, sma_20, sma_50, current_price)
            
            # Determine recommendation type
            recommendation = self._get_recommendation_type(score)
            
            # Calculate enhanced fields
            target_price = self.calculate_target_price(recommendation, current_price)
            stop_loss = self.calculate_stop_loss(recommendation, current_price)
            
            # Get technical indicators used
            technical_indicators = self.get_technical_indicators_used(data)
            
            # Calculate confidence level
            indicators_consistency = self._calculate_indicators_consistency(
                rsi, macd, sma_20, sma_50, current_price
            )
            confidence_level = self.calculate_confidence_level(score, indicators_consistency)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                recommendation, rsi, macd, sma_20, sma_50, score
            )
            
            # Get company info
            try:
                company_info = ticker.info
                company_name = company_info.get('longName', symbol)
                fundamental_data = {
                    'market_cap': company_info.get('marketCap'),
                    'pe_ratio': company_info.get('trailingPE'),
                    'volume': company_info.get('volume'),
                    'avg_volume': company_info.get('averageVolume')
                }
            except:
                company_name = symbol
                fundamental_data = {}
            
            return Recommendation(
                symbol=symbol,
                company=company_name,
                price=current_price,
                change_pct=change_pct,
                rsi=rsi,
                macd=macd,
                sma_20=sma_20,
                sma_50=sma_50,
                recommendation=recommendation,
                score=score,
                reasoning=reasoning,
                fundamental=fundamental_data,
                timestamp=datetime.utcnow().isoformat(),
                target_price=target_price,
                stop_loss=stop_loss,
                confidence_level=confidence_level,
                technical_indicators=technical_indicators,
                price_chart_url=None  # Will be generated separately
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            raise
    
    def _calculate_score(self, rsi: float, macd: float, sma_20: float, sma_50: float, price: float) -> float:
        """Calculate recommendation score based on technical indicators"""
        score = 0.0
        
        # RSI scoring
        if rsi < 30:  # Oversold
            score += 0.3
        elif rsi > 70:  # Overbought
            score -= 0.3
        elif 40 <= rsi <= 60:  # Neutral
            score += 0.1
        
        # MACD scoring
        if macd > 0:
            score += 0.2
        else:
            score -= 0.2
        
        # SMA scoring
        if price > sma_20 > sma_50:  # Bullish
            score += 0.3
        elif price < sma_20 < sma_50:  # Bearish
            score -= 0.3
        elif sma_20 < price < sma_50:  # Mixed
            score += 0.1
        
        # Normalize to -1 to 1 range
        return max(-1, min(1, score))
    
    def _get_recommendation_type(self, score: float) -> str:
        """Convert score to recommendation type"""
        if score >= 0.7:
            return 'Strong Buy'
        elif score >= 0.3:
            return 'Buy'
        elif score >= -0.3:
            return 'Hold'
        elif score >= -0.7:
            return 'Sell'
        else:
            return 'Strong Sell'
    
    def _calculate_indicators_consistency(self, rsi: float, macd: float, sma_20: float, sma_50: float, price: float) -> float:
        """Calculate how consistent the indicators are"""
        consistency_score = 0.0
        total_checks = 0
        
        # RSI and MACD consistency
        rsi_bullish = 30 <= rsi <= 70
        macd_bullish = macd > 0
        if rsi_bullish == macd_bullish:
            consistency_score += 1
        total_checks += 1
        
        # Price and SMA consistency
        price_above_sma20 = price > sma_20
        sma20_above_sma50 = sma_20 > sma_50
        if price_above_sma20 == sma20_above_sma50:
            consistency_score += 1
        total_checks += 1
        
        return consistency_score / total_checks if total_checks > 0 else 0.5
    
    def _generate_reasoning(self, recommendation: str, rsi: float, macd: float, sma_20: float, sma_50: float, score: float) -> str:
        """Generate detailed reasoning for the recommendation"""
        reasons = []
        
        # RSI reasoning
        if rsi < 30:
            reasons.append(f"RSI indicates oversold conditions ({rsi:.1f})")
        elif rsi > 70:
            reasons.append(f"RSI indicates overbought conditions ({rsi:.1f})")
        else:
            reasons.append(f"RSI is neutral ({rsi:.1f})")
        
        # MACD reasoning
        if macd > 0:
            reasons.append(f"MACD shows bullish momentum ({macd:.3f})")
        else:
            reasons.append(f"MACD shows bearish momentum ({macd:.3f})")
        
        # SMA reasoning
        if sma_20 > sma_50:
            reasons.append(f"20-day SMA ({sma_20:.2f}) above 50-day SMA ({sma_50:.2f})")
        else:
            reasons.append(f"20-day SMA ({sma_20:.2f}) below 50-day SMA ({sma_50:.2f})")
        
        # Overall score
        reasons.append(f"Overall technical score: {score:.2f}")
        
        return "; ".join(reasons)

def run_enhanced_analysis(symbols: List[str]) -> List[Recommendation]:
    """Run enhanced analysis on multiple symbols"""
    recommender = EnhancedRecommender()
    recommendations = []
    
    for symbol in symbols:
        try:
            recommendation = recommender.analyze_stock(symbol)
            recommendations.append(recommendation)
            logger.info(f"Successfully analyzed {symbol}")
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {str(e)}")
            continue
    
    return recommendations
