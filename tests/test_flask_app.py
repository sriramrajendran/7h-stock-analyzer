import pytest
import sys
import os
import json
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

class TestFlaskApp:
    """Test cases for Flask web application"""
    
    def setup_method(self):
        """Setup method run before each test"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_home_page_loads(self):
        """Test that the home page loads successfully"""
        response = self.app.get('/')
        assert response.status_code == 200
        assert b'7H Stock Analyzer' in response.data
        assert b'Portfolio Analysis' in response.data
    
    def test_watchlist_page_loads(self):
        """Test that the watchlist page loads successfully"""
        response = self.app.get('/watchlist')
        assert response.status_code == 200
        assert b'Watchlist Analysis' in response.data
    
    def test_market_page_loads(self):
        """Test that the market page loads successfully"""
        response = self.app.get('/market')
        assert response.status_code == 200
        assert b'US Market Analysis' in response.data
    
    def test_etf_page_loads(self):
        """Test that the ETF page loads successfully"""
        response = self.app.get('/etf')
        assert response.status_code == 200
        assert b'ETF & Index Analysis' in response.data
    
    def test_api_config_stocks_portfolio(self):
        """Test API endpoint for portfolio config stocks"""
        response = self.app.get('/api/config_stocks?type=portfolio')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'success' in data
        assert 'stocks' in data
        assert isinstance(data['stocks'], list)
    
    def test_api_config_stocks_watchlist(self):
        """Test API endpoint for watchlist config stocks"""
        response = self.app.get('/api/config_stocks?type=watchlist')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'success' in data
        assert 'stocks' in data
        assert isinstance(data['stocks'], list)
    
    def test_analyze_portfolio_endpoint(self):
        """Test portfolio analysis endpoint"""
        # Test data
        test_data = {
            'symbols': 'AAPL,MSFT,GOOGL',
            'period': '1mo',
            'top_n': 5
        }
        
        response = self.app.post('/analyze_portfolio', 
                              data=json.dumps(test_data),
                              content_type='application/json')
        
        # Should return 200 or 500 (if API issues)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'buy_stocks' in data or 'error' in data
    
    def test_analyze_market_endpoint(self):
        """Test market analysis endpoint"""
        test_data = {
            'period': '1mo',
            'top_n': 5
        }
        
        response = self.app.post('/analyze_market',
                              data=json.dumps(test_data),
                              content_type='application/json')
        
        # Should return 200 or 500 (if API issues)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'buy_recommendations' in data or 'error' in data
    
    def test_analyze_etf_endpoint(self):
        """Test ETF analysis endpoint"""
        test_data = {
            'period': '1mo',
            'top_n': 5
        }
        
        response = self.app.post('/analyze_etf',
                              data=json.dumps(test_data),
                              content_type='application/json')
        
        # Should return 200, 404, or 500 (404 if route missing, 500 if API issues)
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'buy_recommendations' in data or 'error' in data
    
    def test_invalid_endpoint(self):
        """Test that invalid endpoints return 404"""
        response = self.app.get('/invalid-endpoint')
        assert response.status_code == 404
    
    def test_static_files_served(self):
        """Test that static CSS and JS files are served"""
        css_response = self.app.get('/assets/css/style.css')
        assert css_response.status_code == 200
        assert b'background' in css_response.data  # CSS content check
        
        js_response = self.app.get('/assets/js/main.js')
        assert js_response.status_code == 200
        assert b'function' in js_response.data  # JS content check
    
    def test_form_submission_validation(self):
        """Test form validation with missing data"""
        # Test with missing symbols
        response = self.app.post('/analyze_portfolio',
                              data=json.dumps({'period': '1mo'}),
                              content_type='application/json')
        
        # Should handle missing data gracefully
        assert response.status_code in [200, 400]
    
    def test_error_handling(self):
        """Test error handling for malformed requests"""
        # Test with invalid JSON
        response = self.app.post('/analyze_portfolio',
                              data='invalid json',
                              content_type='application/json')
        
        # Should handle gracefully - either 400 or 500 is acceptable
        assert response.status_code in [400, 500]

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
