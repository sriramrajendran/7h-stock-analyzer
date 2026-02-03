"""
Stock Recommendation Engine - Migrated from BatchStockAnalyzer
"""

import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import MACD, EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import random
import warnings
warnings.filterwarnings('ignore')


class StockRecommendationEngine:
    """Core recommendation engine for stock analysis"""
    
    def __init__(self, symbols: List[str], period: str = "6mo"):
        self.symbols = [s.upper().strip() for s in symbols if s.strip()]
        self.period = period if period != "1y" else "6mo"
        self.data_cache = {}
        self.ticker_cache = {}
    
    def fetch_all_data(self) -> Dict[str, bool]:
        """Fetch data for all symbols"""
        results = {}
        
        # Check which symbols we already have cached
        uncached_symbols = [s for s in self.symbols if s not in self.data_cache]
        
        if not uncached_symbols:
            return {symbol: True for symbol in self.symbols}
        
        # Process in batches to avoid rate limits
        batch_size = 50
        for i in range(0, len(uncached_symbols), batch_size):
            batch_symbols = uncached_symbols[i:i + batch_size]
            batch_results = self._fetch_batch(batch_symbols)
            results.update(batch_results)
            
            # Add delay between batches
            if i + batch_size < len(uncached_symbols):
                delay = random.uniform(1.0, 2.0)
                time.sleep(delay)
        
        # Add cached symbols
        for symbol in self.symbols:
            if symbol in self.data_cache and symbol not in results:
                results[symbol] = True
        
        return results
    
    def _fetch_batch(self, symbols: List[str]) -> Dict[str, bool]:
        """Fetch data for a batch of symbols"""
        results = {}
        
        try:
            data = yf.download(
                symbols,
                period=self.period,
                group_by='ticker',
                auto_adjust=True,
                prepost=False,
                threads=True,
                timeout=30
            )
            
            # Handle single symbol case
            if len(symbols) == 1:
                symbol = symbols[0]
                if not data.empty:
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = [col[1] for col in data.columns]
                    
                    if all(col in data.columns for col in ['Close', 'High', 'Low', 'Volume']):
                        self.data_cache[symbol] = data
                        self.ticker_cache[symbol] = yf.Ticker(symbol)
                        results[symbol] = True
                    else:
                        results[symbol] = False
                else:
                    results[symbol] = False
                return results
            
            # Process multi-symbol data
            for symbol in symbols:
                try:
                    if symbol in data.columns:
                        symbol_data = data[symbol]
                        
                        if not symbol_data.empty and len(symbol_data) >= 14:
                            if all(col in symbol_data.columns for col in ['Close', 'High', 'Low', 'Volume']):
                                self.data_cache[symbol] = symbol_data
                                self.ticker_cache[symbol] = yf.Ticker(symbol)
                                results[symbol] = True
                            else:
                                results[symbol] = False
                        else:
                            results[symbol] = False
                    else:
                        results[symbol] = False
                        
                except Exception as e:
                    print(f"Error processing {symbol}: {str(e)}")
                    results[symbol] = False
                    
        except Exception as e:
            print(f"Error fetching batch data: {str(e)}")
            for symbol in symbols:
                results[symbol] = False
        
        return results
    
    def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """Analyze a single symbol"""
        if symbol not in self.data_cache:
            return None
        
        try:
            data = self.data_cache[symbol]
            ticker = self.ticker_cache.get(symbol)
            
            if data is None or data.empty or len(data) < 2:
                return {'error': 'Insufficient data for analysis'}
            
            # Calculate indicators
            indicators = self._calculate_indicators(data)
            if not indicators:
                return {'error': 'Failed to calculate indicators'}
            
            # Get fundamental data
            fundamental = self._get_fundamental_data(ticker)
            
            # Get recommendation
            recommendation = self._get_recommendation(indicators)
            
            # Calculate target and stop loss prices based on recommendation
            target_price, stop_loss = self._calculate_price_targets(indicators, recommendation['recommendation'])
            
            # Create summary
            summary = {
                'symbol': symbol,
                'company_name': ticker.info.get('longName', 'N/A') if ticker and hasattr(ticker, 'info') else 'N/A',
                'current_price': round(indicators.get('Current_Price', 0), 2),
                'price_change_pct': round(indicators.get('Price_Change_Pct', 0), 2),
                'price_change_1d_pct': round(indicators.get('Price_Change_1d_Pct', 0), 2),
                'price_change_1w_pct': round(indicators.get('Price_Change_1w_Pct', 0), 2),
                'price_change_1m_pct': round(indicators.get('Price_Change_1m_Pct', 0), 2),
                'price_change_6m_pct': round(indicators.get('Price_Change_6m_Pct', 0), 2),
                'price_change_1y_pct': round(indicators.get('Price_Change_1y_Pct', 0), 2),
                'rsi': round(indicators.get('RSI', 0), 2) if indicators.get('RSI') is not None else 0,
                'macd': round(indicators.get('MACD', 0), 2) if indicators.get('MACD') is not None else 0,
                'macd_signal': round(indicators.get('MACD_Signal', 0), 2) if indicators.get('MACD_Signal') is not None else 0,
                'sma_20': round(indicators.get('SMA_20', 0), 2) if indicators.get('SMA_20') is not None else 0,
                'sma_50': round(indicators.get('SMA_50', 0), 2) if indicators.get('SMA_50') is not None else 0,
                'sma_200': round(indicators.get('SMA_200', 0), 2) if indicators.get('SMA_200') is not None else 0,
                'bb_upper': round(indicators.get('BB_Upper', 0), 2) if indicators.get('BB_Upper') is not None else 0,
                'bb_lower': round(indicators.get('BB_Lower', 0), 2) if indicators.get('BB_Lower') is not None else 0,
                'target_price': round(target_price, 2),
                'stop_loss': round(stop_loss, 2),
                'fundamental': fundamental
            }
            
            return {
                'summary': summary,
                'recommendation': recommendation,
                'indicators': indicators
            }
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {str(e)}")
            return {'error': f'Analysis failed: {str(e)}'}
    
    def analyze_all(self) -> List[Dict]:
        """Analyze all symbols and return recommendations"""
        recommendations = []
        
        # Fetch all data
        fetch_results = self.fetch_all_data()
        
        # Analyze each successful symbol
        for symbol in self.symbols:
            if fetch_results.get(symbol, False):
                analysis = self.analyze_symbol(symbol)
                if analysis and 'error' not in analysis:
                    summary = analysis['summary']
                    recommendation = analysis['recommendation']
                    
                    # Only include BUY recommendations for daily runs
                    if 'BUY' in recommendation['recommendation']:
                        recommendations.append({
                            'symbol': symbol,
                            'company': summary.get('company_name', 'N/A'),
                            'price': summary.get('current_price', 0),
                            'change_pct': summary.get('price_change_pct', 0),
                            'rsi': summary.get('rsi', 0),
                            'macd': summary.get('macd', 0),
                            'sma_20': summary.get('sma_20', 0),
                            'sma_50': summary.get('sma_50', 0),
                            'recommendation': recommendation['recommendation'],
                            'score': recommendation['score'],
                            'reasoning': recommendation['reasoning'],
                            'target_price': summary.get('target_price', 0),
                            'stop_loss': summary.get('stop_loss', 0),
                            'fundamental': summary.get('fundamental', {}),
                            'timestamp': datetime.utcnow().isoformat()
                        })
        
        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations
    
    def _calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate technical indicators"""
        indicators = {}
        
        try:
            # Price data
            indicators['Current_Price'] = data['Close'].iloc[-1]
            
            # Price changes
            if len(data) >= 2:
                prev_close = data['Close'].iloc[-2]
                indicators['Price_Change_Pct'] = ((data['Close'].iloc[-1] - prev_close) / prev_close) * 100
            else:
                indicators['Price_Change_Pct'] = 0
            
            indicators['Price_Change_1d_Pct'] = indicators['Price_Change_Pct']
            
            # Different period changes
            if len(data) >= 6:
                week_ago_close = data['Close'].iloc[-6]
                indicators['Price_Change_1w_Pct'] = ((data['Close'].iloc[-1] - week_ago_close) / week_ago_close) * 100
            else:
                indicators['Price_Change_1w_Pct'] = 0
                
            if len(data) >= 22:
                month_ago_close = data['Close'].iloc[-22]
                indicators['Price_Change_1m_Pct'] = ((data['Close'].iloc[-1] - month_ago_close) / month_ago_close) * 100
            else:
                indicators['Price_Change_1m_Pct'] = 0
                
            if len(data) >= 126:
                six_months_ago_close = data['Close'].iloc[-127]
                indicators['Price_Change_6m_Pct'] = ((data['Close'].iloc[-1] - six_months_ago_close) / six_months_ago_close) * 100
            else:
                indicators['Price_Change_6m_Pct'] = 0
                
            if len(data) >= 253:
                year_ago_close = data['Close'].iloc[-253]
                indicators['Price_Change_1y_Pct'] = ((data['Close'].iloc[-1] - year_ago_close) / year_ago_close) * 100
            elif len(data) >= 50:
                earliest_close = data['Close'].iloc[0]
                days_available = len(data)
                annualized_change = ((data['Close'].iloc[-1] - earliest_close) / earliest_close) * 100
                indicators['Price_Change_1y_Pct'] = annualized_change * (252 / days_available)
            else:
                indicators['Price_Change_1y_Pct'] = 0
            
            # Moving Averages
            if len(data) >= 20:
                sma_20 = SMAIndicator(close=data['Close'], window=20)
                sma_20_series = sma_20.sma_indicator()
                indicators['SMA_20'] = sma_20_series.iloc[-1] if len(sma_20_series.dropna()) > 0 else None
            else:
                indicators['SMA_20'] = None
                
            if len(data) >= 50:
                sma_50 = SMAIndicator(close=data['Close'], window=50)
                sma_50_series = sma_50.sma_indicator()
                indicators['SMA_50'] = sma_50_series.iloc[-1] if len(sma_50_series.dropna()) > 0 else None
            else:
                indicators['SMA_50'] = None
                
            if len(data) >= 200:
                sma_200 = SMAIndicator(close=data['Close'], window=200)
                sma_200_series = sma_200.sma_indicator()
                indicators['SMA_200'] = sma_200_series.iloc[-1] if len(sma_200_series.dropna()) > 0 else None
            else:
                indicators['SMA_200'] = None
            
            # MACD
            if len(data) >= 26:
                macd = MACD(close=data['Close'])
                macd_series = macd.macd()
                macd_signal_series = macd.macd_signal()
                
                indicators['MACD'] = macd_series.iloc[-1] if len(macd_series.dropna()) > 0 else None
                indicators['MACD_Signal'] = macd_signal_series.iloc[-1] if len(macd_signal_series.dropna()) > 0 else None
            else:
                indicators['MACD'] = None
                indicators['MACD_Signal'] = None
            
            # RSI
            rsi = RSIIndicator(close=data['Close'], window=14)
            rsi_series = rsi.rsi()
            indicators['RSI'] = rsi_series.iloc[-1] if len(rsi_series.dropna()) > 0 else None
            
            # Bollinger Bands
            if len(data) >= 20:
                bb = BollingerBands(close=data['Close'], window=20, window_dev=2)
                bb_upper_series = bb.bollinger_hband()
                bb_lower_series = bb.bollinger_lband()
                
                indicators['BB_Upper'] = bb_upper_series.iloc[-1] if len(bb_upper_series.dropna()) > 0 else None
                indicators['BB_Lower'] = bb_lower_series.iloc[-1] if len(bb_lower_series.dropna()) > 0 else None
            else:
                indicators['BB_Upper'] = None
                indicators['BB_Lower'] = None
            
        except Exception as e:
            print(f"Error calculating indicators: {str(e)}")
        
        return indicators
    
    def _get_fundamental_data(self, ticker) -> Dict:
        """Get fundamental analysis data"""
        if not ticker:
            return {}
        
        try:
            info = {}
            try:
                info = ticker.info
                if not info or (isinstance(info, dict) and len(info) < 5):
                    try:
                        fast_info = ticker.fast_info
                        if fast_info and isinstance(fast_info, dict):
                            info.update(fast_info)
                    except:
                        pass
            except Exception:
                try:
                    info = ticker.fast_info or {}
                except:
                    info = {}
            
            def safe_get(keys, default='N/A'):
                if isinstance(keys, str):
                    keys = [keys]
                
                for key in keys:
                    value = info.get(key)
                    if value is not None and value != '':
                        if isinstance(value, str) and value.lower() in ['none', 'null', '']:
                            continue
                        return value
                return default
            
            # Market cap formatting
            market_cap = safe_get(['marketCap', 'market_cap', 'totalMarketCap'], 0)
            if isinstance(market_cap, (int, float)) and market_cap > 0:
                if market_cap >= 1e12:
                    market_cap_str = f"${market_cap/1e12:.2f}T"
                elif market_cap >= 1e9:
                    market_cap_str = f"${market_cap/1e9:.2f}B"
                elif market_cap >= 1e6:
                    market_cap_str = f"${market_cap/1e6:.2f}M"
                else:
                    market_cap_str = f"${market_cap:,.0f}"
            else:
                market_cap_str = 'N/A'
            
            return {
                'pe_ratio': safe_get(['trailingPE', 'trailingP/E', 'peRatio', 'pe'], 'N/A'),
                'market_cap': market_cap_str,
                'sector': safe_get(['sector'], 'N/A'),
                'industry': safe_get(['industry'], 'N/A'),
                'volume': safe_get(['volume'], 'N/A'),
                'avg_volume': safe_get(['averageVolume'], 'N/A'),
                'beta': safe_get(['beta'], 'N/A')
            }
            
        except Exception as e:
            print(f"Error getting fundamental data: {str(e)}")
            return {}
    
    def _get_recommendation(self, indicators: Dict) -> Dict:
        """Generate buy/sell/hold recommendation"""
        score = 0
        reasoning = []
        
        # RSI analysis
        rsi = indicators.get('RSI')
        if rsi is not None:
            if rsi < 30:
                score += 2
                reasoning.append("RSI oversold")
            elif rsi < 50:
                score += 1
                reasoning.append("RSI favorable")
            elif rsi > 70:
                score -= 2
                reasoning.append("RSI overbought")
        
        # MACD analysis
        macd = indicators.get('MACD')
        macd_signal = indicators.get('MACD_Signal')
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                score += 1
                reasoning.append("MACD bullish")
            else:
                score -= 1
                reasoning.append("MACD bearish")
        
        # Moving average analysis
        sma_20 = indicators.get('SMA_20')
        sma_50 = indicators.get('SMA_50')
        current_price = indicators.get('Current_Price')
        
        if current_price and sma_20:
            if current_price > sma_20:
                score += 1
                reasoning.append("Above SMA 20")
            else:
                score -= 1
                reasoning.append("Below SMA 20")
        
        if current_price and sma_50:
            if current_price > sma_50:
                score += 1
                reasoning.append("Above SMA 50")
            else:
                score -= 1
                reasoning.append("Below SMA 50")
        
        # Price momentum
        price_change_1w = indicators.get('Price_Change_1w_Pct', 0)
        price_change_1m = indicators.get('Price_Change_1m_Pct', 0)
        
        if price_change_1w > 0:
            score += 0.5
            reasoning.append("Weekly gain")
        
        if price_change_1m > 0:
            score += 0.5
            reasoning.append("Monthly gain")
        
        # Determine recommendation
        if score >= 3:
            recommendation = "STRONG_BUY"
        elif score >= 1:
            recommendation = "BUY"
        elif score <= -3:
            recommendation = "STRONG_SELL"
        elif score <= -1:
            recommendation = "SELL"
        else:
            recommendation = "HOLD"
        
        return {
            'recommendation': recommendation,
            'score': score,
            'reasoning': '; '.join(reasoning) if reasoning else "Neutral"
        }
    
    def _calculate_price_targets(self, indicators: Dict, recommendation: str) -> tuple:
        """
        Calculate target price and stop loss based on recommendation
        
        Args:
            indicators: Technical indicators
            recommendation: Recommendation type
            
        Returns:
            tuple: (target_price, stop_loss)
        """
        current_price = indicators.get('Current_Price', 0)
        
        if current_price <= 0:
            return 0, 0
        
        # Calculate target and stop loss based on recommendation type
        if recommendation == "STRONG_BUY":
            target_price = current_price * 1.20  # +20%
            stop_loss = current_price * 0.90    # -10%
        elif recommendation == "BUY":
            target_price = current_price * 1.10  # +10%
            stop_loss = current_price * 0.95    # -5%
        elif recommendation == "HOLD":
            target_price = current_price         # Same price
            stop_loss = current_price * 0.90    # -10%
        elif recommendation == "SELL":
            target_price = current_price * 0.90  # -10%
            stop_loss = current_price * 1.05     # +5%
        elif recommendation == "STRONG_SELL":
            target_price = current_price * 0.80  # -20%
            stop_loss = current_price * 1.10     # +10%
        else:
            target_price = current_price
            stop_loss = current_price * 0.95
        
        return target_price, stop_loss


def run_engine(symbols: List[str] = None) -> List[Dict]:
    """Main entry point for running the recommendation engine"""
    if symbols is None:
        # Load default symbols from config
        symbols = []
        try:
            with open('input/config_portfolio.txt', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        symbols.append(line.upper())
        except:
            # Fallback symbols if config fails
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    engine = StockRecommendationEngine(symbols)
    recommendations = engine.analyze_all()
    
    return recommendations
