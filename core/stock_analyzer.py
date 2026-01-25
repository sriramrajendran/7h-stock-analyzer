"""
Stock Technical Analysis and Recommendation System
"""

try:
    import yfinance as yf
except ImportError as e:
    print(f"Error: Failed to import yfinance. Please install it using: pip install yfinance")
    print(f"Details: {e}")
    raise

try:
    import pandas as pd
    import numpy as np
except ImportError as e:
    print(f"Error: Failed to import pandas or numpy. Please install using: pip install pandas numpy")
    print(f"Details: {e}")
    raise

try:
    from ta.trend import MACD, EMAIndicator, SMAIndicator
    from ta.momentum import RSIIndicator, StochasticOscillator
    from ta.volatility import BollingerBands, AverageTrueRange
    from ta.volume import OnBalanceVolumeIndicator
except ImportError as e:
    print(f"Error: Failed to import ta library. Please install it using: pip install ta")
    print(f"Details: {e}")
    raise

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class StockAnalyzer:
    """Main class for stock technical analysis"""
    
    def __init__(self, symbol: str, period: str = "1y"):
        """
        Initialize stock analyzer
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            period: Data period ('1mo', '3mo', '6mo', '1y', '2y', '5y')
        """
        self.symbol = symbol.upper()
        self.period = period
        self.stock = None
        self.data = None
        self.indicators = {}
        
    def fetch_data(self) -> bool:
        """Fetch stock data from Yahoo Finance"""
        try:
            self.stock = yf.Ticker(self.symbol)
            self.data = self.stock.history(period=self.period)
            
            if self.data.empty:
                print(f"Error: No data found for {self.symbol}")
                return False
                
            # Ensure we have enough data for basic indicators
            if len(self.data) < 14:
                print(f"Warning: Limited data for {self.symbol}. Need at least 14 days for basic indicators.")
                return False
            
            # Try to pre-fetch info to have it ready (non-blocking)
            try:
                # Access info to trigger fetch, but don't wait too long
                _ = self.stock.info
            except:
                pass  # Info fetch failed, but we can still proceed
                
            return True
        except Exception as e:
            print(f"Error fetching data for {self.symbol}: {str(e)}")
            return False
    
    def calculate_indicators(self):
        """Calculate all technical indicators"""
        if self.data is None or self.data.empty:
            return
        
        df = self.data.copy()
        
        # Trend Indicators (only calculate if enough data)
        if len(df) >= 26:
            macd = MACD(close=df['Close'])
            self.indicators['MACD'] = macd.macd().iloc[-1]
            self.indicators['MACD_Signal'] = macd.macd_signal().iloc[-1]
            self.indicators['MACD_Histogram'] = macd.macd_diff().iloc[-1]
        else:
            self.indicators['MACD'] = None
            self.indicators['MACD_Signal'] = None
            self.indicators['MACD_Histogram'] = None
        
        # Moving Averages (only calculate if enough data)
        sma_20 = SMAIndicator(close=df['Close'], window=20)
        if len(df) >= 20:
            self.indicators['SMA_20'] = sma_20.sma_indicator().iloc[-1]
        else:
            self.indicators['SMA_20'] = None
            
        if len(df) >= 50:
            sma_50 = SMAIndicator(close=df['Close'], window=50)
            self.indicators['SMA_50'] = sma_50.sma_indicator().iloc[-1]
        else:
            self.indicators['SMA_50'] = None
            
        if len(df) >= 200:
            sma_200 = SMAIndicator(close=df['Close'], window=200)
            self.indicators['SMA_200'] = sma_200.sma_indicator().iloc[-1]
        else:
            self.indicators['SMA_200'] = None
            
        ema_12 = EMAIndicator(close=df['Close'], window=12)
        ema_26 = EMAIndicator(close=df['Close'], window=26)
        
        if len(df) >= 12:
            self.indicators['EMA_12'] = ema_12.ema_indicator().iloc[-1]
        else:
            self.indicators['EMA_12'] = None
            
        if len(df) >= 26:
            self.indicators['EMA_26'] = ema_26.ema_indicator().iloc[-1]
        else:
            self.indicators['EMA_26'] = None
        
        # Momentum Indicators
        rsi = RSIIndicator(close=df['Close'], window=14)
        self.indicators['RSI'] = rsi.rsi().iloc[-1]
        
        stoch = StochasticOscillator(high=df['High'], low=df['Low'], close=df['Close'])
        self.indicators['Stoch_K'] = stoch.stoch().iloc[-1]
        self.indicators['Stoch_D'] = stoch.stoch_signal().iloc[-1]
        
        # Volatility Indicators (only calculate if enough data)
        if len(df) >= 20:
            bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
            self.indicators['BB_Upper'] = bb.bollinger_hband().iloc[-1]
            self.indicators['BB_Lower'] = bb.bollinger_lband().iloc[-1]
            self.indicators['BB_Middle'] = bb.bollinger_mavg().iloc[-1]
        else:
            self.indicators['BB_Upper'] = None
            self.indicators['BB_Lower'] = None
            self.indicators['BB_Middle'] = None
        
        atr = AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'])
        self.indicators['ATR'] = atr.average_true_range().iloc[-1]
        
        # Volume Indicators
        obv = OnBalanceVolumeIndicator(close=df['Close'], volume=df['Volume'])
        self.indicators['OBV'] = obv.on_balance_volume().iloc[-1]
        
        # Current price and price changes for different periods
        self.indicators['Current_Price'] = df['Close'].iloc[-1]
        self.indicators['Price_Change_Pct'] = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        
        # Calculate price changes for different periods
        self.indicators['Price_Change_1d_Pct'] = self.indicators['Price_Change_Pct']  # Daily change
        
        # Weekly change (5 trading days)
        if len(df) >= 5:
            self.indicators['Price_Change_1w_Pct'] = ((df['Close'].iloc[-1] - df['Close'].iloc[-6]) / df['Close'].iloc[-6]) * 100
        else:
            self.indicators['Price_Change_1w_Pct'] = 0
            
        # Monthly change (21 trading days approximately)
        if len(df) >= 21:
            self.indicators['Price_Change_1m_Pct'] = ((df['Close'].iloc[-1] - df['Close'].iloc[-22]) / df['Close'].iloc[-22]) * 100
        else:
            self.indicators['Price_Change_1m_Pct'] = 0
            
        # 6-month change (126 trading days approximately)
        if len(df) >= 126:
            self.indicators['Price_Change_6m_Pct'] = ((df['Close'].iloc[-1] - df['Close'].iloc[-127]) / df['Close'].iloc[-127]) * 100
        else:
            self.indicators['Price_Change_6m_Pct'] = 0
            
        # 1-year change (252 trading days approximately)
        if len(df) >= 252:
            self.indicators['Price_Change_1y_Pct'] = ((df['Close'].iloc[-1] - df['Close'].iloc[-253]) / df['Close'].iloc[-253]) * 100
        elif len(df) >= 200:  # If we have at least ~200 days, use the earliest available data
            self.indicators['Price_Change_1y_Pct'] = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
        else:
            self.indicators['Price_Change_1y_Pct'] = 0
        
        # Advanced Pattern Analysis
        self.indicators['VCP_Pattern'] = self.detect_vcp_pattern()
        self.indicators['RSI_Divergence'] = self.detect_rsi_divergence()
        self.indicators['MACD_Divergence'] = self.detect_macd_divergence()
        self.indicators['Enhanced_Crossovers'] = self.detect_enhanced_crossovers()
        self.indicators['Breakout_Setup'] = self.detect_breakout_setup()
        
        # Store full dataframes for analysis
        self.data = df
    
    def get_fundamental_indicators(self) -> Dict:
        """Get fundamental analysis indicators"""
        if not self.stock:
            return {}
        
        try:
            # Try to get info, may need to fetch it explicitly with timeout handling
            info = {}
            try:
                # Try regular info first
                info = self.stock.info
                # Sometimes info returns empty dict if not ready
                if not info or (isinstance(info, dict) and len(info) < 5):
                    # Try fast_info as backup
                    try:
                        fast_info = self.stock.fast_info
                        if fast_info and isinstance(fast_info, dict):
                            info.update(fast_info)
                    except:
                        pass
            except Exception as e:
                # If info fails, try fast_info
                try:
                    info = self.stock.fast_info or {}
                except:
                    info = {}
            
            # Continue even if info is minimal - we'll try to get what we can
            
            # Helper function to safely get values with fallbacks
            def safe_get(keys, default='N/A'):
                """Try multiple key names"""
                if isinstance(keys, str):
                    keys = [keys]
                
                for key in keys:
                    value = info.get(key)
                    if value is not None and value != '':
                        # Handle string 'None' or empty strings
                        if isinstance(value, str) and value.lower() in ['none', 'null', '']:
                            continue
                        return value
                return default
            
            # Get market cap with multiple attempts
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
            
            # Get current price from data if available
            current_price = self.indicators.get('Current_Price', 0) if self.indicators else 0
            
            fundamental = {
                'pe_ratio': safe_get(['trailingPE', 'trailingP/E', 'peRatio', 'pe']),
                'forward_pe': safe_get(['forwardPE', 'forwardP/E', 'forwardPeRatio']),
                'pb_ratio': safe_get(['priceToBook', 'priceToBookRatio', 'pb', 'p/b']),
                'dividend_yield': safe_get(['dividendYield', 'dividend_yield', 'yield', 'trailingAnnualDividendYield', 'fiveYearAvgDividendYield']),
                'market_cap': market_cap_str,
                'market_cap_raw': market_cap if isinstance(market_cap, (int, float)) and market_cap > 0 else 0,
                'eps': safe_get(['trailingEps', 'epsTrailing12Months', 'eps', 'earningsPerShare']),
                'revenue_growth': safe_get(['revenueGrowth', 'revenue_growth', 'quarterlyRevenueGrowth', 'revenueGrowthRate']),
                'earnings_growth': safe_get(['earningsQuarterlyGrowth', 'earningsGrowth', 'quarterlyEarningsGrowth', 'earnings_growth']),
                'debt_to_equity': safe_get(['debtToEquity', 'debtToEquityRatio', 'totalDebt/totalEquity']),
                'roe': safe_get(['returnOnEquity', 'returnOnEquityTTM', 'roe']),
                'profit_margin': safe_get(['profitMargins', 'profitMargin', 'profit_margin', 'netProfitMargin']),
                '52_week_high': safe_get(['fiftyTwoWeekHigh', '52WeekHigh', 'fifty_two_week_high']),
                '52_week_low': safe_get(['fiftyTwoWeekLow', '52WeekLow', 'fifty_two_week_low']),
                'avg_volume': safe_get(['averageVolume', 'averageVolume10days', 'avgVolume']),
                'beta': safe_get(['beta', 'beta3Year']),
            }
            
            # Format dividend yield - Yahoo Finance returns dividend yield inconsistently:
            # - Sometimes as percentage decimal (0.79 = 0.79%, 0.41 = 0.41%)
            # - Sometimes as actual decimal (0.0238 = 2.38%)
            # - Sometimes trailingAnnualDividendYield is 0 (suspended dividends) but fiveYearAvgDividendYield has historical data
            if isinstance(fundamental['dividend_yield'], (int, float)) and fundamental['dividend_yield'] != 'N/A':
                # If current dividend yield is 0, try to use 5-year average for context
                if fundamental['dividend_yield'] == 0:
                    five_year_avg = safe_get(['fiveYearAvgDividendYield'])
                    if five_year_avg and five_year_avg != 'N/A':
                        fundamental['dividend_yield'] = round(five_year_avg, 2)
                elif fundamental['dividend_yield'] < 0.1:
                    # Convert decimal to percentage
                    fundamental['dividend_yield'] = round(fundamental['dividend_yield'] * 100, 2)
                else:
                    # Already in percentage format, just round
                    fundamental['dividend_yield'] = round(fundamental['dividend_yield'], 2)
            
            for key in ['revenue_growth', 'earnings_growth']:
                if isinstance(fundamental[key], (int, float)) and fundamental[key] != 'N/A':
                    # These are typically already in percentage form (0.028 = 2.8%)
                    if abs(fundamental[key]) < 1:
                        fundamental[key] = round(fundamental[key] * 100, 2)
                    else:
                        fundamental[key] = round(fundamental[key], 2)
            
            # ROE and Profit Margin are already in decimal form and should be converted to percentage
            for key in ['roe', 'profit_margin']:
                if isinstance(fundamental[key], (int, float)) and fundamental[key] != 'N/A':
                    # These are already in decimal form (0.00186 = 0.186%) and need conversion
                    fundamental[key] = round(fundamental[key] * 100, 2)
            
            # Format other numeric values
            for key in ['pe_ratio', 'forward_pe', 'pb_ratio', 'eps', 'debt_to_equity', 'beta', '52_week_high', '52_week_low', 'avg_volume']:
                if isinstance(fundamental[key], (int, float)) and fundamental[key] != 'N/A':
                    fundamental[key] = round(fundamental[key], 2)
            
            # Convert N/A strings back to proper format
            for key in fundamental:
                if fundamental[key] == 'N/A':
                    fundamental[key] = 'N/A'
                elif fundamental[key] == 0 and key not in ['pe_ratio', 'forward_pe', 'pb_ratio', 'eps', 'dividend_yield']:
                    # Some values might legitimately be 0, but for these fields 0 usually means N/A
                    if key in ['pe_ratio', 'forward_pe', 'pb_ratio', 'eps', 'debt_to_equity', 'roe', 'profit_margin', 'beta']:
                        fundamental[key] = 'N/A'
            
            return fundamental
        except Exception as e:
            print(f"Error getting fundamental indicators for {self.symbol}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_recommendation(self) -> Dict:
        """
        Generate stock recommendation based on technical indicators
        
        Returns:
            Dictionary with recommendation, score, and reasoning
        """
        if not self.indicators:
            return {
                'recommendation': 'NEUTRAL',
                'score': 0,
                'reasoning': 'No indicators calculated'
            }
        
        score = 0
        reasons = []
        
        current_price = self.indicators['Current_Price']
        rsi = self.indicators['RSI']
        macd = self.indicators['MACD']
        macd_signal = self.indicators['MACD_Signal']
        macd_hist = self.indicators['MACD_Histogram']
        sma_20 = self.indicators['SMA_20']
        sma_50 = self.indicators['SMA_50']
        sma_200 = self.indicators['SMA_200']
        bb_upper = self.indicators['BB_Upper']
        bb_lower = self.indicators['BB_Lower']
        stoch_k = self.indicators['Stoch_K']
        stoch_d = self.indicators['Stoch_D']
        
        # RSI Analysis
        if rsi < 30:
            score += 2
            reasons.append("RSI indicates oversold condition (RSI < 30)")
        elif rsi > 70:
            score -= 2
            reasons.append("RSI indicates overbought condition (RSI > 70)")
        elif 30 <= rsi <= 50:
            score += 1
            reasons.append("RSI in neutral-bullish range")
        else:
            score -= 1
            reasons.append("RSI in neutral-bearish range")
        
        # MACD Analysis
        if macd is not None and macd_signal is not None and macd_hist is not None:
            if macd > macd_signal and macd_hist > 0:
                score += 2
                reasons.append("MACD bullish crossover detected")
            elif macd < macd_signal and macd_hist < 0:
                score -= 2
                reasons.append("MACD bearish crossover detected")
        
        # Moving Average Analysis
        ma_bullish_signals = 0
        if sma_20 is not None and current_price > sma_20:
            score += 1
            ma_bullish_signals += 1
        if sma_50 is not None and current_price > sma_50:
            score += 1
            ma_bullish_signals += 1
        if sma_200 is not None and current_price > sma_200:
            score += 1
            ma_bullish_signals += 1
        
        total_ma_signals = sum([
            1 if sma_20 is not None else 0,
            1 if sma_50 is not None else 0,
            1 if sma_200 is not None else 0
        ])
        
        if total_ma_signals > 0:
            if ma_bullish_signals == total_ma_signals:
                reasons.append("Price above all available moving averages (bullish)")
            elif ma_bullish_signals == 0:
                score -= 2
                reasons.append("Price below all available moving averages (bearish)")
        
        # Golden Cross / Death Cross (only if both SMAs are available)
        if sma_50 is not None and sma_200 is not None:
            if sma_50 > sma_200:
                score += 1
                reasons.append("Golden Cross pattern (SMA50 > SMA200)")
            else:
                score -= 1
                reasons.append("Death Cross pattern (SMA50 < SMA200)")
        
        # Bollinger Bands Analysis
        if bb_lower is not None and bb_upper is not None:
            if current_price < bb_lower:
                score += 1
                reasons.append("Price near lower Bollinger Band (potential bounce)")
            elif current_price > bb_upper:
                score -= 1
                reasons.append("Price near upper Bollinger Band (potential pullback)")
        
        # Stochastic Oscillator
        if stoch_k is not None and stoch_d is not None:
            if stoch_k < 20 and stoch_d < 20:
                score += 1
                reasons.append("Stochastic indicates oversold")
            elif stoch_k > 80 and stoch_d > 80:
                score -= 1
                reasons.append("Stochastic indicates overbought")
        
        # Advanced Pattern Analysis
        vcp_pattern = self.indicators.get('VCP_Pattern', {})
        rsi_divergence = self.indicators.get('RSI_Divergence', {})
        macd_divergence = self.indicators.get('MACD_Divergence', {})
        enhanced_crossovers = self.indicators.get('Enhanced_Crossovers', {})
        breakout_setup = self.indicators.get('Breakout_Setup', {'qualified': False})
        
        # VCP Pattern Analysis
        if vcp_pattern.get('pattern') == 'STRONG_VCP':
            score += 3
            reasons.append("Strong Volatility Contraction Pattern detected - potential breakout")
        elif vcp_pattern.get('pattern') == 'WEAK_VCP':
            score += 1
            reasons.append("Weak Volatility Contraction Pattern detected")
        
        # RSI Divergence Analysis
        if rsi_divergence.get('divergence') == 'BULLISH':
            score += 2
            reasons.append("Bullish RSI divergence detected - potential upward reversal")
        elif rsi_divergence.get('divergence') == 'BEARISH':
            score -= 2
            reasons.append("Bearish RSI divergence detected - potential downward reversal")
        
        # MACD Divergence Analysis
        if macd_divergence.get('divergence') == 'BULLISH':
            score += 2
            reasons.append("Bullish MACD divergence detected - momentum shift upward")
        elif macd_divergence.get('divergence') == 'BEARISH':
            score -= 2
            reasons.append("Bearish MACD divergence detected - momentum shift downward")
        
        # Enhanced Crossover Analysis
        volume_confirmed = enhanced_crossovers.get('volume_confirmed', [])
        crossover_strength = enhanced_crossovers.get('strength', 0)
        
        if volume_confirmed:
            bullish_volume_confirmed = [c for c in volume_confirmed if 'BULLISH' in c]
            bearish_volume_confirmed = [c for c in volume_confirmed if 'BEARISH' in c]
            
            if bullish_volume_confirmed:
                score += len(bullish_volume_confirmed)
                reasons.append(f"Volume-confirmed bullish crossovers: {', '.join(bullish_volume_confirmed)}")
            
            if bearish_volume_confirmed:
                score -= len(bearish_volume_confirmed)
                reasons.append(f"Volume-confirmed bearish crossovers: {', '.join(bearish_volume_confirmed)}")
        
        # Price momentum
        price_change = self.indicators['Price_Change_Pct']
        if price_change > 2:
            score += 1
            reasons.append("Strong positive price momentum")
        elif price_change < -2:
            score -= 1
            reasons.append("Strong negative price momentum")
        
        # Hybrid strict setup bonus
        if breakout_setup.get('qualified'):
            score += 2
            reasons.append("Hybrid breakout setup qualified: trend aligned, RSI>50, shrinking pullbacks, declining consolidation volume, high-volume breakout")
        
        # Determine recommendation
        if score >= 5:
            recommendation = "STRONG BUY"
        elif score >= 2:
            recommendation = "BUY"
        elif score >= -1:
            recommendation = "HOLD"
        elif score >= -4:
            recommendation = "SELL"
        else:
            recommendation = "STRONG SELL"
        
        return {
            'recommendation': recommendation,
            'score': score,
            'reasoning': reasons,
            'indicators': self.indicators
        }
    
    def get_summary(self) -> Dict:
        """Get a summary of the stock analysis"""
        if not self.indicators:
            return {}
        
        info = self.stock.info if self.stock else {}
        fundamental = self.get_fundamental_indicators()
        
        summary = {
            'symbol': self.symbol,
            'company_name': info.get('longName', 'N/A'),
            'current_price': round(self.indicators['Current_Price'], 2),
            'price_change_pct': round(self.indicators['Price_Change_Pct'], 2),
            'price_change_1d_pct': round(self.indicators['Price_Change_1d_Pct'], 2),
            'price_change_1w_pct': round(self.indicators.get('Price_Change_1w_Pct', 0), 2),
            'price_change_1m_pct': round(self.indicators.get('Price_Change_1m_Pct', 0), 2),
            'price_change_6m_pct': round(self.indicators.get('Price_Change_6m_Pct', 0), 2),
            'price_change_1y_pct': round(self.indicators.get('Price_Change_1y_Pct', 0), 2),
            'rsi': round(self.indicators['RSI'], 2) if self.indicators['RSI'] is not None else 0,
            'macd': round(self.indicators['MACD'], 2) if self.indicators['MACD'] is not None else 0,
            'macd_signal': round(self.indicators['MACD_Signal'], 2) if self.indicators['MACD_Signal'] is not None else 0,
            'sma_20': round(self.indicators['SMA_20'], 2) if self.indicators['SMA_20'] is not None else 0,
            'sma_50': round(self.indicators['SMA_50'], 2) if self.indicators['SMA_50'] is not None else 0,
            'sma_200': round(self.indicators['SMA_200'], 2) if self.indicators['SMA_200'] is not None else 0,
            'bb_upper': round(self.indicators['BB_Upper'], 2) if self.indicators['BB_Upper'] is not None else 0,
            'bb_lower': round(self.indicators['BB_Lower'], 2) if self.indicators['BB_Lower'] is not None else 0,
            # Advanced pattern analysis
            'vcp_pattern': self.indicators.get('VCP_Pattern', {}),
            'rsi_divergence': self.indicators.get('RSI_Divergence', {}),
            'macd_divergence': self.indicators.get('MACD_Divergence', {}),
            'enhanced_crossovers': self.indicators.get('Enhanced_Crossovers', {}),
            'breakout_setup': self.indicators.get('Breakout_Setup', {}),
        }
        
        # Add fundamental indicators
        summary['fundamental'] = fundamental
        
        return summary

    def detect_breakout_setup(self) -> Dict:
        if self.data is None or len(self.data) < 60:
            return {'qualified': False, 'strength': 0, 'details': ['INSUFFICIENT_DATA']}

        df = self.data.copy()
        details = []
        strength = 0
        flags = []
        checks = {}

        sma50 = SMAIndicator(close=df['Close'], window=50).sma_indicator()
        sma200 = SMAIndicator(close=df['Close'], window=200).sma_indicator() if len(df) >= 200 else None
        rsi_series = RSIIndicator(close=df['Close'], window=14).rsi()

        current_price = df['Close'].iloc[-1]
        curr_rsi = rsi_series.iloc[-1] if len(rsi_series.dropna()) else None
        curr_sma50 = sma50.iloc[-1] if len(sma50.dropna()) else None
        curr_sma200 = (sma200.iloc[-1] if isinstance(sma200, pd.Series) and len(sma200.dropna()) else None)

        trend_ok = False
        if curr_sma50 is not None:
            # Require price > SMA50; if SMA200 available also require SMA50 > SMA200
            if curr_sma200 is not None:
                trend_ok = (current_price > curr_sma50) and (curr_sma50 > curr_sma200)
            else:
                trend_ok = (current_price > curr_sma50)
        details.append('Trend alignment: ' + ('OK' if trend_ok else 'NO'))
        checks['trend_ok'] = trend_ok
        if trend_ok:
            strength += 1
        flags.append(trend_ok)

        rsi_ok = curr_rsi is not None and curr_rsi > 50
        details.append(f"RSI > 50: {'OK' if rsi_ok else 'NO'} (RSI={round(curr_rsi,2) if curr_rsi is not None else 'N/A'})")
        checks['rsi_ok'] = rsi_ok
        if rsi_ok:
            strength += 1
        flags.append(rsi_ok)

        lookback = min(80, len(df))
        recent = df.tail(lookback)
        swing_highs = []
        swing_lows = []
        for i in range(2, len(recent)-2):
            hi = recent['High'].iloc[i]
            lo = recent['Low'].iloc[i]
            if hi > recent['High'].iloc[i-1] and hi > recent['High'].iloc[i-2] and hi > recent['High'].iloc[i+1] and hi > recent['High'].iloc[i+2]:
                swing_highs.append((recent.index[i], hi))
            if lo < recent['Low'].iloc[i-1] and lo < recent['Low'].iloc[i-2] and lo < recent['Low'].iloc[i+1] and lo < recent['Low'].iloc[i+2]:
                swing_lows.append((recent.index[i], lo))
        pullbacks = []
        j = 0
        for h_idx, h_val in swing_highs:
            while j < len(swing_lows) and swing_lows[j][0] <= h_idx:
                j += 1
            if j < len(swing_lows):
                l_idx, l_val = swing_lows[j]
                if l_val < h_val and h_val > 0:
                    pullbacks.append((h_val - l_val) / h_val)
        shrinking_ok = False
        if len(pullbacks) >= 3:
            a, b, c = pullbacks[-3:]
            # Relax: allow non-increasing and reduce required overall reduction to 5%
            shrinking_ok = (a >= b >= c) and (a - c) >= 0.05 * a
        details.append('Shrinking pullbacks: ' + ('OK' if shrinking_ok else 'NO'))
        checks['shrinking_pullbacks'] = shrinking_ok
        if shrinking_ok:
            strength += 1
        flags.append(shrinking_ok)

        vol_ok = False
        if len(df) >= 30:
            recent_vol = df['Volume'].tail(10).mean()
            prior_vol = df['Volume'].tail(20).head(10).mean()
            # Relax: 0.9 instead of 0.8
            if prior_vol > 0 and recent_vol < prior_vol * 0.9:
                vol_ok = True
        details.append('Declining volume in consolidation: ' + ('OK' if vol_ok else 'NO'))
        checks['declining_volume'] = vol_ok
        if vol_ok:
            strength += 1
        flags.append(vol_ok)

        N = 20
        vol_mult = 1.3
        rolling_high = df['High'].rolling(N).max()
        vol_ma = df['Volume'].rolling(20).mean()
        breakout_ok = False
        if len(df) >= N + 1:
            prior_high = rolling_high.shift(1).iloc[-1]
            today_close = df['Close'].iloc[-1]
            today_high = df['High'].iloc[-1]
            today_vol = df['Volume'].iloc[-1]
            vma = vol_ma.iloc[-1]
            if pd.notna(prior_high) and pd.notna(vma):
                # Relax: allow breakout by intraday high
                breakout_ok = ((today_close > prior_high) or (today_high > prior_high)) and (today_vol > vol_mult * vma)
        details.append('Breakout above high with volume: ' + ('OK' if breakout_ok else 'NO'))
        checks['breakout_high_volume'] = breakout_ok
        if breakout_ok:
            strength += 2
        flags.append(breakout_ok)

        qualified = all(flags)
        # Prequalified: all checks except the breakout itself
        prequalified = False
        if 'breakout_high_volume' in checks:
            other_checks_ok = all(v for k, v in checks.items() if k != 'breakout_high_volume')
            prequalified = other_checks_ok and not qualified
        return {'qualified': qualified, 'prequalified': prequalified, 'strength': strength, 'details': details, 'checks': checks}

    def detect_vcp_pattern(self) -> Dict:
        """
        Detect Volatility Contraction Pattern (VCP)
        VCP indicates potential breakout after volatility contraction
        """
        if self.data is None or len(self.data) < 50:
            return {'pattern': 'INSUFFICIENT_DATA', 'strength': 0, 'details': []}
        
        df = self.data.copy()
        details = []
        pattern_strength = 0
        
        # Calculate price ranges over different windows
        df['high_20'] = df['High'].rolling(20).max()
        df['low_20'] = df['Low'].rolling(20).min()
        df['range_20'] = (df['high_20'] - df['low_20']) / df['Close']
        
        df['high_10'] = df['High'].rolling(10).max()
        df['low_10'] = df['Low'].rolling(10).min()
        df['range_10'] = (df['high_10'] - df['low_10']) / df['Close']
        
        # Check for volatility contraction over recent periods
        recent_ranges = df['range_20'].dropna().tail(10)
        if len(recent_ranges) >= 5:
            range_trend = np.polyfit(range(len(recent_ranges)), recent_ranges.values, 1)[0]
            if range_trend < -0.001:  # Negative trend indicates contraction
                pattern_strength += 2
                details.append("Volatility contracting over recent periods")
        
        # Check for price tightening near highs
        recent_highs = df['high_20'].dropna().tail(20)
        recent_closes = df['Close'].tail(20)
        
        if len(recent_highs) >= 10 and len(recent_closes) >= 10:
            avg_high = recent_highs.mean()
            avg_close = recent_closes.mean()
            
            if avg_close >= avg_high * 0.95:  # Price within 5% of recent highs
                pattern_strength += 2
                details.append("Price tightening near recent highs")
        
        # Check for decreasing volume during consolidation
        if len(df) >= 20:
            recent_volume = df['Volume'].tail(10)
            earlier_volume = df['Volume'].tail(20).head(10)
            
            if recent_volume.mean() < earlier_volume.mean() * 0.8:
                pattern_strength += 1
                details.append("Decreasing volume during consolidation")
        
        # Determine pattern type
        if pattern_strength >= 4:
            pattern_type = 'STRONG_VCP'
        elif pattern_strength >= 2:
            pattern_type = 'WEAK_VCP'
        else:
            pattern_type = 'NO_VCP'
        
        return {
            'pattern': pattern_type,
            'strength': pattern_strength,
            'details': details
        }
    
    def detect_rsi_divergence(self) -> Dict:
        """
        Detect RSI divergence (bullish and bearish)
        """
        if self.data is None or len(self.data) < 30:
            return {'divergence': 'INSUFFICIENT_DATA', 'type': None, 'strength': 0}
        
        df = self.data.copy()
        
        # Calculate RSI if not already done
        rsi = RSIIndicator(close=df['Close'], window=14)
        df['RSI'] = rsi.rsi()
        
        # Look for divergence over last 20-30 periods
        lookback = min(30, len(df) - 1)
        recent_data = df.tail(lookback + 1)
        
        if len(recent_data) < 10:
            return {'divergence': 'INSUFFICIENT_DATA', 'type': None, 'strength': 0}
        
        # Find price highs and lows
        price_highs = []
        price_lows = []
        rsi_highs = []
        rsi_lows = []
        
        for i in range(2, len(recent_data)):
            # Price highs
            if (recent_data.iloc[i]['High'] > recent_data.iloc[i-1]['High'] and 
                recent_data.iloc[i]['High'] > recent_data.iloc[i-2]['High']):
                price_highs.append((i, recent_data.iloc[i]['High']))
                rsi_highs.append((i, recent_data.iloc[i]['RSI']))
            
            # Price lows
            if (recent_data.iloc[i]['Low'] < recent_data.iloc[i-1]['Low'] and 
                recent_data.iloc[i]['Low'] < recent_data.iloc[i-2]['Low']):
                price_lows.append((i, recent_data.iloc[i]['Low']))
                rsi_lows.append((i, recent_data.iloc[i]['RSI']))
        
        divergence_type = None
        strength = 0
        
        # Check for bearish divergence (higher price highs + lower RSI highs)
        if len(price_highs) >= 2 and len(rsi_highs) >= 2:
            price_trend = price_highs[-1][1] - price_highs[-2][1]
            rsi_trend = rsi_highs[-1][1] - rsi_highs[-2][1]
            
            if price_trend > 0 and rsi_trend < 0:
                divergence_type = 'BEARISH'
                strength = min(abs(rsi_trend) * 10, 5)
        
        # Check for bullish divergence (lower price lows + higher RSI lows)
        if len(price_lows) >= 2 and len(rsi_lows) >= 2:
            price_trend = price_lows[-1][1] - price_lows[-2][1]
            rsi_trend = rsi_lows[-1][1] - rsi_lows[-2][1]
            
            if price_trend < 0 and rsi_trend > 0:
                divergence_type = 'BULLISH'
                strength = min(abs(rsi_trend) * 10, 5)
        
        return {
            'divergence': divergence_type if divergence_type else 'NONE',
            'type': divergence_type,
            'strength': strength
        }
    
    def detect_macd_divergence(self) -> Dict:
        """
        Detect MACD divergence
        """
        if self.data is None or len(self.data) < 50:
            return {'divergence': 'INSUFFICIENT_DATA', 'type': None, 'strength': 0}
        
        df = self.data.copy()
        
        # Calculate MACD if not already done
        macd = MACD(close=df['Close'])
        df['MACD'] = macd.macd()
        
        # Look for divergence over last 30-40 periods
        lookback = min(40, len(df) - 1)
        recent_data = df.tail(lookback + 1)
        
        if len(recent_data) < 15:
            return {'divergence': 'INSUFFICIENT_DATA', 'type': None, 'strength': 0}
        
        # Find price highs and corresponding MACD highs
        price_highs = []
        price_lows = []
        macd_highs = []
        macd_lows = []
        
        for i in range(3, len(recent_data)):
            # Price highs
            if (recent_data.iloc[i]['High'] > recent_data.iloc[i-1]['High'] and 
                recent_data.iloc[i]['High'] > recent_data.iloc[i-2]['High'] and
                recent_data.iloc[i]['High'] > recent_data.iloc[i-3]['High']):
                price_highs.append((i, recent_data.iloc[i]['High']))
                macd_highs.append((i, recent_data.iloc[i]['MACD']))
            
            # Price lows
            if (recent_data.iloc[i]['Low'] < recent_data.iloc[i-1]['Low'] and 
                recent_data.iloc[i]['Low'] < recent_data.iloc[i-2]['Low'] and
                recent_data.iloc[i]['Low'] < recent_data.iloc[i-3]['Low']):
                price_lows.append((i, recent_data.iloc[i]['Low']))
                macd_lows.append((i, recent_data.iloc[i]['MACD']))
        
        divergence_type = None
        strength = 0
        
        # Check for bearish divergence
        if len(price_highs) >= 2 and len(macd_highs) >= 2:
            price_trend = price_highs[-1][1] - price_highs[-2][1]
            macd_trend = macd_highs[-1][1] - macd_highs[-2][1]
            
            if price_trend > 0 and macd_trend < 0:
                divergence_type = 'BEARISH'
                strength = min(abs(macd_trend) * 100, 5)
        
        # Check for bullish divergence
        if len(price_lows) >= 2 and len(macd_lows) >= 2:
            price_trend = price_lows[-1][1] - price_lows[-2][1]
            macd_trend = macd_lows[-1][1] - macd_lows[-2][1]
            
            if price_trend < 0 and macd_trend > 0:
                divergence_type = 'BULLISH'
                strength = min(abs(macd_trend) * 100, 5)
        
        return {
            'divergence': divergence_type if divergence_type else 'NONE',
            'type': divergence_type,
            'strength': strength
        }
    
    def detect_enhanced_crossovers(self) -> Dict:
        """
        Enhanced crossover detection with volume confirmation
        """
        if self.data is None or len(self.data) < 50:
            return {'crossovers': [], 'volume_confirmed': [], 'strength': 0}
        
        df = self.data.copy()
        crossovers = []
        volume_confirmed = []
        
        # Calculate moving averages
        sma_10 = SMAIndicator(close=df['Close'], window=10)
        sma_20 = SMAIndicator(close=df['Close'], window=20)
        sma_40 = SMAIndicator(close=df['Close'], window=40)
        
        df['SMA_10'] = sma_10.sma_indicator()
        df['SMA_20'] = sma_20.sma_indicator()
        df['SMA_40'] = sma_40.sma_indicator()
        
        # Calculate average volume
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        
        # Look for crossovers in last 20 periods
        lookback = min(20, len(df) - 1)
        recent_data = df.tail(lookback + 1).dropna()
        
        if len(recent_data) < 5:
            return {'crossovers': [], 'volume_confirmed': [], 'strength': 0}
        
        for i in range(1, len(recent_data)):
            prev = recent_data.iloc[i-1]
            curr = recent_data.iloc[i]
            
            # 10/20 SMA crossover
            if (prev['SMA_10'] <= prev['SMA_20'] and curr['SMA_10'] > curr['SMA_20']):
                crossover_type = 'BULLISH_10_20'
                volume_confirm = curr['Volume'] > curr['Volume_MA'] * 1.2
                
                crossovers.append(crossover_type)
                if volume_confirm:
                    volume_confirmed.append(crossover_type)
            
            elif (prev['SMA_10'] >= prev['SMA_20'] and curr['SMA_10'] < curr['SMA_20']):
                crossover_type = 'BEARISH_10_20'
                volume_confirm = curr['Volume'] > curr['Volume_MA'] * 1.2
                
                crossovers.append(crossover_type)
                if volume_confirm:
                    volume_confirmed.append(crossover_type)
            
            # 20/40 SMA crossover
            if (prev['SMA_20'] <= prev['SMA_40'] and curr['SMA_20'] > curr['SMA_40']):
                crossover_type = 'BULLISH_20_40'
                volume_confirm = curr['Volume'] > curr['Volume_MA'] * 1.2
                
                crossovers.append(crossover_type)
                if volume_confirm:
                    volume_confirmed.append(crossover_type)
            
            elif (prev['SMA_20'] >= prev['SMA_40'] and curr['SMA_20'] < curr['SMA_40']):
                crossover_type = 'BEARISH_20_40'
                volume_confirm = curr['Volume'] > curr['Volume_MA'] * 1.2
                
                crossovers.append(crossover_type)
                if volume_confirm:
                    volume_confirmed.append(crossover_type)
        
        # Calculate strength based on volume confirmation
        strength = len(volume_confirmed) * 2 if volume_confirmed else 0
        
        return {
            'crossovers': crossovers[-5:],  # Last 5 crossovers
            'volume_confirmed': volume_confirmed[-5:],
            'strength': strength
        }

