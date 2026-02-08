"""
Signal Engine Module - Generates individual indicator signals and aggregates into scores
"""

import pandas as pd
import numpy as np
import warnings
from typing import Dict, List, Tuple, Optional
import logging

# Suppress TA library warnings and pandas deprecation warnings
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*invalid value encountered in scalar divide.*')
warnings.filterwarnings('ignore', category=FutureWarning, message='.*Downcasting object dtype arrays.*')
pd.set_option('future.no_silent_downcasting', True)

logger = logging.getLogger(__name__)

class SignalEngine:
    """Generates and aggregates trading signals from technical indicators"""
    
    def __init__(self):
        self.indicator_weights = {
            'trend': 0.4,
            'momentum': 0.3,
            'volatility': 0.2,
            'volume': 0.1
        }
        
        # Individual indicator weights within categories
        self.trend_weights = {
            'EMA_Cross': 0.3,
            'SMA_Cross': 0.3,
            'MACD_Cross': 0.2,
            'ADX_Strength': 0.2
        }
        
        self.momentum_weights = {
            'RSI_Signal': 0.4,
            'Stoch_Signal': 0.3,
            'ROC_Signal': 0.2,
            'CCI_Signal': 0.1
        }
        
        self.volatility_weights = {
            'BB_Position': 0.5,
            'ATR_Signal': 0.3,
            'HV_Signal': 0.2
        }
        
        self.volume_weights = {
            'OBV_Signal': 0.4,
            'Volume_Ratio': 0.3,
            'PVT_Signal': 0.3
        }
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate all trading signals for the given indicator data"""
        if df.empty:
            logger.warning("Empty dataframe provided for signal generation")
            return df
        
        df_signals = df.copy()
        
        try:
            # Generate trend signals
            df_signals = self._generate_trend_signals(df_signals)
            
            # Generate momentum signals
            df_signals = self._generate_momentum_signals(df_signals)
            
            # Generate volatility signals
            df_signals = self._generate_volatility_signals(df_signals)
            
            # Generate volume signals
            df_signals = self._generate_volume_signals(df_signals)
            
            # Aggregate all signals into final score
            df_signals = self._aggregate_signals(df_signals)
            
            logger.info(f"Generated signals for {len(df_signals)} data points")
            
        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
            return df
        
        return df_signals
    
    def _generate_trend_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trend-based signals"""
        try:
            # EMA Cross Signal
            if 'EMA_12' in df.columns and 'EMA_26' in df.columns:
                df['EMA_Signal'] = np.where(df['EMA_12'] > df['EMA_26'], 1, -1)
                # Add confirmation: signal strength based on distance
                ema_distance = (df['EMA_12'] - df['EMA_26']) / df['EMA_26']
                df['EMA_Strength'] = np.where(ema_distance > 0.02, 1, 
                                             np.where(ema_distance < -0.02, -1, 0))
            else:
                df['EMA_Signal'] = 0
                df['EMA_Strength'] = 0
            
            # SMA Cross Signal
            if 'SMA_50' in df.columns and 'SMA_200' in df.columns:
                df['SMA_Signal'] = np.where(df['SMA_50'] > df['SMA_200'], 1, -1)
                # Golden cross/death cross confirmation
                sma_distance = (df['SMA_50'] - df['SMA_200']) / df['SMA_200']
                df['SMA_Strength'] = np.where(sma_distance > 0.05, 1,
                                             np.where(sma_distance < -0.05, -1, 0))
            else:
                df['SMA_Signal'] = 0
                df['SMA_Strength'] = 0
            
            # MACD Signal
            if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
                df['MACD_Signal'] = np.where(df['MACD'] > df['MACD_Signal'], 1, -1)
                # MACD histogram momentum
                df['MACD_Momentum'] = np.where(df['MACD_Histogram'] > 0, 1, -1)
            else:
                df['MACD_Signal'] = 0
                df['MACD_Momentum'] = 0
            
            # ADX Strength Signal
            if 'ADX' in df.columns:
                # ADX > 25 indicates strong trend
                df['ADX_Strength'] = np.where(df['ADX'] > 25, 1, 0)
                # ADX > 50 indicates very strong trend
                df['ADX_VeryStrong'] = np.where(df['ADX'] > 50, 1, 0)
            else:
                df['ADX_Strength'] = 0
                df['ADX_VeryStrong'] = 0
            
            # Combined trend signal
            df['Trend_Signal'] = (
                df['EMA_Signal'] * self.trend_weights['EMA_Cross'] +
                df['SMA_Signal'] * self.trend_weights['SMA_Cross'] +
                df['MACD_Signal'] * self.trend_weights['MACD_Cross'] +
                df['ADX_Strength'] * self.trend_weights['ADX_Strength']
            )
            
            logger.debug("Generated trend signals")
            
        except Exception as e:
            logger.error(f"Error generating trend signals: {str(e)}")
            df['Trend_Signal'] = 0
        
        return df
    
    def _generate_momentum_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate momentum-based signals"""
        try:
            # RSI Signal
            if 'RSI_14' in df.columns:
                df['RSI_Signal'] = np.where(df['RSI_14'] < 30, 1,
                                           np.where(df['RSI_14'] > 70, -1, 0))
                # RSI divergence zones
                df['RSI_Oversold'] = np.where(df['RSI_14'] < 20, 1, 0)
                df['RSI_Overbought'] = np.where(df['RSI_14'] > 80, 1, 0)
            else:
                df['RSI_Signal'] = 0
                df['RSI_Oversold'] = 0
                df['RSI_Overbought'] = 0
            
            # Stochastic Signal
            if 'Stoch_K' in df.columns and 'Stoch_D' in df.columns:
                df['Stoch_Signal'] = np.where(df['Stoch_K'] < 20, 1,
                                            np.where(df['Stoch_K'] > 80, -1, 0))
                # Stochastic cross confirmation (handle None values)
                stoch_d_filled = df['Stoch_D'].fillna(df['Stoch_K']).infer_objects(copy=False)  # Fill None with Stoch_K
                df['Stoch_Cross'] = np.where(df['Stoch_K'] > stoch_d_filled, 1, -1)
            else:
                df['Stoch_Signal'] = 0
                df['Stoch_Cross'] = 0
            
            # Rate of Change Signal
            if 'ROC_10' in df.columns:
                df['ROC_Signal'] = np.where(df['ROC_10'] > 5, 1,
                                          np.where(df['ROC_10'] < -5, -1, 0))
            else:
                df['ROC_Signal'] = 0
            
            # CCI Signal
            if 'CCI_20' in df.columns:
                df['CCI_Signal'] = np.where(df['CCI_20'] < -100, 1,
                                          np.where(df['CCI_20'] > 100, -1, 0))
            else:
                df['CCI_Signal'] = 0
            
            # Williams %R Signal
            if 'Williams_R' in df.columns:
                df['WilliamsR_Signal'] = np.where(df['Williams_R'] > -20, -1,
                                               np.where(df['Williams_R'] < -80, 1, 0))
            else:
                df['WilliamsR_Signal'] = 0
            
            # Combined momentum signal
            df['Momentum_Signal'] = (
                df['RSI_Signal'] * self.momentum_weights['RSI_Signal'] +
                df['Stoch_Signal'] * self.momentum_weights['Stoch_Signal'] +
                df['ROC_Signal'] * self.momentum_weights['ROC_Signal'] +
                df['CCI_Signal'] * self.momentum_weights['CCI_Signal']
            )
            
            logger.debug("Generated momentum signals")
            
        except Exception as e:
            logger.error(f"Error generating momentum signals: {str(e)}")
            df['Momentum_Signal'] = 0
        
        return df
    
    def _generate_volatility_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate volatility-based signals"""
        try:
            # Bollinger Bands Position Signal
            if 'BB_Position' in df.columns:
                # BB_Position: 0 = lower band, 1 = upper band
                df['BB_Signal'] = np.where(df['BB_Position'] < 0.2, 1,
                                         np.where(df['BB_Position'] > 0.8, -1, 0))
                # Squeeze detection (low volatility)
                if 'BB_Width' in df.columns:
                    df['BB_Squeeze'] = np.where(df['BB_Width'] < df['BB_Width'].rolling(20).mean() * 0.8, 1, 0)
                else:
                    df['BB_Squeeze'] = 0
            else:
                df['BB_Signal'] = 0
                df['BB_Squeeze'] = 0
            
            # ATR Signal (volatility expansion)
            if 'ATR_14' in df.columns:
                # High ATR compared to recent average indicates volatility expansion
                atr_ma = df['ATR_14'].rolling(20).mean()
                df['ATR_Signal'] = np.where(df['ATR_14'] > atr_ma * 1.2, 1, 0)
                df['ATR_Expansion'] = df['ATR_14'] / atr_ma
            else:
                df['ATR_Signal'] = 0
                df['ATR_Expansion'] = 1
            
            # Historical Volatility Signal
            if 'HV_20' in df.columns:
                # High volatility (>30%) suggests caution
                df['HV_Signal'] = np.where(df['HV_20'] > 30, -1,
                                         np.where(df['HV_20'] < 15, 1, 0))
            else:
                df['HV_Signal'] = 0
            
            # Combined volatility signal
            df['Volatility_Signal'] = (
                df['BB_Signal'] * self.volatility_weights['BB_Position'] +
                df['ATR_Signal'] * self.volatility_weights['ATR_Signal'] +
                df['HV_Signal'] * self.volatility_weights['HV_Signal']
            )
            
            logger.debug("Generated volatility signals")
            
        except Exception as e:
            logger.error(f"Error generating volatility signals: {str(e)}")
            df['Volatility_Signal'] = 0
        
        return df
    
    def _generate_volume_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate volume-based signals"""
        try:
            # OBV Signal
            if 'OBV' in df.columns:
                # OBV trend
                obv_ma = df['OBV'].rolling(20).mean()
                df['OBV_Signal'] = np.where(df['OBV'] > obv_ma, 1, -1)
                # OBV divergence
                df['OBV_Divergence'] = np.where(
                    (df['Close'] > df['Close'].shift(1)) & (df['OBV'] < df['OBV'].shift(1)), -1,
                    np.where(
                        (df['Close'] < df['Close'].shift(1)) & (df['OBV'] > df['OBV'].shift(1)), 1, 0
                    )
                )
            else:
                df['OBV_Signal'] = 0
                df['OBV_Divergence'] = 0
            
            # Volume Ratio Signal
            if 'Volume_Ratio' in df.columns:
                # High volume (>2x average) confirms price moves
                df['Volume_Signal'] = np.where(df['Volume_Ratio'] > 2, 1,
                                             np.where(df['Volume_Ratio'] < 0.5, -1, 0))
            else:
                df['Volume_Signal'] = 0
            
            # PVT Signal
            if 'PVT' in df.columns:
                pvt_ma = df['PVT'].rolling(20).mean()
                df['PVT_Signal'] = np.where(df['PVT'] > pvt_ma, 1, -1)
            else:
                df['PVT_Signal'] = 0
            
            # VWAP Signal
            if 'VWAP' in df.columns:
                df['VWAP_Signal'] = np.where(df['Close'] > df['VWAP'], 1, -1)
            else:
                df['VWAP_Signal'] = 0
            
            # Combined volume signal
            df['Volume_Signal_Combined'] = (
                df['OBV_Signal'] * self.volume_weights['OBV_Signal'] +
                df['Volume_Signal'] * self.volume_weights['Volume_Ratio'] +
                df['PVT_Signal'] * self.volume_weights['PVT_Signal']
            )
            
            logger.debug("Generated volume signals")
            
        except Exception as e:
            logger.error(f"Error generating volume signals: {str(e)}")
            df['Volume_Signal_Combined'] = 0
        
        return df
    
    def _aggregate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate all signals into final weighted score"""
        try:
            # Weighted aggregation
            df['Final_Score'] = (
                df['Trend_Signal'] * self.indicator_weights['trend'] +
                df['Momentum_Signal'] * self.indicator_weights['momentum'] +
                df['Volatility_Signal'] * self.indicator_weights['volatility'] +
                df['Volume_Signal_Combined'] * self.indicator_weights['volume']
            )
            
            # Normalize score to [-1, 1] range
            df['Final_Score_Normalized'] = np.clip(df['Final_Score'], -1, 1)
            
            # Signal strength categories
            df['Signal_Strength'] = np.where(
                df['Final_Score_Normalized'] >= 0.5, 'Strong',
                np.where(
                    df['Final_Score_Normalized'] <= -0.5, 'Strong',
                    'Moderate'
                )
            )
            
            # Signal direction
            df['Signal_Direction'] = np.where(
                df['Final_Score_Normalized'] > 0, 'Bullish',
                np.where(df['Final_Score_Normalized'] < 0, 'Bearish', 'Neutral')
            )
            
            logger.debug("Aggregated signals into final score")
            
        except Exception as e:
            logger.error(f"Error aggregating signals: {str(e)}")
            df['Final_Score'] = 0
            df['Final_Score_Normalized'] = 0
            df['Signal_Strength'] = 'Moderate'
            df['Signal_Direction'] = 'Neutral'
        
        return df
    
    def get_signal_summary(self, df: pd.DataFrame) -> Dict[str, any]:
        """Get summary of latest signals"""
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        
        return {
            'final_score': latest.get('Final_Score_Normalized', 0),
            'signal_strength': latest.get('Signal_Strength', 'Moderate'),
            'signal_direction': latest.get('Signal_Direction', 'Neutral'),
            'trend_signal': latest.get('Trend_Signal', 0),
            'momentum_signal': latest.get('Momentum_Signal', 0),
            'volatility_signal': latest.get('Volatility_Signal', 0),
            'volume_signal': latest.get('Volume_Signal_Combined', 0),
            'individual_signals': {
                'ema_signal': latest.get('EMA_Signal', 0),
                'sma_signal': latest.get('SMA_Signal', 0),
                'macd_signal': latest.get('MACD_Signal', 0),
                'rsi_signal': latest.get('RSI_Signal', 0),
                'stoch_signal': latest.get('Stoch_Signal', 0),
                'bb_signal': latest.get('BB_Signal', 0),
                'obv_signal': latest.get('OBV_Signal', 0)
            }
        }
    
    def get_signal_history(self, df: pd.DataFrame, periods: int = 20) -> pd.DataFrame:
        """Get signal history for analysis"""
        if df.empty:
            return pd.DataFrame()
        
        columns = [
            'Final_Score_Normalized', 'Signal_Strength', 'Signal_Direction',
            'Trend_Signal', 'Momentum_Signal', 'Volatility_Signal', 'Volume_Signal_Combined'
        ]
        
        available_columns = [col for col in columns if col in df.columns]
        
        return df[available_columns].tail(periods)
