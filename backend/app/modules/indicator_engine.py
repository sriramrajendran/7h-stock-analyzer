"""
Indicator Engine Module - Computes comprehensive suite of technical indicators
"""

import pandas as pd
# import numpy as np
from typing import Dict, List, Optional
import logging
try:
    from ta.trend import EMAIndicator, SMAIndicator, MACD, ADXIndicator
    from ta.momentum import RSIIndicator, StochRSIIndicator, ROCIndicator
    from ta.volatility import BollingerBands, AverageTrueRange
    from ta.volume import OnBalanceVolumeIndicator, VolumeWeightedAveragePrice
    from ta.others import DailyReturnIndicator
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    print("Warning: ta library not available, using fallback calculations")

logger = logging.getLogger(__name__)

class IndicatorEngine:
    """Comprehensive technical indicator computation engine"""
    
    def __init__(self):
        self.indicators = {}
        self.indicator_weights = {
            'trend': 0.4,
            'momentum': 0.3,
            'volatility': 0.2,
            'volume': 0.1
        }
    
    def compute_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute comprehensive suite of technical indicators"""
        if not TA_AVAILABLE:
            logger.warning("TA library not available, returning basic indicators")
            # Add basic moving averages using pandas
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['RSI'] = 50.0  # Neutral fallback
            return df
        
        if df.empty or len(df) < 50:
            logger.warning("Insufficient data for indicator computation")
            return df
        
        df_indicators = df.copy()
        
        try:
            # Trend Indicators (40% weight)
            df_indicators = self._compute_trend_indicators(df_indicators)
            
            # Momentum Indicators (30% weight)
            df_indicators = self._compute_momentum_indicators(df_indicators)
            
            # Volatility Indicators (20% weight)
            df_indicators = self._compute_volatility_indicators(df_indicators)
            
            # Volume Indicators (10% weight)
            df_indicators = self._compute_volume_indicators(df_indicators)
            
            # Additional indicators
            df_indicators = self._compute_other_indicators(df_indicators)
            
            logger.info(f"Computed {len([col for col in df_indicators.columns if col not in df.columns])} indicators")
            
        except Exception as e:
            logger.error(f"Error computing indicators: {str(e)}")
            return df
        
        return df_indicators
    
    def _compute_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute trend-based indicators"""
        try:
            # EMA (12, 26)
            ema_12 = EMAIndicator(df['Close'], window=12)
            ema_26 = EMAIndicator(df['Close'], window=26)
            df['EMA_12'] = ema_12.ema_indicator()
            df['EMA_26'] = ema_26.ema_indicator()
            
            # SMA (50, 200)
            sma_50 = SMAIndicator(df['Close'], window=50)
            sma_200 = SMAIndicator(df['Close'], window=200)
            df['SMA_50'] = sma_50.sma_indicator()
            df['SMA_200'] = sma_200.sma_indicator()
            
            # MACD
            macd = MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9)
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['MACD_Histogram'] = macd.macd_diff()
            
            # ADX (14) - Trend strength
            adx = ADXIndicator(df['High'], df['Low'], df['Close'], window=14)
            df['ADX'] = adx.adx()
            df['ADX_Pos'] = adx.adx_pos()
            df['ADX_Neg'] = adx.adx_neg()
            
            logger.debug("Computed trend indicators")
            
        except Exception as e:
            logger.error(f"Error computing trend indicators: {str(e)}")
        
        return df
    
    def _compute_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute momentum-based indicators"""
        try:
            # RSI (14)
            rsi = RSIIndicator(df['Close'], window=14)
            df['RSI_14'] = rsi.rsi()
            
            # Stochastic RSI
            stoch = StochRSIIndicator(df['Close'], window=14)
            df['Stoch_K'] = stoch.stochrsi()
            # StochRSI doesn't have signal method, use None or calculate manually
            df['Stoch_D'] = None
            
            # Rate of Change
            roc = ROCIndicator(df['Close'], window=10)
            df['ROC_10'] = roc.roc()
            
            # Williams %R (computed manually)
            df['Williams_R'] = ((df['High'].rolling(14).max() - df['Close']) / 
                              (df['High'].rolling(14).max() - df['Low'].rolling(14).min())) * -100
            
            # Commodity Channel Index (CCI)
            tp = (df['High'] + df['Low'] + df['Close']) / 3
            sma_tp = tp.rolling(20).mean()
            mad = tp.rolling(20).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
            df['CCI_20'] = (tp - sma_tp) / (0.015 * mad)
            
            logger.debug("Computed momentum indicators")
            
        except Exception as e:
            logger.error(f"Error computing momentum indicators: {str(e)}")
        
        return df
    
    def _compute_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute volatility-based indicators"""
        try:
            # ATR (14) - Average True Range
            atr = AverageTrueRange(df['High'], df['Low'], df['Close'], window=14)
            df['ATR_14'] = atr.average_true_range()
            
            # Bollinger Bands (20, 2)
            bb = BollingerBands(df['Close'], window=20, window_dev=2)
            df['BB_Upper'] = bb.bollinger_hband()
            df['BB_Middle'] = bb.bollinger_mavg()
            df['BB_Lower'] = bb.bollinger_lband()
            df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
            df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
            
            # Historical Volatility (20-day)
            returns = df['Close'].pct_change()
            df['HV_20'] = returns.rolling(20).std() * np.sqrt(252) * 100
            
            logger.debug("Computed volatility indicators")
            
        except Exception as e:
            logger.error(f"Error computing volatility indicators: {str(e)}")
        
        return df
    
    def _compute_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute volume-based indicators"""
        try:
            # On-Balance Volume (OBV)
            obv = OnBalanceVolumeIndicator(df['Close'], df['Volume'])
            df['OBV'] = obv.on_balance_volume()
            
            # Volume Weighted Average Price (20)
            vwap = VolumeWeightedAveragePrice(df['High'], df['Low'], df['Close'], df['Volume'], window=20)
            df['Volume_SMA_20'] = vwap.volume_weighted_average_price()
            
            # Volume Rate of Change
            df['Volume_ROC'] = df['Volume'].pct_change(periods=10)
            
            # Price-Volume Trend (PVT)
            df['PVT'] = (df['Volume'] * df['Close'].pct_change()).cumsum()
            
            # Volume Weighted Average Price (VWAP)
            df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
            
            # Volume Profile
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_20']
            
            logger.debug("Computed volume indicators")
            
        except Exception as e:
            logger.error(f"Error computing volume indicators: {str(e)}")
        
        return df
    
    def _compute_other_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute additional useful indicators"""
        try:
            # Pivot Points
            df['Pivot'] = (df['High'].shift(1) + df['Low'].shift(1) + df['Close'].shift(1)) / 3
            df['R1'] = 2 * df['Pivot'] - df['Low'].shift(1)
            df['S1'] = 2 * df['Pivot'] - df['High'].shift(1)
            df['R2'] = df['Pivot'] + (df['High'].shift(1) - df['Low'].shift(1))
            df['S2'] = df['Pivot'] - (df['High'].shift(1) - df['Low'].shift(1))
            
            # Daily Returns
            df['Daily_Return'] = df['Close'].pct_change()
            
            # Cumulative Returns
            df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1
            
            # Moving Average Convergence Divergence signals
            df['MACD_Cross'] = np.where(df['MACD'] > df['MACD_Signal'], 1, -1)
            
            # EMA Cross signals
            df['EMA_Cross'] = np.where(df['EMA_12'] > df['EMA_26'], 1, -1)
            
            # SMA Cross signals
            df['SMA_Cross'] = np.where(df['SMA_50'] > df['SMA_200'], 1, -1)
            
            # Price relative to moving averages
            df['Price_vs_SMA_50'] = (df['Close'] - df['SMA_50']) / df['SMA_50'] * 100
            df['Price_vs_SMA_200'] = (df['Close'] - df['SMA_200']) / df['SMA_200'] * 100
            
            logger.debug("Computed additional indicators")
            
        except Exception as e:
            logger.error(f"Error computing additional indicators: {str(e)}")
        
        return df
    
    def get_indicator_summary(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Get summary of all computed indicators"""
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        summary = {}
        
        # Trend indicators
        summary['trend'] = {
            'EMA_12': latest.get('EMA_12'),
            'EMA_26': latest.get('EMA_26'),
            'SMA_50': latest.get('SMA_50'),
            'SMA_200': latest.get('SMA_200'),
            'MACD': latest.get('MACD'),
            'MACD_Signal': latest.get('MACD_Signal'),
            'ADX': latest.get('ADX'),
            'EMA_Cross': latest.get('EMA_Cross'),
            'SMA_Cross': latest.get('SMA_Cross')
        }
        
        # Momentum indicators
        summary['momentum'] = {
            'RSI_14': latest.get('RSI_14'),
            'Stoch_K': latest.get('Stoch_K'),
            'Stoch_D': latest.get('Stoch_D'),
            'ROC_10': latest.get('ROC_10'),
            'Williams_R': latest.get('Williams_R'),
            'CCI_20': latest.get('CCI_20')
        }
        
        # Volatility indicators
        summary['volatility'] = {
            'ATR_14': latest.get('ATR_14'),
            'BB_Upper': latest.get('BB_Upper'),
            'BB_Lower': latest.get('BB_Lower'),
            'BB_Position': latest.get('BB_Position'),
            'HV_20': latest.get('HV_20')
        }
        
        # Volume indicators
        summary['volume'] = {
            'OBV': latest.get('OBV'),
            'Volume_SMA_20': latest.get('Volume_SMA_20'),
            'Volume_ROC': latest.get('Volume_ROC'),
            'VWAP': latest.get('VWAP'),
            'Volume_Ratio': latest.get('Volume_Ratio')
        }
        
        return summary
    
    def validate_indicators(self, df: pd.DataFrame) -> Dict[str, bool]:
        """Validate computed indicators for data quality"""
        validation = {}
        
        # Check for NaN values in critical indicators
        critical_indicators = ['RSI_14', 'MACD', 'ADX', 'ATR_14', 'OBV']
        for indicator in critical_indicators:
            if indicator in df.columns:
                validation[f'{indicator}_valid'] = not df[indicator].isna().all()
            else:
                validation[f'{indicator}_valid'] = False
        
        # Check data ranges
        if 'RSI_14' in df.columns:
            validation['RSI_range_valid'] = df['RSI_14'].between(0, 100).all()
        
        if 'ADX' in df.columns:
            validation['ADX_range_valid'] = df['ADX'].between(0, 100).all()
        
        # Check for sufficient data points
        validation['sufficient_data'] = len(df) >= 50
        
        return validation
