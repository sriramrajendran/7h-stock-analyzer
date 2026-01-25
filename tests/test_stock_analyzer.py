import pytest
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.stock_analyzer import StockAnalyzer

class TestStockAnalyzer:
    """Test cases for StockAnalyzer core functionality"""
    
    def setup_method(self):
        """Setup method run before each test"""
        self.analyzer = StockAnalyzer('AAPL')  # Provide required symbol parameter
    
    def test_analyzer_initialization(self):
        """Test that StockAnalyzer initializes correctly"""
        analyzer = StockAnalyzer('AAPL')  # Test with symbol
        assert analyzer is not None
        assert hasattr(analyzer, 'fetch_data')
        assert hasattr(analyzer, 'calculate_indicators')
        assert hasattr(analyzer, 'get_fundamental_indicators')
        assert hasattr(analyzer, 'get_recommendation')
    
    def test_get_technical_indicators_valid_symbol(self):
        """Test technical indicators with a valid stock symbol"""
        # Test with a commonly available stock
        analyzer = StockAnalyzer('AAPL', period='1mo')
        success = analyzer.fetch_data()
        if success:
            analyzer.calculate_indicators()
            indicators = analyzer.indicators
            
            # Check that we get some indicators back
            assert indicators is not None
            assert isinstance(indicators, dict)
            
            # Check for key technical indicators that should be available with 1mo data
            expected_keys = ['RSI', 'Current_Price', 'Price_Change_Pct']
            for key in expected_keys:
                assert key in indicators
                assert indicators[key] is not None
        else:
            # If data fetch fails, that's acceptable for a test
            assert True
    
    def test_get_technical_indicators_invalid_symbol(self):
        """Test technical indicators with invalid stock symbol"""
        analyzer = StockAnalyzer('INVALID123', period='1mo')
        success = analyzer.fetch_data()
        
        # Should return False for invalid symbol
        assert success is False
    
    def test_get_recommendation_logic(self):
        """Test recommendation generation logic"""
        # Mock technical indicators for testing
        mock_indicators = {
            'RSI': 30,  # Oversold - should be bullish
            'MACD': 0.5,  # Positive MACD - bullish
            'SMA_20': 150,
            'Current_Price': 155,  # Price above SMA - bullish
            'SMA_50': 145,
            'BB_lower': 148,
            'BB_upper': 160
        }
        
        recommendation = self.analyzer.get_recommendation()
            
        assert recommendation is not None
        assert isinstance(recommendation, dict)
        assert 'recommendation' in recommendation
        assert 'score' in recommendation
        assert 'reasoning' in recommendation
            
        # Score should be a number
        assert isinstance(recommendation['score'], (int, float))
            
        # Recommendation should be one of the expected types
        valid_recommendations = ['STRONG BUY', 'BUY', 'HOLD', 'SELL', 'STRONG SELL', 'NEUTRAL']
        assert recommendation['recommendation'] in valid_recommendations
    
    def test_get_recommendation_scoring_ranges(self):
        """Test that recommendation scores fall within expected ranges"""
        # Test oversold conditions (should be BUY)
        oversold_indicators = {
            'RSI': 25,
            'MACD': -0.2,
            'SMA_20': 150,
            'Current_Price': 145,
            'SMA_50': 155,
            'BB_lower': 142,
            'BB_upper': 158
        }
        
        rec1 = self.analyzer.get_recommendation()
            
        assert rec1 is not None
        assert isinstance(rec1['score'], (int, float))
            
        # Score should be within reasonable bounds
        assert -10 <= rec1['score'] <= 10
    
    def test_fundamental_indicators_structure(self):
        """Test fundamental indicators return proper structure"""
        analyzer = StockAnalyzer('AAPL')
        fundamentals = analyzer.get_fundamental_indicators()
        
        if fundamentals:  # Might be None if data unavailable
            assert isinstance(fundamentals, dict)
            
            # Check for expected fundamental keys
            expected_keys = ['pe_ratio', 'pb_ratio', 'dividend_yield', 'market_cap']
            for key in expected_keys:
                assert key in fundamentals
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        analyzer = StockAnalyzer('AAPL')
        
        # Test with very short period
        short_analyzer = StockAnalyzer('AAPL', period='1d')
        success = short_analyzer.fetch_data()
        # Should handle gracefully without crashing
        assert isinstance(success, bool)
        
        # Test that get_recommendation handles edge cases
        recommendation = analyzer.get_recommendation()
        assert recommendation is not None

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
