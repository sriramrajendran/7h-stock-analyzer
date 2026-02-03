"""
Tests for signal engine to ensure signal generation integrity
"""

import pytest
import sys
import os
import pandas as pd
import numpy as np

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.modules.signal_engine import SignalEngine


class TestSignalEngine:
    """Test suite for signal engine logic integrity"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.engine = SignalEngine()
        
        # Create sample data with known indicator values
        np.random.seed(42)  # For reproducible tests
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        
        self.sample_df = pd.DataFrame({
            'Open': np.random.uniform(95, 105, 100),
            'High': np.random.uniform(105, 115, 100),
            'Low': np.random.uniform(85, 95, 100),
            'Close': np.random.uniform(90, 110, 100),
            'Volume': np.random.uniform(1000000, 5000000, 100),
            # Technical indicators
            'RSI_14': np.random.uniform(20, 80, 100),
            'MACD': np.random.uniform(-2, 2, 100),
            'MACD_Signal': np.random.uniform(-1, 1, 100),
            'EMA_12': np.random.uniform(95, 105, 100),
            'EMA_26': np.random.uniform(90, 110, 100),
            'SMA_50': np.random.uniform(95, 105, 100),
            'SMA_200': np.random.uniform(90, 110, 100),
            'ADX': np.random.uniform(15, 35, 100),
            'Stoch_K': np.random.uniform(0, 100, 100),
            'Stoch_D': np.random.uniform(0, 100, 100),
            'ROC_10': np.random.uniform(-10, 10, 100),
            'Williams_R': np.random.uniform(-100, 0, 100),
            'CCI_20': np.random.uniform(-200, 200, 100),
            'ATR_14': np.random.uniform(1, 5, 100),
            'BB_Upper': np.random.uniform(105, 115, 100),
            'BB_Lower': np.random.uniform(85, 95, 100),
            'OBV': np.random.uniform(1000000, 5000000, 100),
            'Volume_SMA_20': np.random.uniform(2000000, 3000000, 100),
            'VWAP': np.random.uniform(95, 105, 100)
        }, index=dates)
    
    def test_signal_generation_structure(self):
        """Test that signal generation returns proper structure"""
        result_df = self.engine.generate_signals(self.sample_df)
        
        # Should return DataFrame
        assert isinstance(result_df, pd.DataFrame), "Should return DataFrame"
        assert len(result_df) == len(self.sample_df), "Should preserve original length"
        
        # Check that signal columns are added
        signal_columns = [
            'RSI_Signal', 'MACD_Signal', 'EMA_Signal', 'SMA_Signal',
            'ADX_Signal', 'Stoch_Signal', 'ROC_Signal', 'WilliamsR_Signal',
            'CCI_Signal', 'ATR_Signal', 'BB_Signal', 'OBV_Signal',
            'Volume_SMA_Signal', 'VWAP_Signal', 'Volume_Ratio_Signal',
            'Trend_Signal', 'Momentum_Signal', 'Volatility_Signal',
            'Volume_Signal', 'Final_Score'
        ]
        
        for col in signal_columns:
            assert col in result_df.columns, f"Missing signal column: {col}"
    
    def test_rsi_signal_logic(self):
        """Test RSI signal generation logic"""
        # Create test data with known RSI values
        test_df = self.sample_df.copy()
        test_df.loc[test_df.index[0], 'RSI_14'] = 25.0  # Oversold
        test_df.loc[test_df.index[1], 'RSI_14'] = 75.0  # Overbought
        test_df.loc[test_df.index[2], 'RSI_14'] = 50.0  # Neutral
        
        result_df = self.engine.generate_signals(test_df)
        
        # Check RSI signals
        assert result_df.loc[test_df.index[0], 'RSI_Signal'] == 1, "RSI < 30 should give buy signal (1)"
        assert result_df.loc[test_df.index[1], 'RSI_Signal'] == -1, "RSI > 70 should give sell signal (-1)"
        assert result_df.loc[test_df.index[2], 'RSI_Signal'] == 0, "RSI 30-70 should give neutral signal (0)"
    
    def test_macd_signal_logic(self):
        """Test MACD signal generation logic"""
        # Create test data with known MACD values
        test_df = self.sample_df.copy()
        test_df.loc[test_df.index[0], 'MACD'] = 1.0
        test_df.loc[test_df.index[0], 'MACD_Signal'] = 0.5  # MACD > Signal
        test_df.loc[test_df.index[1], 'MACD'] = -1.0
        test_df.loc[test_df.index[1], 'MACD_Signal'] = -0.5  # MACD < Signal
        test_df.loc[test_df.index[2], 'MACD'] = 0.5
        test_df.loc[test_df.index[2], 'MACD_Signal'] = 0.5  # MACD = Signal
        
        result_df = self.engine.generate_signals(test_df)
        
        # Check MACD signals
        assert result_df.loc[test_df.index[0], 'MACD_Signal'] == 1, "MACD > Signal should give buy signal (1)"
        assert result_df.loc[test_df.index[1], 'MACD_Signal'] == -1, "MACD < Signal should give sell signal (-1)"
        assert result_df.loc[test_df.index[2], 'MACD_Signal'] == 0, "MACD = Signal should give neutral signal (0)"
    
    def test_ema_signal_logic(self):
        """Test EMA crossover signal logic"""
        # Create test data with known EMA values
        test_df = self.sample_df.copy()
        test_df.loc[test_df.index[0], 'EMA_12'] = 105.0
        test_df.loc[test_df.index[0], 'EMA_26'] = 100.0  # EMA_12 > EMA_26
        test_df.loc[test_df.index[1], 'EMA_12'] = 95.0
        test_df.loc[test_df.index[1], 'EMA_26'] = 100.0  # EMA_12 < EMA_26
        test_df.loc[test_df.index[2], 'EMA_12'] = 100.0
        test_df.loc[test_df.index[2], 'EMA_26'] = 100.0  # EMA_12 = EMA_26
        
        result_df = self.engine.generate_signals(test_df)
        
        # Check EMA signals
        assert result_df.loc[test_df.index[0], 'EMA_Signal'] == 1, "EMA_12 > EMA_26 should give buy signal (1)"
        assert result_df.loc[test_df.index[1], 'EMA_Signal'] == -1, "EMA_12 < EMA_26 should give sell signal (-1)"
        assert result_df.loc[test_df.index[2], 'EMA_Signal'] == 0, "EMA_12 = EMA_26 should give neutral signal (0)"
    
    def test_sma_signal_logic(self):
        """Test SMA crossover signal logic"""
        # Create test data with known SMA values
        test_df = self.sample_df.copy()
        test_df.loc[test_df.index[0], 'Close'] = 105.0
        test_df.loc[test_df.index[0], 'SMA_50'] = 100.0  # Price > SMA_50
        test_df.loc[test_df.index[1], 'Close'] = 95.0
        test_df.loc[test_df.index[1], 'SMA_50'] = 100.0  # Price < SMA_50
        test_df.loc[test_df.index[2], 'Close'] = 100.0
        test_df.loc[test_df.index[2], 'SMA_50'] = 100.0  # Price = SMA_50
        
        result_df = self.engine.generate_signals(test_df)
        
        # Check SMA signals
        assert result_df.loc[test_df.index[0], 'SMA_Signal'] == 1, "Price > SMA_50 should give buy signal (1)"
        assert result_df.loc[test_df.index[1], 'SMA_Signal'] == -1, "Price < SMA_50 should give sell signal (-1)"
        assert result_df.loc[test_df.index[2], 'SMA_Signal'] == 0, "Price = SMA_50 should give neutral signal (0)"
    
    def test_stochastic_signal_logic(self):
        """Test Stochastic oscillator signal logic"""
        # Create test data with known Stoch values
        test_df = self.sample_df.copy()
        test_df.loc[test_df.index[0], 'Stoch_K'] = 15.0  # Oversold
        test_df.loc[test_df.index[1], 'Stoch_K'] = 85.0  # Overbought
        test_df.loc[test_df.index[2], 'Stoch_K'] = 50.0  # Neutral
        
        result_df = self.engine.generate_signals(test_df)
        
        # Check Stoch signals
        assert result_df.loc[test_df.index[0], 'Stoch_Signal'] == 1, "Stoch_K < 20 should give buy signal (1)"
        assert result_df.loc[test_df.index[1], 'Stoch_Signal'] == -1, "Stoch_K > 80 should give sell signal (-1)"
        assert result_df.loc[test_df.index[2], 'Stoch_Signal'] == 0, "Stoch_K 20-80 should give neutral signal (0)"
    
    def test_final_score_calculation(self):
        """Test final score calculation integrity"""
        result_df = self.engine.generate_signals(self.sample_df)
        
        # Check that Final_Score is calculated
        assert 'Final_Score' in result_df.columns, "Final_Score should be calculated"
        
        # Check that Final_Score is within expected range
        final_scores = result_df['Final_Score'].dropna()
        assert not final_scores.empty, "Should have some Final_Score values"
        assert final_scores.min() >= -1.0, "Final_Score should not be less than -1"
        assert final_scores.max() <= 1.0, "Final_Score should not be greater than 1"
    
    def test_signal_weights_integrity(self):
        """Test that signal weights are correctly applied"""
        # Check that weights are defined
        assert hasattr(self.engine, 'trend_weights'), "Should have trend_weights"
        assert hasattr(self.engine, 'momentum_weights'), "Should have momentum_weights"
        assert hasattr(self.engine, 'volatility_weights'), "Should have volatility_weights"
        assert hasattr(self.engine, 'volume_weights'), "Should have volume_weights"
        
        # Check that weights sum to 1 (or close to it)
        trend_total = sum(self.engine.trend_weights.values())
        momentum_total = sum(self.engine.momentum_weights.values())
        volatility_total = sum(self.engine.volatility_weights.values())
        volume_total = sum(self.engine.volume_weights.values())
        
        assert abs(trend_total - 1.0) < 0.01, f"Trend weights should sum to 1, got {trend_total}"
        assert abs(momentum_total - 1.0) < 0.01, f"Momentum weights should sum to 1, got {momentum_total}"
        assert abs(volatility_total - 1.0) < 0.01, f"Volatility weights should sum to 1, got {volatility_total}"
        assert abs(volume_total - 1.0) < 0.01, f"Volume weights should sum to 1, got {volume_total}"
    
    def test_signal_range_validation(self):
        """Test that all signals are within expected ranges"""
        result_df = self.engine.generate_signals(self.sample_df)
        
        # Check that all signal columns are within [-1, 1] range
        signal_columns = [col for col in result_df.columns if col.endswith('_Signal')]
        
        for col in signal_columns:
            signals = result_df[col].dropna()
            if not signals.empty:
                assert signals.min() >= -1.0, f"Signal {col} should not be less than -1"
                assert signals.max() <= 1.0, f"Signal {col} should not be greater than 1"
    
    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrame"""
        empty_df = pd.DataFrame()
        
        result_df = self.engine.generate_signals(empty_df)
        
        # Should return empty DataFrame
        assert isinstance(result_df, pd.DataFrame), "Should return DataFrame even for empty input"
        assert len(result_df) == 0, "Should return empty DataFrame for empty input"
    
    def test_missing_indicator_handling(self):
        """Test handling of missing indicators"""
        # Create DataFrame with missing indicators
        incomplete_df = pd.DataFrame({
            'Close': [100.0, 101.0, 102.0],
            'Volume': [1000000, 1100000, 1200000]
        })
        
        result_df = self.engine.generate_signals(incomplete_df)
        
        # Should not crash and should handle missing indicators gracefully
        assert isinstance(result_df, pd.DataFrame), "Should return DataFrame even with missing indicators"
        assert len(result_df) == len(incomplete_df), "Should preserve original length"
    
    def test_signal_consistency(self):
        """Test that signals are consistent across similar data"""
        # Create two identical DataFrames
        df1 = self.sample_df.copy()
        df2 = self.sample_df.copy()
        
        result1 = self.engine.generate_signals(df1)
        result2 = self.engine.generate_signals(df2)
        
        # Results should be identical for identical inputs
        pd.testing.assert_frame_equal(result1, result2, check_dtype=False)
    
    def test_signal_calculation_reproducibility(self):
        """Test that signal calculations are reproducible"""
        # Set random seed for reproducibility
        np.random.seed(123)
        
        # Generate signals twice
        result1 = self.engine.generate_signals(self.sample_df)
        result2 = self.engine.generate_signals(self.sample_df)
        
        # Results should be identical
        pd.testing.assert_frame_equal(result1, result2, check_dtype=False)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
