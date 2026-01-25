"""
Batch Stock Technical Analysis - Efficient multi-stock analysis to avoid rate limits
"""

try:
    import yfinance as yf
    import yfinance.utils
    import requests
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
from typing import Dict, List, Tuple, Optional
import time
import random
import warnings
warnings.filterwarnings('ignore')


class BatchStockAnalyzer:
    """Efficient batch stock analyzer to avoid rate limits"""
    
    def __init__(self, symbols: List[str], period: str = "6mo", batch_size: int = 50):
        """
        Initialize batch analyzer
        
        Args:
            symbols: List of stock ticker symbols
            period: Data period ('1mo', '3mo', '6mo', '1y', '2y', '5y')
            batch_size: Number of symbols to fetch in each batch
        """
        self.symbols = [s.upper().strip() for s in symbols if s.strip()]
        # Use 6mo as default to get more reliable data
        self.period = period if period != "1y" else "6mo"
        self.batch_size = batch_size
        self.data_cache = {}
        self.ticker_cache = {}
        self.session_reset_attempts = 0
        self.max_session_resets = 3
    
    def _reset_yfinance_session(self):
        """Comprehensive yfinance session reset"""
        try:
            print("Resetting yfinance session...")
            
            # Reset multiple session components
            yfinance.utils.tickers._session = None
            if hasattr(yfinance.utils, '_shared_session'):
                yfinance.utils._shared_session = None
            
            # Clear any cached sessions
            if hasattr(yfinance, 'multi'):
                yfinance.multi._session = None
            
            # Create a fresh session
            import requests
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # Update yfinance session
            yfinance.utils.tickers._session = session
            
            self.session_reset_attempts += 1
            print(f"Session reset attempt {self.session_reset_attempts}/{self.max_session_resets}")
            
            return True
            
        except Exception as e:
            print(f"Session reset failed: {e}")
            return False
        
    def fetch_batch_data(self) -> Dict[str, bool]:
        """
        Fetch data for all symbols in batches to avoid rate limits
        
        Returns:
            Dictionary mapping symbols to success status
        """
        results = {}
        
        # Check which symbols we already have cached
        uncached_symbols = [s for s in self.symbols if s not in self.data_cache]
        
        if not uncached_symbols:
            print("All symbols already cached")
            return {symbol: True for symbol in self.symbols}
        
        print(f"Fetching data for {len(uncached_symbols)} uncached symbols...")
        
        # Process symbols in batches
        for i in range(0, len(uncached_symbols), self.batch_size):
            batch_symbols = uncached_symbols[i:i + self.batch_size]
            batch_results = self._fetch_single_batch(batch_symbols)
            results.update(batch_results)
            
            # Add delay between batches to be respectful to the API
            if i + self.batch_size < len(uncached_symbols):
                # Conservative delay to avoid rate limits
                delay = random.uniform(1.0, 2.0)  # 1-2 seconds random delay
                time.sleep(delay)
        
        # Add cached symbols to results
        for symbol in self.symbols:
            if symbol in self.data_cache and symbol not in results:
                results[symbol] = True
        
        return results
    
    def _fetch_single_batch(self, symbols: List[str], retry_count: int = 0) -> Dict[str, bool]:
        """Fetch data for a single batch of symbols with retry logic"""
        results = {}
        max_retries = 3
        base_delay = 1.0  # Base delay in seconds
        
        try:
            # Use yfinance's download method for batch fetching
            data = yf.download(
                symbols,
                period=self.period,
                group_by='ticker',
                auto_adjust=True,
                prepost=False,
                threads=True,  # Use threading for faster downloads
                timeout=30
            )
            
            # Handle single symbol case (returns DataFrame instead of MultiIndex)
            if len(symbols) == 1:
                symbol = symbols[0]
                if not data.empty:
                    # Handle MultiIndex columns for single symbol
                    if isinstance(data.columns, pd.MultiIndex):
                        # Flatten MultiIndex columns
                        data.columns = [col[1] for col in data.columns]
                    
                    self.data_cache[symbol] = data
                    results[symbol] = True
                else:
                    results[symbol] = False
                return results
            
            # Process multi-symbol data
            for symbol in symbols:
                try:
                    if symbol in data.columns:
                        symbol_data = data[symbol]
                        
                        # Check if we have valid data
                        if not symbol_data.empty and len(symbol_data) >= 14:
                            # Ensure we have the required columns
                            if all(col in symbol_data.columns for col in ['Close', 'High', 'Low', 'Volume']):
                                self.data_cache[symbol] = symbol_data
                                
                                # Also create ticker object for fundamental data
                                ticker = yf.Ticker(symbol)
                                self.ticker_cache[symbol] = ticker
                                
                                results[symbol] = True
                            else:
                                # Try to handle different data format
                                # Sometimes yfinance returns data with different column names
                                print(f"Warning: {symbol} data has unexpected columns: {list(symbol_data.columns)}")
                                results[symbol] = False
                        else:
                            results[symbol] = False
                    else:
                        # Handle MultiIndex columns case
                        if isinstance(data.columns, pd.MultiIndex):
                            # Check if symbol is in the first level of MultiIndex
                            if symbol in data.columns.get_level_values(0):
                                # Extract all columns for this symbol
                                symbol_columns = [(symbol, col) for col in ['Open', 'High', 'Low', 'Close', 'Volume'] if (symbol, col) in data.columns]
                                if symbol_columns:
                                    symbol_data = data[symbol_columns]
                                    # Flatten column names
                                    symbol_data.columns = [col[1] for col in symbol_columns]
                                    
                                    if not symbol_data.empty and len(symbol_data) >= 14:
                                        self.data_cache[symbol] = symbol_data
                                        
                                        # Also create ticker object for fundamental data
                                        ticker = yf.Ticker(symbol)
                                        self.ticker_cache[symbol] = ticker
                                        
                                        results[symbol] = True
                                    else:
                                        results[symbol] = False
                                else:
                                    results[symbol] = False
                            else:
                                results[symbol] = False
                        else:
                            # Check if data is in a different format (flat DataFrame)
                            if hasattr(data, 'index') and symbol in data.index:
                                symbol_data = data.loc[symbol]
                                if isinstance(symbol_data, pd.Series):
                                    # This is likely a single row of data, not suitable for analysis
                                    results[symbol] = False
                                else:
                                    # Try to extract the symbol data differently
                                    results[symbol] = False
                            else:
                                results[symbol] = False
                        
                except Exception as e:
                    print(f"Error processing {symbol}: {str(e)}")
                    results[symbol] = False
                    
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if this is a rate limit error
            if any(keyword in error_msg for keyword in ['too many requests', 'rate limit', '429', 'timeout']):
                if retry_count < max_retries:
                    # Exponential backoff with jitter
                    delay = base_delay * (2 ** retry_count) + random.uniform(0.1, 0.5)
                    print(f"Rate limit hit, retrying in {delay:.2f} seconds... (attempt {retry_count + 1}/{max_retries})")
                    time.sleep(delay)
                    return self._fetch_single_batch(symbols, retry_count + 1)
                else:
                    print(f"Max retries exceeded for batch: {symbols}")
            
            # Check if this is an authentication error
            elif any(keyword in error_msg for keyword in ['401', 'unauthorized', 'invalid crumb', 'authentication']):
                print(f"Authentication error detected. Attempting to refresh yfinance session...")
                
                if self.session_reset_attempts < self.max_session_resets:
                    if self._reset_yfinance_session():
                        if retry_count < max_retries:
                            delay = base_delay * (2 ** retry_count) + random.uniform(0.1, 0.5)
                            time.sleep(delay)
                            return self._fetch_single_batch(symbols, retry_count + 1)
                        else:
                            print(f"Max retries exceeded for authentication: {symbols}")
                            print("Falling back to individual downloads...")
                            return self._fallback_individual_downloads(symbols)
                    else:
                        print("Session reset failed. Falling back to individual downloads...")
                        return self._fallback_individual_downloads(symbols)
                else:
                    print(f"Max session resets exceeded ({self.session_reset_attempts}). Falling back to individual downloads...")
                    return self._fallback_individual_downloads(symbols)
            
            print(f"Error fetching batch data: {str(e)}")
            # Mark all symbols in this batch as failed
            for symbol in symbols:
                results[symbol] = False
        
        return results
    
    def _fallback_individual_downloads(self, symbols: List[str]) -> Dict[str, bool]:
        """Fallback method to download symbols individually when batch fails"""
        results = {}
        print(f"Using individual downloads for {len(symbols)} symbols...")
        
        for symbol in symbols:
            try:
                # Try multiple approaches for individual downloads
                success = False
                
                # Method 1: Standard ticker history
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period=self.period, timeout=30)
                    
                    if not data.empty and len(data) >= 14:
                        if all(col in data.columns for col in ['Close', 'High', 'Low', 'Volume']):
                            self.data_cache[symbol] = data
                            self.ticker_cache[symbol] = ticker
                            results[symbol] = True
                            success = True
                            print(f"✓ {symbol}: Standard individual download successful")
                except Exception as e1:
                    print(f"✗ {symbol}: Standard download failed - {str(e1)}")
                
                # Method 2: Download with different parameters if first method failed
                if not success:
                    try:
                        # Try with auto_adjust=False and different timeout
                        data = yf.download(
                            symbol,
                            period=self.period,
                            auto_adjust=False,
                            prepost=False,
                            timeout=15
                        )
                        
                        if not data.empty and len(data) >= 14:
                            # Handle MultiIndex if present
                            if isinstance(data.columns, pd.MultiIndex):
                                data.columns = [col[1] for col in data.columns]
                            
                            if all(col in data.columns for col in ['Close', 'High', 'Low', 'Volume']):
                                self.data_cache[symbol] = data
                                ticker = yf.Ticker(symbol)
                                self.ticker_cache[symbol] = ticker
                                results[symbol] = True
                                success = True
                                print(f"✓ {symbol}: Alternative download successful")
                    except Exception as e2:
                        print(f"✗ {symbol}: Alternative download failed - {str(e2)}")
                
                # Method 3: Try shorter period if still failing
                if not success and self.period != "3mo":
                    try:
                        shorter_period = "3mo"
                        data = yf.download(symbol, period=shorter_period, timeout=15)
                        
                        if not data.empty and len(data) >= 14:
                            if isinstance(data.columns, pd.MultiIndex):
                                data.columns = [col[1] for col in data.columns]
                            
                            if all(col in data.columns for col in ['Close', 'High', 'Low', 'Volume']):
                                self.data_cache[symbol] = data
                                ticker = yf.Ticker(symbol)
                                self.ticker_cache[symbol] = ticker
                                results[symbol] = True
                                success = True
                                print(f"✓ {symbol}: Short period ({shorter_period}) download successful")
                    except Exception as e3:
                        print(f"✗ {symbol}: Short period download failed - {str(e3)}")
                
                if not success:
                    print(f"✗ {symbol}: All download methods failed")
                    results[symbol] = False
                    
            except Exception as e:
                print(f"✗ {symbol}: Individual download error - {str(e)}")
                results[symbol] = False
            
            # Add delay between individual downloads
            time.sleep(0.3)
        
        successful = sum(1 for success in results.values() if success)
        print(f"Individual downloads completed: {successful}/{len(symbols)} successful")
        
        # If still no successful downloads, try to provide a helpful error message
        if successful == 0:
            print("⚠ All individual downloads failed. This might be due to:")
            print("  - Yahoo Finance API issues")
            print("  - Network connectivity problems")
            print("  - Rate limiting")
            print("  - Invalid stock symbols")
            print("Please try again in a few minutes or check your internet connection.")
        
        return results
    
    def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Analyze a single symbol using cached data
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Analysis result or None if data not available
        """
        if symbol not in self.data_cache:
            return None
        
        try:
            data = self.data_cache[symbol]
            ticker = self.ticker_cache.get(symbol)
            
            # Validate data before processing
            if data is None or data.empty or len(data) < 2:
                return {'error': 'Insufficient data for analysis'}
            
            # Check required columns
            required_columns = ['Close', 'High', 'Low', 'Volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                return {'error': f'Missing required columns: {missing_columns}'}
            
            # Calculate indicators
            indicators = self._calculate_indicators(data)
            
            # Validate indicators
            if not indicators:
                return {'error': 'Failed to calculate indicators'}
            
            # Get fundamental data
            fundamental = self._get_fundamental_indicators(ticker, indicators)
            
            # Get recommendation
            recommendation = self._get_recommendation(indicators)
            
            # Create summary with safe access
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
                # Advanced pattern analysis
                'vcp_pattern': indicators.get('VCP_Pattern', {}),
                'rsi_divergence': indicators.get('RSI_Divergence', {}),
                'macd_divergence': indicators.get('MACD_Divergence', {}),
                'enhanced_crossovers': indicators.get('Enhanced_Crossovers', {}),
                'breakout_setup': indicators.get('Breakout_Setup', {}),
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
    
    def analyze_all(self) -> Dict[str, Dict]:
        """
        Analyze all symbols in the batch
        
        Returns:
            Dictionary mapping symbols to analysis results
        """
        results = {}
        
        # First fetch all data
        fetch_results = self.fetch_batch_data()
        
        # Then analyze each successful symbol
        for symbol in self.symbols:
            if fetch_results.get(symbol, False):
                analysis = self.analyze_symbol(symbol)
                if analysis:
                    results[symbol] = analysis
                else:
                    results[symbol] = {'error': 'Analysis failed'}
            else:
                results[symbol] = {'error': 'Data fetch failed'}
        
        return results
    
    def _calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate technical indicators for given data"""
        indicators = {}
        
        try:
            # Trend Indicators
            if len(data) >= 26:
                macd = MACD(close=data['Close'])
                macd_series = macd.macd()
                macd_signal_series = macd.macd_signal()
                macd_diff_series = macd.macd_diff()
                
                # Check if series have data before accessing last element
                if len(macd_series.dropna()) > 0:
                    indicators['MACD'] = macd_series.iloc[-1]
                else:
                    indicators['MACD'] = None
                    
                if len(macd_signal_series.dropna()) > 0:
                    indicators['MACD_Signal'] = macd_signal_series.iloc[-1]
                else:
                    indicators['MACD_Signal'] = None
                    
                if len(macd_diff_series.dropna()) > 0:
                    indicators['MACD_Histogram'] = macd_diff_series.iloc[-1]
                else:
                    indicators['MACD_Histogram'] = None
            else:
                indicators['MACD'] = None
                indicators['MACD_Signal'] = None
                indicators['MACD_Histogram'] = None
            
            # Moving Averages
            if len(data) >= 20:
                sma_20 = SMAIndicator(close=data['Close'], window=20)
                sma_20_series = sma_20.sma_indicator()
                if len(sma_20_series.dropna()) > 0:
                    indicators['SMA_20'] = sma_20_series.iloc[-1]
                else:
                    indicators['SMA_20'] = None
            else:
                indicators['SMA_20'] = None
                
            if len(data) >= 50:
                sma_50 = SMAIndicator(close=data['Close'], window=50)
                sma_50_series = sma_50.sma_indicator()
                if len(sma_50_series.dropna()) > 0:
                    indicators['SMA_50'] = sma_50_series.iloc[-1]
                else:
                    indicators['SMA_50'] = None
            else:
                indicators['SMA_50'] = None
                
            if len(data) >= 200:
                sma_200 = SMAIndicator(close=data['Close'], window=200)
                sma_200_series = sma_200.sma_indicator()
                if len(sma_200_series.dropna()) > 0:
                    indicators['SMA_200'] = sma_200_series.iloc[-1]
                else:
                    indicators['SMA_200'] = None
            else:
                indicators['SMA_200'] = None
            
            # EMAs
            if len(data) >= 12:
                ema_12 = EMAIndicator(close=data['Close'], window=12)
                ema_12_series = ema_12.ema_indicator()
                if len(ema_12_series.dropna()) > 0:
                    indicators['EMA_12'] = ema_12_series.iloc[-1]
                else:
                    indicators['EMA_12'] = None
            else:
                indicators['EMA_12'] = None
                
            if len(data) >= 26:
                ema_26 = EMAIndicator(close=data['Close'], window=26)
                ema_26_series = ema_26.ema_indicator()
                if len(ema_26_series.dropna()) > 0:
                    indicators['EMA_26'] = ema_26_series.iloc[-1]
                else:
                    indicators['EMA_26'] = None
            else:
                indicators['EMA_26'] = None
            
            # Momentum Indicators
            rsi = RSIIndicator(close=data['Close'], window=14)
            rsi_series = rsi.rsi()
            if len(rsi_series.dropna()) > 0:
                indicators['RSI'] = rsi_series.iloc[-1]
            else:
                indicators['RSI'] = None
            
            stoch = StochasticOscillator(high=data['High'], low=data['Low'], close=data['Close'])
            stoch_k_series = stoch.stoch()
            stoch_d_series = stoch.stoch_signal()
            if len(stoch_k_series.dropna()) > 0:
                indicators['Stoch_K'] = stoch_k_series.iloc[-1]
            else:
                indicators['Stoch_K'] = None
            if len(stoch_d_series.dropna()) > 0:
                indicators['Stoch_D'] = stoch_d_series.iloc[-1]
            else:
                indicators['Stoch_D'] = None
            
            # Volatility Indicators
            if len(data) >= 20:
                bb = BollingerBands(close=data['Close'], window=20, window_dev=2)
                bb_upper_series = bb.bollinger_hband()
                bb_lower_series = bb.bollinger_lband()
                bb_middle_series = bb.bollinger_mavg()
                
                if len(bb_upper_series.dropna()) > 0:
                    indicators['BB_Upper'] = bb_upper_series.iloc[-1]
                else:
                    indicators['BB_Upper'] = None
                if len(bb_lower_series.dropna()) > 0:
                    indicators['BB_Lower'] = bb_lower_series.iloc[-1]
                else:
                    indicators['BB_Lower'] = None
                if len(bb_middle_series.dropna()) > 0:
                    indicators['BB_Middle'] = bb_middle_series.iloc[-1]
                else:
                    indicators['BB_Middle'] = None
            else:
                indicators['BB_Upper'] = None
                indicators['BB_Lower'] = None
                indicators['BB_Middle'] = None
            
            atr = AverageTrueRange(high=data['High'], low=data['Low'], close=data['Close'])
            atr_series = atr.average_true_range()
            if len(atr_series.dropna()) > 0:
                indicators['ATR'] = atr_series.iloc[-1]
            else:
                indicators['ATR'] = None
            
            # Volume Indicators
            obv = OnBalanceVolumeIndicator(close=data['Close'], volume=data['Volume'])
            obv_series = obv.on_balance_volume()
            if len(obv_series.dropna()) > 0:
                indicators['OBV'] = obv_series.iloc[-1]
            else:
                indicators['OBV'] = None
            
            # Price data
            indicators['Current_Price'] = data['Close'].iloc[-1]
            
            # Calculate price changes with bounds checking and validation
            if len(data) >= 2:
                prev_close = data['Close'].iloc[-2]
                indicators['Price_Change_Pct'] = ((data['Close'].iloc[-1] - prev_close) / prev_close) * 100
            else:
                indicators['Price_Change_Pct'] = 0
            indicators['Price_Change_1d_Pct'] = indicators['Price_Change_Pct']
            
            # Calculate price changes for different periods with bounds checking
            # Use more conservative time periods to avoid future data issues
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
                
            # For 1 year change, use either 252 trading days or the earliest available data
            if len(data) >= 253:
                year_ago_close = data['Close'].iloc[-253]
                indicators['Price_Change_1y_Pct'] = ((data['Close'].iloc[-1] - year_ago_close) / year_ago_close) * 100
            elif len(data) >= 50:  # Use at least 50 days of data for meaningful yearly calculation
                earliest_close = data['Close'].iloc[0]
                # Calculate annualized change based on available data
                days_available = len(data)
                annualized_change = ((data['Close'].iloc[-1] - earliest_close) / earliest_close) * 100
                # Scale to approximately 252 trading days per year
                indicators['Price_Change_1y_Pct'] = annualized_change * (252 / days_available)
            else:
                indicators['Price_Change_1y_Pct'] = 0
            
            # Advanced Pattern Analysis (simplified versions)
            indicators['VCP_Pattern'] = self._detect_vcp_pattern(data)
            indicators['RSI_Divergence'] = self._detect_rsi_divergence(data)
            indicators['MACD_Divergence'] = self._detect_macd_divergence(data)
            indicators['Enhanced_Crossovers'] = self._detect_enhanced_crossovers(data)
            indicators['Breakout_Setup'] = self._detect_breakout_setup(data)
            
        except Exception as e:
            print(f"Error calculating indicators: {str(e)}")
        
        return indicators
    
    def _get_fundamental_indicators(self, ticker, indicators: Dict) -> Dict:
        """Get fundamental analysis indicators"""
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
            
            # Get market cap
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
            
            # Format numeric values
            for key in ['revenue_growth', 'earnings_growth']:
                if isinstance(fundamental[key], (int, float)) and fundamental[key] != 'N/A':
                    if abs(fundamental[key]) < 1:
                        fundamental[key] = round(fundamental[key] * 100, 2)
                    else:
                        fundamental[key] = round(fundamental[key], 2)
            
            for key in ['roe', 'profit_margin']:
                if isinstance(fundamental[key], (int, float)) and fundamental[key] != 'N/A':
                    fundamental[key] = round(fundamental[key] * 100, 2)
            
            for key in ['pe_ratio', 'forward_pe', 'pb_ratio', 'eps', 'debt_to_equity', 'beta', '52_week_high', '52_week_low', 'avg_volume']:
                if isinstance(fundamental[key], (int, float)) and fundamental[key] != 'N/A':
                    fundamental[key] = round(fundamental[key], 2)
            
            return fundamental
            
        except Exception as e:
            print(f"Error getting fundamental indicators: {str(e)}")
            return {}
    
    def _get_recommendation(self, indicators: Dict) -> Dict:
        """Generate stock recommendation based on technical indicators"""
        if not indicators:
            return {
                'recommendation': 'NEUTRAL',
                'score': 0,
                'reasoning': ['No indicators calculated']
            }
        
        score = 0
        reasons = []
        
        current_price = indicators.get('Current_Price', 0)
        rsi = indicators.get('RSI')
        macd = indicators.get('MACD')
        macd_signal = indicators.get('MACD_Signal')
        macd_hist = indicators.get('MACD_Histogram')
        sma_20 = indicators.get('SMA_20')
        sma_50 = indicators.get('SMA_50')
        sma_200 = indicators.get('SMA_200')
        bb_upper = indicators.get('BB_Upper')
        bb_lower = indicators.get('BB_Lower')
        stoch_k = indicators.get('Stoch_K')
        stoch_d = indicators.get('Stoch_D')
        
        # RSI Analysis
        if rsi is not None:
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
        total_ma_signals = 0
        
        if sma_20 is not None:
            total_ma_signals += 1
            if current_price > sma_20:
                score += 1
                ma_bullish_signals += 1
                
        if sma_50 is not None:
            total_ma_signals += 1
            if current_price > sma_50:
                score += 1
                ma_bullish_signals += 1
                
        if sma_200 is not None:
            total_ma_signals += 1
            if current_price > sma_200:
                score += 1
                ma_bullish_signals += 1
        
        if total_ma_signals > 0:
            if ma_bullish_signals == total_ma_signals:
                reasons.append("Price above all available moving averages (bullish)")
            elif ma_bullish_signals == 0:
                score -= 2
                reasons.append("Price below all available moving averages (bearish)")
        
        # Golden Cross / Death Cross
        if sma_50 is not None and sma_200 is not None:
            if sma_50 > sma_200:
                score += 1
                reasons.append("Golden Cross pattern (SMA50 > SMA200)")
            else:
                score -= 1
                reasons.append("Death Cross pattern (SMA50 < SMA200)")
        
        # Bollinger Bands
        if bb_lower is not None and bb_upper is not None:
            if current_price < bb_lower:
                score += 1
                reasons.append("Price near lower Bollinger Band (potential bounce)")
            elif current_price > bb_upper:
                score -= 1
                reasons.append("Price near upper Bollinger Band (potential pullback)")
        
        # Stochastic
        if stoch_k is not None and stoch_d is not None:
            if stoch_k < 20 and stoch_d < 20:
                score += 1
                reasons.append("Stochastic indicates oversold")
            elif stoch_k > 80 and stoch_d > 80:
                score -= 1
                reasons.append("Stochastic indicates overbought")
        
        # Advanced patterns (simplified scoring)
        vcp_pattern = indicators.get('VCP_Pattern', {})
        if vcp_pattern.get('pattern') == 'STRONG_VCP':
            score += 3
            reasons.append("Strong Volatility Contraction Pattern detected")
        elif vcp_pattern.get('pattern') == 'WEAK_VCP':
            score += 1
            reasons.append("Weak Volatility Contraction Pattern detected")
        
        # Price momentum
        price_change = indicators.get('Price_Change_Pct', 0)
        if price_change > 2:
            score += 1
            reasons.append("Strong positive price momentum")
        elif price_change < -2:
            score -= 1
            reasons.append("Strong negative price momentum")
        
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
            'reasoning': reasons
        }
    
    # Simplified pattern detection methods for batch processing
    def _detect_vcp_pattern(self, data: pd.DataFrame) -> Dict:
        """Detect Volatility Contraction Pattern (VCP)"""
        if data is None or len(data) < 50:
            return {'pattern': 'INSUFFICIENT_DATA', 'strength': 0, 'details': []}
        
        df = data.copy()
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
    
    def _detect_rsi_divergence(self, data: pd.DataFrame) -> Dict:
        """Detect RSI divergence (bullish and bearish)"""
        if data is None or len(data) < 30:
            return {'divergence': 'INSUFFICIENT_DATA', 'type': None, 'strength': 0}
        
        df = data.copy()
        
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
    
    def _detect_macd_divergence(self, data: pd.DataFrame) -> Dict:
        """Detect MACD divergence"""
        if data is None or len(data) < 50:
            return {'divergence': 'INSUFFICIENT_DATA', 'type': None, 'strength': 0}
        
        df = data.copy()
        
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
    
    def _detect_enhanced_crossovers(self, data: pd.DataFrame) -> Dict:
        """Enhanced crossover detection with volume confirmation"""
        if data is None or len(data) < 50:
            return {'crossovers': [], 'volume_confirmed': [], 'strength': 0}
        
        df = data.copy()
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
    
    def _detect_breakout_setup(self, data: pd.DataFrame) -> Dict:
        """Detect breakout setup pattern"""
        if data is None or len(data) < 60:
            return {'qualified': False, 'strength': 0, 'details': ['INSUFFICIENT_DATA']}

        df = data.copy()
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
