"""
Tests for API endpoints to ensure API integrity and security
"""

import pytest
import sys
import os
import json
from unittest.mock import Mock, patch

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from app.main import app


class TestAPIEndpoints:
    """Test suite for API endpoint integrity"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.client = TestClient(app)
        
        # Mock API key for testing
        self.valid_api_key = "test-api-key-12345"
        self.invalid_api_key = "invalid-key"
        
        # Set environment variable for API key
        os.environ['API_KEY'] = self.valid_api_key
        os.environ['REQUIRE_AUTH'] = 'true'
    
    def test_health_endpoint_integrity(self):
        """Test health endpoint structure and response"""
        response = self.client.get("/health")
        
        assert response.status_code == 200, "Health endpoint should return 200"
        
        data = response.json()
        assert 'status' in data, "Health response should include status"
        assert 'timestamp' in data, "Health response should include timestamp"
        assert 'version' in data, "Health response should include version"
        
        assert data['status'] == 'healthy', "Status should be healthy"
        assert isinstance(data['timestamp'], str), "Timestamp should be string"
        assert isinstance(data['version'], str), "Version should be string"
    
    def test_api_key_authentication(self):
        """Test API key authentication integrity"""
        # Test without API key
        response = self.client.get("/recommendations")
        assert response.status_code == 403, "Should require API key"
        
        # Test with invalid API key
        response = self.client.get("/recommendations", headers={"X-API-Key": self.invalid_api_key})
        assert response.status_code == 403, "Should reject invalid API key"
        
        # Test with valid API key
        response = self.client.get("/recommendations", headers={"X-API-Key": self.valid_api_key})
        assert response.status_code in [200, 404], "Should accept valid API key"
    
    def test_recommendations_endpoint_structure(self):
        """Test recommendations endpoint structure"""
        with patch('app.main.get_recommendations') as mock_get_rec:
            # Mock successful response
            mock_response = {
                "timestamp": "2026-02-03T15:00:00.000Z",
                "date": "2026-02-03",
                "count": 5,
                "recommendations": [
                    {
                        "symbol": "AAPL",
                        "recommendation": "Buy",
                        "price": 150.0,
                        "target_price": 165.0,
                        "stop_loss": 141.0,
                        "confidence_level": "Medium"
                    }
                ]
            }
            mock_get_rec.return_value = mock_response
            
            response = self.client.get("/recommendations", headers={"X-API-Key": self.valid_api_key})
            
            assert response.status_code == 200, "Should return 200 for valid request"
            
            data = response.json()
            assert 'timestamp' in data, "Should include timestamp"
            assert 'date' in data, "Should include date"
            assert 'count' in data, "Should include count"
            assert 'recommendations' in data, "Should include recommendations list"
            assert isinstance(data['recommendations'], list), "Recommendations should be a list"
            
            if data['recommendations']:
                rec = data['recommendations'][0]
                required_fields = ['symbol', 'recommendation', 'price', 'target_price', 'stop_loss', 'confidence_level']
                for field in required_fields:
                    assert field in rec, f"Recommendation should include {field}"
    
    def test_analysis_endpoint_structure(self):
        """Test single analysis endpoint structure"""
        with patch('app.main.run_single_analysis') as mock_analysis:
            # Mock successful analysis
            mock_analysis.return_value = {
                "symbol": "AAPL",
                "company": "Apple Inc.",
                "price": 150.0,
                "change_pct": 2.5,
                "recommendation": "Buy",
                "score": 0.3,
                "target_price": 165.0,
                "stop_loss": 141.0,
                "confidence_level": "Medium"
            }
            
            response = self.client.get("/analysis/AAPL", headers={"X-API-Key": self.valid_api_key})
            
            assert response.status_code == 200, "Should return 200 for valid ticker"
            
            data = response.json()
            assert 'success' in data, "Should include success flag"
            assert 'data' in data, "Should include data"
            assert 'timestamp' in data, "Should include timestamp"
            
            analysis_data = data['data']
            required_fields = ['symbol', 'company', 'price', 'recommendation', 'target_price', 'stop_loss']
            for field in required_fields:
                assert field in analysis_data, f"Analysis should include {field}"
    
    def test_run_now_endpoint_structure(self):
        """Test manual analysis trigger endpoint"""
        with patch('app.main.run_modular_analysis') as mock_run, \
             patch('app.main.persist_results') as mock_persist, \
             patch('app.main.send_push_notification') as mock_notify:
            
            # Mock successful run
            mock_run.return_value = [{"symbol": "AAPL", "recommendation": "Buy"}]
            
            response = self.client.post("/run-now", headers={"X-API-Key": self.valid_api_key})
            
            assert response.status_code == 200, "Should return 200 for valid request"
            
            data = response.json()
            assert 'status' in data, "Should include status"
            assert 'recommendations' in data, "Should include recommendations count"
            assert 'timestamp' in data, "Should include timestamp"
            
            assert data['status'] == 'success', "Status should be success"
            assert isinstance(data['recommendations'], int), "Recommendations should be integer"
            
            # Verify functions were called
            mock_run.assert_called_once()
            mock_persist.assert_called_once()
            mock_notify.assert_called_once()
    
    def test_recon_endpoints_structure(self):
        """Test reconciliation endpoints structure"""
        # Test recon summary endpoint
        with patch('app.main.ReconService') as mock_recon_service:
            mock_service_instance = Mock()
            mock_service_instance.get_recon_summary.return_value = {
                "total_reconciled": 10,
                "targets_met": 3,
                "stop_losses_hit": 2,
                "avg_days_to_target": 5.5,
                "performance_by_recommendation": {
                    "Buy": {"count": 5, "targets_met": 2, "stop_losses_hit": 1}
                }
            }
            mock_recon_service.return_value = mock_service_instance
            
            response = self.client.get("/recon/summary", headers={"X-API-Key": self.valid_api_key})
            
            assert response.status_code == 200, "Should return 200 for recon summary"
            
            data = response.json()
            required_fields = ['total_reconciled', 'targets_met', 'stop_losses_hit', 'avg_days_to_target']
            for field in required_fields:
                assert field in data, f"Recon summary should include {field}"
        
        # Test recon run endpoint
        with patch('app.main.run_daily_reconciliation') as mock_recon_run:
            mock_recon_run.return_value = {
                "success": True,
                "reconciled_count": 5,
                "timestamp": "2026-02-03T15:00:00.000Z"
            }
            
            response = self.client.post("/recon/run", headers={"X-API-Key": self.valid_api_key})
            
            assert response.status_code == 200, "Should return 200 for recon run"
            
            data = response.json()
            assert 'success' in data, "Should include success flag"
            assert 'reconciled_count' in data, "Should include reconciled count"
            assert 'timestamp' in data, "Should include timestamp"
    
    def test_config_endpoints_structure(self):
        """Test configuration endpoints structure"""
        # Test portfolio config
        with patch('app.main.load_config_from_s3') as mock_config:
            mock_config.return_value = {
                "success": True,
                "config_type": "portfolio",
                "symbols": ["AAPL", "MSFT", "GOOGL"],
                "count": 3
            }
            
            response = self.client.get("/config/portfolio", headers={"X-API-Key": self.valid_api_key})
            
            assert response.status_code == 200, "Should return 200 for config request"
            
            data = response.json()
            assert 'success' in data, "Should include success flag"
            assert 'config_type' in data, "Should include config type"
            assert 'symbols' in data, "Should include symbols list"
            assert 'count' in data, "Should include symbol count"
            
            assert isinstance(data['symbols'], list), "Symbols should be a list"
            assert data['count'] == len(data['symbols']), "Count should match symbols length"
    
    def test_error_handling_integrity(self):
        """Test error handling integrity"""
        # Test invalid ticker
        with patch('app.main.run_single_analysis') as mock_analysis:
            mock_analysis.side_effect = Exception("Invalid ticker")
            
            response = self.client.get("/analysis/INVALID", headers={"X-API-Key": self.valid_api_key})
            
            # Should handle error gracefully
            assert response.status_code in [400, 500], "Should handle invalid ticker gracefully"
        
        # Test missing config
        with patch('app.main.load_config_from_s3') as mock_config:
            mock_config.return_value = {"success": False, "error": "Config not found"}
            
            response = self.client.get("/config/nonexistent", headers={"X-API-Key": self.valid_api_key})
            
            assert response.status_code == 404, "Should return 404 for nonexistent config"
    
    def test_input_validation(self):
        """Test input validation integrity"""
        # Test empty ticker
        response = self.client.get("/analysis/", headers={"X-API-Key": self.valid_api_key})
        assert response.status_code == 404, "Should handle empty ticker"
        
        # Test very long ticker
        long_ticker = "A" * 100
        response = self.client.get(f"/analysis/{long_ticker}", headers={"X-API-Key": self.valid_api_key})
        assert response.status_code in [400, 500], "Should handle invalid ticker length"
        
        # Test special characters in ticker
        special_ticker = "AAPL@#$"
        response = self.client.get(f"/analysis/{special_ticker}", headers={"X-API-Key": self.valid_api_key})
        assert response.status_code in [400, 500], "Should handle special characters"
    
    def test_response_format_consistency(self):
        """Test that response formats are consistent"""
        # Test that all endpoints return JSON
        endpoints = [
            ("/health", "GET"),
            ("/recommendations", "GET"),
            ("/config/portfolio", "GET"),
            ("/recon/summary", "GET")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = self.client.get(endpoint, headers={"X-API-Key": self.valid_api_key})
            else:
                response = self.client.post(endpoint, headers={"X-API-Key": self.valid_api_key})
            
            # Should return JSON or appropriate status code
            if response.status_code == 200:
                assert response.headers["content-type"] == "application/json", \
                    f"{endpoint} should return JSON content type"
    
    def test_rate_limiting_resilience(self):
        """Test API resilience to rapid requests"""
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = self.client.get("/health", headers={"X-API-Key": self.valid_api_key})
            responses.append(response.status_code)
        
        # All should succeed or fail consistently
        unique_statuses = set(responses)
        assert len(unique_statuses) <= 2, "Should handle rapid requests consistently"
    
    def test_security_headers(self):
        """Test security headers are present"""
        response = self.client.get("/health")
        
        # Check for security-related headers (if implemented)
        # This is a placeholder for future security header implementation
        assert response.status_code == 200, "Health endpoint should be accessible"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
