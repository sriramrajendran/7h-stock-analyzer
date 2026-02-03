"""
Recommendation Engine Module - Converts aggregated scores into BUY/HOLD/SELL recommendations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Converts signal scores into actionable trading recommendations"""
    
    def __init__(self):
        # Recommendation thresholds
        self.thresholds = {
            'strong_buy': 0.5,
            'buy': 0.2,
            'hold': -0.2,
            'sell': -0.5,
            'strong_sell': -1.0
        }
        
        # Target price calculations based on recommendation type
        self.target_multipliers = {
            'Strong Buy': 1.20,    # +20%
            'Buy': 1.10,           # +10%
            'Hold': 1.02,          # +2% (small upside potential)
            'Sell': 0.95,          # -5% (stop loss)
            'Strong Sell': 0.80    # -20% (stop loss)
        }
        
        # Stop loss percentages (lower than profit percentages for better risk/reward)
        self.stop_loss_percentages = {
            'Strong Buy': 0.08,    # 8% stop loss (vs 20% profit)
            'Buy': 0.06,           # 6% stop loss (vs 10% profit)
            'Hold': 0.015,         # 1.5% stop loss (vs 2% profit)
            'Sell': 0.04,          # 4% stop loss (vs 5% profit from current)
            'Strong Sell': 0.06    # 6% stop loss (vs 20% profit from current)
        }
    
    def generate_recommendations(self, df: pd.DataFrame, ticker: str) -> Dict:
        """Generate comprehensive recommendation for a ticker"""
        if df.empty:
            return self._empty_recommendation(ticker)
        
        try:
            latest_data = df.iloc[-1]
            current_price = latest_data.get('Close', 0)
            
            if current_price <= 0:
                logger.warning(f"Invalid price for {ticker}: {current_price}")
                return self._empty_recommendation(ticker)
            
            # Get final score and recommendation
            final_score = latest_data.get('Final_Score_Normalized', 0)
            recommendation = self._score_to_recommendation(final_score)
            
            # Calculate target and stop loss prices
            target_price = self._calculate_target_price(current_price, recommendation)
            stop_loss = self._calculate_stop_loss(current_price, recommendation)
            
            # Determine confidence level
            confidence = self._calculate_confidence(final_score, df)
            
            # Get technical indicators used
            technical_indicators = self._get_technical_indicators(df)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(df, final_score, recommendation)
            
            # Calculate price change percentage
            change_pct = self._calculate_price_change(df)
            
            # Create recommendation object
            recommendation_data = {
                'symbol': ticker,
                'company': self._get_company_name(ticker),
                'price': float(current_price),
                'change_pct': float(change_pct),
                'recommendation': recommendation,
                'score': float(final_score),
                'target_price': float(target_price),
                'stop_loss': float(stop_loss),
                'confidence_level': confidence,
                'technical_indicators': technical_indicators,
                'reasoning': reasoning,
                'timestamp': datetime.utcnow().isoformat(),
                
                # Additional data for enhanced features
                'signal_strength': latest_data.get('Signal_Strength', 'Moderate'),
                'signal_direction': latest_data.get('Signal_Direction', 'Neutral'),
                'trend_score': float(latest_data.get('Trend_Signal', 0)),
                'momentum_score': float(latest_data.get('Momentum_Signal', 0)),
                'volatility_score': float(latest_data.get('Volatility_Signal', 0)),
                'volume_score': float(latest_data.get('Volume_Signal_Combined', 0)),
                
                # Technical indicator values
                'rsi': float(latest_data.get('RSI_14', 0)),
                'macd': float(latest_data.get('MACD', 0)),
                'sma_20': float(latest_data.get('SMA_20', latest_data.get('SMA_50', 0))),
                'sma_50': float(latest_data.get('SMA_50', 0)),
                
                # Fundamental data placeholder (can be enhanced later)
                'fundamental': {
                    'market_cap': None,
                    'pe_ratio': None,
                    'eps': None,
                    'dividend_yield': None
                }
            }
            
            logger.info(f"Generated {recommendation} for {ticker} (score: {final_score:.3f})")
            return recommendation_data
            
        except Exception as e:
            logger.error(f"Error generating recommendation for {ticker}: {str(e)}")
            return self._empty_recommendation(ticker)
    
    def _score_to_recommendation(self, score: float) -> str:
        """Convert normalized score to recommendation"""
        if score >= self.thresholds['strong_buy']:
            return 'Strong Buy'
        elif score >= self.thresholds['buy']:
            return 'Buy'
        elif score >= self.thresholds['hold']:
            return 'Hold'
        elif score >= self.thresholds['sell']:
            return 'Sell'
        else:
            return 'Strong Sell'
    
    def _calculate_target_price(self, current_price: float, recommendation: str) -> float:
        """Calculate target price based on recommendation type"""
        multiplier = self.target_multipliers.get(recommendation, 1.0)
        return round(current_price * multiplier, 2)
    
    def _calculate_stop_loss(self, current_price: float, recommendation: str) -> float:
        """Calculate stop loss price based on recommendation type"""
        # For buy recommendations, stop loss is below current price
        if recommendation in ['Strong Buy', 'Buy', 'Hold']:
            percentage = self.stop_loss_percentages.get(recommendation, 0.05)
            return round(current_price * (1 - percentage), 2)
        # For sell recommendations, stop loss is above current price
        else:
            percentage = self.stop_loss_percentages.get(recommendation, 0.05)
            return round(current_price * (1 + percentage), 2)
    
    def _calculate_confidence(self, score: float, df: pd.DataFrame) -> str:
        """Calculate confidence level based on score strength and data quality"""
        # Base confidence on score magnitude
        score_magnitude = abs(score)
        
        if score_magnitude >= 0.7:
            base_confidence = 'High'
        elif score_magnitude >= 0.4:
            base_confidence = 'Medium'
        else:
            base_confidence = 'Low'
        
        # Adjust confidence based on signal consistency
        if len(df) >= 10:
            recent_scores = df['Final_Score_Normalized'].tail(10)
            score_consistency = 1 - recent_scores.std()
            
            # Boost confidence if signals are consistent
            if score_consistency > 0.8 and base_confidence == 'Medium':
                base_confidence = 'High'
            elif score_consistency < 0.4 and base_confidence == 'High':
                base_confidence = 'Medium'
        
        return base_confidence
    
    def _get_technical_indicators(self, df: pd.DataFrame) -> List[str]:
        """Get list of technical indicators used in analysis"""
        indicators = []
        
        # Check which indicators are available
        indicator_checks = {
            'RSI': 'RSI_14',
            'MACD': 'MACD',
            'EMA': 'EMA_12',
            'SMA': 'SMA_50',
            'Bollinger Bands': 'BB_Position',
            'ATR': 'ATR_14',
            'OBV': 'OBV',
            'ADX': 'ADX',
            'Stochastic': 'Stoch_K',
            'Volume Analysis': 'Volume_Ratio'
        }
        
        for name, column in indicator_checks.items():
            if column in df.columns and not df[column].isna().all():
                indicators.append(name)
        
        return indicators
    
    def _generate_reasoning(self, df: pd.DataFrame, score: float, recommendation: str) -> str:
        """Generate detailed reasoning for the recommendation"""
        if df.empty:
            return "Insufficient data for analysis"
        
        latest = df.iloc[-1]
        reasons = []
        
        # Trend-based reasoning
        trend_signal = latest.get('Trend_Signal', 0)
        if trend_signal > 0.2:
            reasons.append("Positive trend indicators (EMA/MACD bullish)")
        elif trend_signal < -0.2:
            reasons.append("Negative trend indicators (EMA/MACD bearish)")
        
        # Momentum-based reasoning
        momentum_signal = latest.get('Momentum_Signal', 0)
        rsi = latest.get('RSI_14', 50)
        
        if momentum_signal > 0.2:
            if rsi < 30:
                reasons.append("Oversold momentum with RSI recovery potential")
            else:
                reasons.append("Strong momentum indicators")
        elif momentum_signal < -0.2:
            if rsi > 70:
                reasons.append("Overbought momentum with RSI divergence risk")
            else:
                reasons.append("Weak momentum indicators")
        
        # Volatility-based reasoning
        volatility_signal = latest.get('Volatility_Signal', 0)
        bb_position = latest.get('BB_Position', 0.5)
        
        if volatility_signal > 0.2:
            reasons.append("Low volatility with potential breakout setup")
        elif volatility_signal < -0.2:
            reasons.append("High volatility with elevated risk")
        
        # Volume-based reasoning
        volume_signal = latest.get('Volume_Signal_Combined', 0)
        if volume_signal > 0.2:
            reasons.append("Strong volume confirmation")
        elif volume_signal < -0.2:
            reasons.append("Weak volume support")
        
        # Combine reasons based on recommendation
        if recommendation in ['Strong Buy', 'Buy']:
            if not reasons:
                reasons.append("Multiple technical indicators suggest bullish momentum")
            reasoning = "Bullish recommendation based on: " + "; ".join(reasons[:3])
        elif recommendation in ['Strong Sell', 'Sell']:
            if not reasons:
                reasons.append("Multiple technical indicators suggest bearish momentum")
            reasoning = "Bearish recommendation based on: " + "; ".join(reasons[:3])
        else:
            if not reasons:
                reasons.append("Mixed technical signals with no clear direction")
            reasoning = "Neutral recommendation based on: " + "; ".join(reasons[:3])
        
        # Add score context
        reasoning += f" (Score: {score:.3f})"
        
        return reasoning
    
    def _calculate_price_change(self, df: pd.DataFrame) -> float:
        """Calculate price change percentage"""
        if len(df) < 2:
            return 0.0
        
        current_price = df.iloc[-1]['Close']
        previous_price = df.iloc[-2]['Close']
        
        if previous_price == 0:
            return 0.0
        
        return ((current_price - previous_price) / previous_price) * 100
    
    def _get_company_name(self, ticker: str) -> str:
        """Get company name for ticker (placeholder for now)"""
        # This could be enhanced with a company name lookup service
        company_names = {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.',
            'META': 'Meta Platforms Inc.',
            'NVDA': 'NVIDIA Corporation',
            'JPM': 'JPMorgan Chase & Co.',
            'V': 'Visa Inc.',
            'JNJ': 'Johnson & Johnson'
        }
        
        return company_names.get(ticker.upper(), ticker.upper())
    
    def _empty_recommendation(self, ticker: str) -> Dict:
        """Return empty recommendation for error cases"""
        return {
            'symbol': ticker,
            'company': self._get_company_name(ticker),
            'price': 0.0,
            'change_pct': 0.0,
            'recommendation': 'Hold',
            'score': 0.0,
            'target_price': 0.0,
            'stop_loss': 0.0,
            'confidence_level': 'Low',
            'technical_indicators': [],
            'reasoning': 'Insufficient data for analysis',
            'timestamp': datetime.utcnow().isoformat(),
            'signal_strength': 'Moderate',
            'signal_direction': 'Neutral',
            'trend_score': 0.0,
            'momentum_score': 0.0,
            'volatility_score': 0.0,
            'volume_score': 0.0,
            'rsi': 0.0,
            'macd': 0.0,
            'sma_20': 0.0,
            'sma_50': 0.0,
            'fundamental': {}
        }
    
    def batch_recommendations(self, data_dict: Dict[str, pd.DataFrame]) -> List[Dict]:
        """Generate recommendations for multiple tickers"""
        recommendations = []
        
        for ticker, df in data_dict.items():
            try:
                recommendation = self.generate_recommendations(df, ticker)
                recommendations.append(recommendation)
            except Exception as e:
                logger.error(f"Error processing {ticker}: {str(e)}")
                recommendations.append(self._empty_recommendation(ticker))
        
        return recommendations
    
    def get_recommendation_summary(self, recommendations: List[Dict]) -> Dict:
        """Get summary statistics for recommendations"""
        if not recommendations:
            return {}
        
        # Count recommendation types
        rec_counts = {}
        score_sum = 0
        confidence_counts = {'High': 0, 'Medium': 0, 'Low': 0}
        
        for rec in recommendations:
            rec_type = rec.get('recommendation', 'Hold')
            rec_counts[rec_type] = rec_counts.get(rec_type, 0) + 1
            
            score_sum += rec.get('score', 0)
            
            confidence = rec.get('confidence_level', 'Low')
            confidence_counts[confidence] += 1
        
        return {
            'total_recommendations': len(recommendations),
            'recommendation_distribution': rec_counts,
            'average_score': score_sum / len(recommendations) if recommendations else 0,
            'confidence_distribution': confidence_counts,
            'timestamp': datetime.utcnow().isoformat()
        }
