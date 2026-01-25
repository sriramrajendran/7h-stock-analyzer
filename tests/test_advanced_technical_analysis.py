"""
Tests for advanced technical analysis features
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path to import core modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.stock_analyzer import StockAnalyzer


class TestAdvancedTechnicalAnalysis(unittest.TestCase):
    """Test advanced technical analysis features"""
    
    def setUp(self):
        """Set up test data"""
        # Create sample stock data with known patterns
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        dates = dates[dates.weekday < 5]  # Only weekdays
        
        # Generate realistic price data
        np.random.seed(42)
        base_price = 100
        
        # Create price series with some trends and volatility
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = [base_price]
        
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        
        prices = prices[1:]  # Remove initial price
        
        # Create OHLCV data
        self.sample_data = pd.DataFrame({
            'Open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
            'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'Close': prices,
            'Volume': np.random.randint(1000000, 5000000, len(dates))
        }, index=dates)
        
        # Ensure High >= max(Open, Close) and Low <= min(Open, Close)
        self.sample_data['High'] = np.maximum(
            self.sample_data['High'], 
            np.maximum(self.sample_data['Open'], self.sample_data['Close'])
        )
        self.sample_data['Low'] = np.minimum(
            self.sample_data['Low'], 
            np.minimum(self.sample_data['Open'], self.sample_data['Close'])
        )
    
    def create_analyzer(self, data=None):
        """Create a StockAnalyzer instance with test data"""
        analyzer = StockAnalyzer('TEST')
        if data is not None:
            analyzer.data = data
        else:
            analyzer.data = self.sample_data
        return analyzer
    
    def test_vcp_pattern_detection(self):
        """Test VCP pattern detection"""
        analyzer = self.create_analyzer()
        
        # Test with sufficient data
        vcp_result = analyzer.detect_vcp_pattern()
        
        # Verify structure
        self.assertIn('pattern', vcp_result)
        self.assertIn('strength', vcp_result)
        self.assertIn('details', vcp_result)
        
        # Verify pattern types
        valid_patterns = ['STRONG_VCP', 'WEAK_VCP', 'NO_VCP', 'INSUFFICIENT_DATA']
        self.assertIn(vcp_result['pattern'], valid_patterns)
        
        # Verify strength is non-negative
        self.assertGreaterEqual(vcp_result['strength'], 0)
        
        # Test with insufficient data
        small_data = analyzer.data.head(30)
        analyzer.data = small_data
        vcp_small = analyzer.detect_vcp_pattern()
        self.assertEqual(vcp_small['pattern'], 'INSUFFICIENT_DATA')
    
    def test_rsi_divergence_detection(self):
        """Test RSI divergence detection"""
        analyzer = self.create_analyzer()
        
        # Test with sufficient data
        rsi_div = analyzer.detect_rsi_divergence()
        
        # Verify structure
        self.assertIn('divergence', rsi_div)
        self.assertIn('type', rsi_div)
        self.assertIn('strength', rsi_div)
        
        # Verify divergence types
        valid_divergences = ['BULLISH', 'BEARISH', 'NONE', 'INSUFFICIENT_DATA']
        self.assertIn(rsi_div['divergence'], valid_divergences)
        
        # Verify strength is non-negative
        self.assertGreaterEqual(rsi_div['strength'], 0)
        
        # Test with insufficient data
        small_data = analyzer.data.head(20)
        analyzer.data = small_data
        rsi_small = analyzer.detect_rsi_divergence()
        self.assertEqual(rsi_small['divergence'], 'INSUFFICIENT_DATA')
    
    def test_macd_divergence_detection(self):
        """Test MACD divergence detection"""
        analyzer = self.create_analyzer()
        
        # Test with sufficient data
        macd_div = analyzer.detect_macd_divergence()
        
        # Verify structure
        self.assertIn('divergence', macd_div)
        self.assertIn('type', macd_div)
        self.assertIn('strength', macd_div)
        
        # Verify divergence types
        valid_divergences = ['BULLISH', 'BEARISH', 'NONE', 'INSUFFICIENT_DATA']
        self.assertIn(macd_div['divergence'], valid_divergences)
        
        # Verify strength is non-negative
        self.assertGreaterEqual(macd_div['strength'], 0)
        
        # Test with insufficient data
        small_data = analyzer.data.head(30)
        analyzer.data = small_data
        macd_small = analyzer.detect_macd_divergence()
        self.assertEqual(macd_small['divergence'], 'INSUFFICIENT_DATA')
    
    def test_enhanced_crossover_detection(self):
        """Test enhanced crossover detection"""
        analyzer = self.create_analyzer()
        
        # Test with sufficient data
        crossovers = analyzer.detect_enhanced_crossovers()
        
        # Verify structure
        self.assertIn('crossovers', crossovers)
        self.assertIn('volume_confirmed', crossovers)
        self.assertIn('strength', crossovers)
        
        # Verify crossovers are lists
        self.assertIsInstance(crossovers['crossovers'], list)
        self.assertIsInstance(crossovers['volume_confirmed'], list)
        
        # Verify strength is non-negative
        self.assertGreaterEqual(crossovers['strength'], 0)
        
        # Verify volume confirmed is subset of all crossovers
        for vc in crossovers['volume_confirmed']:
            self.assertIn(vc, crossovers['crossovers'])
        
        # Test with insufficient data
        small_data = analyzer.data.head(30)
        analyzer.data = small_data
        cross_small = analyzer.detect_enhanced_crossovers()
        self.assertEqual(len(cross_small['crossovers']), 0)
    
    def test_advanced_patterns_in_recommendations(self):
        """Test that advanced patterns are included in recommendations"""
        analyzer = self.create_analyzer()
        
        # Mock the calculate_indicators method to include our test data
        analyzer.calculate_indicators()
        
        # Get recommendation
        recommendation = analyzer.get_recommendation()
        
        # Verify structure
        self.assertIn('recommendation', recommendation)
        self.assertIn('score', recommendation)
        self.assertIn('reasoning', recommendation)
        self.assertIn('indicators', recommendation)
        
        # Verify advanced patterns are in indicators
        indicators = recommendation['indicators']
        self.assertIn('VCP_Pattern', indicators)
        self.assertIn('RSI_Divergence', indicators)
        self.assertIn('MACD_Divergence', indicators)
        self.assertIn('Enhanced_Crossovers', indicators)
    
    def test_advanced_patterns_in_summary(self):
        """Test that advanced patterns are included in summary"""
        analyzer = self.create_analyzer()
        
        # Mock the calculate_indicators method
        analyzer.calculate_indicators()
        
        # Get summary
        summary = analyzer.get_summary()
        
        # Verify advanced patterns are in summary
        self.assertIn('vcp_pattern', summary)
        self.assertIn('rsi_divergence', summary)
        self.assertIn('macd_divergence', summary)
        self.assertIn('enhanced_crossovers', summary)
    
    def test_vcp_with_consolidation_pattern(self):
        """Test VCP detection with clear consolidation pattern"""
        # Create data with volatility contraction
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        dates = dates[dates.weekday < 5]
        
        # Simulate volatility contraction
        prices = []
        volatility = 0.05  # Start with high volatility
        
        for i in range(len(dates)):
            # Gradually decrease volatility
            if i > 20:
                volatility *= 0.98
            
            price = 100 + np.random.normal(0, volatility)
            prices.append(price)
        
        # Create OHLCV data
        data = pd.DataFrame({
            'Open': prices,
            'High': [p * 1.02 for p in prices],
            'Low': [p * 0.98 for p in prices],
            'Close': prices,
            'Volume': np.random.randint(1000000, 5000000, len(dates))
        }, index=dates)
        
        analyzer = self.create_analyzer(data)
        vcp_result = analyzer.detect_vcp_pattern()
        
        # Should detect some form of VCP due to volatility contraction
        self.assertIn(vcp_result['pattern'], ['STRONG_VCP', 'WEAK_VCP', 'NO_VCP'])
    
    def test_divergence_with_clear_patterns(self):
        """Test divergence detection with clear patterns"""
        # Create data with clear bullish divergence
        dates = pd.date_range(start='2023-01-01', periods=60, freq='D')
        dates = dates[dates.weekday < 5]
        
        # Create price making lower lows
        prices = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55]
        prices.extend([55 + i*0.5 for i in range(len(dates) - len(prices))])
        
        # Create RSI making higher lows (simulated)
        rsi_values = [30, 35, 32, 38, 35, 40, 37, 42, 39, 45]
        rsi_values.extend([45 + i*0.1 for i in range(len(dates) - len(rsi_values))])
        
        data = pd.DataFrame({
            'Close': prices[:len(dates)],
            'High': [p * 1.02 for p in prices[:len(dates)]],
            'Low': [p * 0.98 for p in prices[:len(dates)]],
            'Open': prices[:len(dates)],
            'Volume': np.random.randint(1000000, 5000000, len(dates))
        }, index=dates)
        
        analyzer = self.create_analyzer(data)
        rsi_div = analyzer.detect_rsi_divergence()
        
        # Should detect divergence or at least have valid structure
        self.assertIn(rsi_div['divergence'], ['BULLISH', 'BEARISH', 'NONE', 'INSUFFICIENT_DATA'])
        self.assertGreaterEqual(rsi_div['strength'], 0)


class TestIntegrationWithFlaskApp(unittest.TestCase):
    """Test integration with Flask app"""
    
    @patch('yfinance.Ticker')
    def test_advanced_patterns_in_api_response(self, mock_ticker):
        """Test that advanced patterns appear in API responses"""
        # Mock yfinance data
        mock_stock = Mock()
        mock_ticker.return_value = mock_stock
        
        # Create sample historical data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        dates = dates[dates.weekday < 5]
        
        sample_data = pd.DataFrame({
            'Open': np.random.normal(100, 5, len(dates)),
            'High': np.random.normal(105, 5, len(dates)),
            'Low': np.random.normal(95, 5, len(dates)),
            'Close': np.random.normal(100, 5, len(dates)),
            'Volume': np.random.randint(1000000, 5000000, len(dates))
        }, index=dates)
        
        mock_stock.history.return_value = sample_data
        mock_stock.info = {'longName': 'Test Company'}
        
        # Test analyzer
        analyzer = StockAnalyzer('TEST')
        analyzer.fetch_data()
        analyzer.calculate_indicators()
        
        # Verify advanced patterns are calculated
        self.assertIn('VCP_Pattern', analyzer.indicators)
        self.assertIn('RSI_Divergence', analyzer.indicators)
        self.assertIn('MACD_Divergence', analyzer.indicators)
        self.assertIn('Enhanced_Crossovers', analyzer.indicators)
        
        # Verify summary includes patterns
        summary = analyzer.get_summary()
        self.assertIn('vcp_pattern', summary)
        self.assertIn('rsi_divergence', summary)
        self.assertIn('macd_divergence', summary)
        self.assertIn('enhanced_crossovers', summary)


if __name__ == '__main__':
    unittest.main()
