"""
Tests for reconciliation service to ensure performance tracking integrity
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.recon_service import ReconService
from app.models import ReconData


class TestReconciliationService:
    """Test suite for reconciliation service logic integrity"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.recon_service = ReconService()
        
        # Sample recommendation data
        self.sample_recommendation = {
            'symbol': 'AAPL',
            'recommendation': 'Buy',
            'price': 150.0,
            'target_price': 165.0,  # 10% profit target
            'stop_loss': 141.0,      # 6% stop loss
            'timestamp': '2026-02-01T15:00:00.000Z'
        }
        
        # Sample current market data
        self.sample_current_price = 160.0  # Between target and stop loss
    
    def test_reconciliation_calculation_integrity(self):
        """Test that reconciliation calculations are correct"""
        # Mock yfinance to return controlled data
        with patch('yfinance.Ticker') as mock_ticker:
            mock_history = Mock()
            mock_history.empty = False
            mock_history.iloc = {'Close': self.sample_current_price}
            
            mock_ticker_instance = Mock()
            mock_ticker_instance.history.return_value = mock_history
            mock_ticker.return_value = mock_ticker_instance
            
            # Run reconciliation
            result = self.recon_service._reconcile_recommendation(self.sample_recommendation)
            
            # Verify result structure
            assert isinstance(result, ReconData), "Should return ReconData object"
            assert result.symbol == 'AAPL', "Symbol should match"
            assert result.original_recommendation == 'Buy', "Recommendation should match"
            assert result.original_price == 150.0, "Original price should match"
            assert result.target_price == 165.0, "Target price should match"
            assert result.stop_loss == 141.0, "Stop loss should match"
            assert result.current_price == self.sample_current_price, "Current price should match"
            
            # Verify calculations
            assert isinstance(result.days_elapsed, int), "Days elapsed should be integer"
            assert result.days_elapsed >= 0, "Days elapsed should be non-negative"
            
            # Verify target/stop loss logic
            assert result.target_met == (self.sample_current_price >= 165.0), \
                "Target met should be calculated correctly"
            assert result.stop_loss_hit == (self.sample_current_price <= 141.0), \
                "Stop loss hit should be calculated correctly"
    
    def test_target_met_logic(self):
        """Test target met detection logic"""
        test_cases = [
            (170.0, True),   # Above target
            (165.0, True),   # Exactly at target
            (164.99, False), # Just below target
            (150.0, False),  # At original price
            (140.0, False)   # Below stop loss
        ]
        
        for current_price, expected_target_met in test_cases:
            with patch('yfinance.Ticker') as mock_ticker:
                mock_history = Mock()
                mock_history.empty = False
                mock_history.iloc = {'Close': current_price}
                
                mock_ticker_instance = Mock()
                mock_ticker_instance.history.return_value = mock_history
                mock_ticker.return_value = mock_ticker_instance
                
                result = self.recon_service._reconcile_recommendation(self.sample_recommendation)
                
                assert result.target_met == expected_target_met, \
                    f"Target met should be {expected_target_met} for price {current_price}, got {result.target_met}"
    
    def test_stop_loss_hit_logic(self):
        """Test stop loss hit detection logic"""
        test_cases = [
            (130.0, True),   # Below stop loss
            (141.0, True),   # Exactly at stop loss
            (141.01, False), # Just above stop loss
            (150.0, False),  # At original price
            (160.0, False)   # Above original price
        ]
        
        for current_price, expected_stop_loss_hit in test_cases:
            with patch('yfinance.Ticker') as mock_ticker:
                mock_history = Mock()
                mock_history.empty = False
                mock_history.iloc = {'Close': current_price}
                
                mock_ticker_instance = Mock()
                mock_ticker_instance.history.return_value = mock_history
                mock_ticker.return_value = mock_ticker_instance
                
                result = self.recon_service._reconcile_recommendation(self.sample_recommendation)
                
                assert result.stop_loss_hit == expected_stop_loss_hit, \
                    f"Stop loss hit should be {expected_stop_loss_hit} for price {current_price}, got {result.stop_loss_hit}"
    
    def test_days_elapsed_calculation(self):
        """Test days elapsed calculation"""
        # Test with different timestamps
        test_timestamps = [
            (datetime.utcnow() - timedelta(days=5), 5),
            (datetime.utcnow() - timedelta(days=1), 1),
            (datetime.utcnow() - timedelta(hours=12), 0),  # Less than 1 day
            (datetime.utcnow(), 0)  # Same day
        ]
        
        for past_time, expected_days in test_timestamps:
            recommendation = self.sample_recommendation.copy()
            recommendation['timestamp'] = past_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            
            with patch('yfinance.Ticker') as mock_ticker:
                mock_history = Mock()
                mock_history.empty = False
                mock_history.iloc = {'Close': 155.0}
                
                mock_ticker_instance = Mock()
                mock_ticker_instance.history.return_value = mock_history
                mock_ticker.return_value = mock_ticker_instance
                
                result = self.recon_service._reconcile_recommendation(recommendation)
                
                assert result.days_elapsed == expected_days, \
                    f"Days elapsed should be {expected_days} for timestamp {past_time}, got {result.days_elapsed}"
    
    def test_missing_market_data_handling(self):
        """Test handling of missing market data"""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker_instance.history.return_value = Mock(empty=True)  # Empty data
            mock_ticker.return_value = mock_ticker_instance
            
            result = self.recon_service._reconcile_recommendation(self.sample_recommendation)
            
            assert result is None, "Should return None when market data is missing"
    
    def test_recommendation_data_structure_integrity(self):
        """Test that recommendation data structure is handled correctly"""
        # Test with missing optional fields
        incomplete_recommendation = {
            'symbol': 'AAPL',
            'recommendation': 'Buy',
            'price': 150.0,
            'timestamp': '2026-02-01T15:00:00.000Z'
            # Missing target_price and stop_loss
        }
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_history = Mock()
            mock_history.empty = False
            mock_history.iloc = {'Close': 155.0}
            
            mock_ticker_instance = Mock()
            mock_ticker_instance.history.return_value = mock_history
            mock_ticker.return_value = mock_ticker_instance
            
            result = self.recon_service._reconcile_recommendation(incomplete_recommendation)
            
            assert result is not None, "Should handle incomplete recommendation data"
            assert result.target_price is None, "Target price should be None when not provided"
            assert result.stop_loss is None, "Stop loss should be None when not provided"
            assert result.target_met is False, "Target met should be False when no target"
            assert result.stop_loss_hit is False, "Stop loss hit should be False when no stop loss"
    
    def test_recon_summary_calculation_integrity(self):
        """Test reconciliation summary calculations"""
        # Mock S3 responses for different dates
        mock_recon_data = [
            {
                'date': '2026-02-01',
                'reconciliations': [
                    {
                        'symbol': 'AAPL',
                        'original_recommendation': 'Buy',
                        'days_elapsed': 5,
                        'target_met': True,
                        'stop_loss_hit': False
                    },
                    {
                        'symbol': 'GOOGL',
                        'original_recommendation': 'Hold',
                        'days_elapsed': 3,
                        'target_met': False,
                        'stop_loss_hit': True
                    }
                ]
            },
            {
                'date': '2026-02-02',
                'reconciliations': [
                    {
                        'symbol': 'MSFT',
                        'original_recommendation': 'Buy',
                        'days_elapsed': 2,
                        'target_met': True,
                        'stop_loss_hit': False
                    }
                ]
            }
        ]
        
        with patch.object(self.recon_service, 's3_client') as mock_s3:
            # Mock S3 get_object responses
            mock_response = Mock()
            mock_response.get.return_value = Mock()
            mock_response.Body.read.return_value.decode.return_value = '{"reconciliations": []}'
            
            # Set up different responses for different calls
            def mock_get_object(Bucket, Key):
                response = Mock()
                if 'recon/daily/2026-02-01' in Key:
                    response.Body.read.return_value.decode.return_value = str(mock_recon_data[0]).replace("'", '"')
                elif 'recon/daily/2026-02-02' in Key:
                    response.Body.read.return_value.decode.return_value = str(mock_recon_data[1]).replace("'", '"')
                else:
                    # Simulate file not found
                    from botocore.exceptions import ClientError
                    error_response = {'Error': {'Code': 'NoSuchKey'}}
                    raise ClientError(error_response, 'GetObject')
                return response
            
            mock_s3.get_object.side_effect = mock_get_object
            
            # Run summary calculation
            summary = self.recon_service.get_recon_summary(days=30)
            
            # Verify summary structure
            assert 'total_reconciled' in summary, "Summary should include total reconciled"
            assert 'targets_met' in summary, "Summary should include targets met"
            assert 'stop_losses_hit' in summary, "Summary should include stop losses hit"
            assert 'avg_days_to_target' in summary, "Summary should include average days to target"
            assert 'performance_by_recommendation' in summary, "Summary should include performance by recommendation"
            
            # Verify calculations
            assert summary['total_reconciled'] == 3, "Should reconcile 3 items total"
            assert summary['targets_met'] == 2, "Should have 2 targets met"
            assert summary['stop_losses_hit'] == 1, "Should have 1 stop loss hit"
            assert summary['avg_days_to_target'] == 3.5, "Average days to target should be (5+2)/2 = 3.5"
            
            # Verify performance by recommendation
            perf_by_rec = summary['performance_by_recommendation']
            assert 'Buy' in perf_by_rec, "Should track Buy recommendations"
            assert 'Hold' in perf_by_rec, "Should track Hold recommendations"
            
            assert perf_by_rec['Buy']['count'] == 2, "Should have 2 Buy recommendations"
            assert perf_by_rec['Buy']['targets_met'] == 2, "Should have 2 Buy targets met"
            assert perf_by_rec['Buy']['stop_losses_hit'] == 0, "Should have 0 Buy stop losses hit"
            
            assert perf_by_rec['Hold']['count'] == 1, "Should have 1 Hold recommendation"
            assert perf_by_rec['Hold']['targets_met'] == 0, "Should have 0 Hold targets met"
            assert perf_by_rec['Hold']['stop_losses_hit'] == 1, "Should have 1 Hold stop loss hit"
    
    def test_error_handling_integrity(self):
        """Test error handling in reconciliation service"""
        # Test with invalid recommendation data
        invalid_recommendation = {
            'symbol': '',  # Empty symbol
            'recommendation': 'Invalid',
            'price': 'not_a_number',
            'timestamp': 'invalid-date'
        }
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker_instance.history.return_value = Mock(empty=True)
            mock_ticker.return_value = mock_ticker_instance
            
            # Should not crash, should return None
            result = self.recon_service._reconcile_recommendation(invalid_recommendation)
            assert result is None, "Should handle invalid data gracefully"
    
    def test_performance_tracking_accuracy(self):
        """Test that performance tracking metrics are accurate"""
        # Create test data with known outcomes
        test_recommendations = [
            {
                'symbol': 'STOCK1',
                'original_recommendation': 'Buy',
                'days_elapsed': 10,
                'target_met': True,
                'stop_loss_hit': False
            },
            {
                'symbol': 'STOCK2',
                'original_recommendation': 'Buy',
                'days_elapsed': 5,
                'target_met': True,
                'stop_loss_hit': False
            },
            {
                'symbol': 'STOCK3',
                'original_recommendation': 'Sell',
                'days_elapsed': 3,
                'target_met': False,
                'stop_loss_hit': True
            }
        ]
        
        # Mock S3 to return test data
        with patch.object(self.recon_service, 's3_client') as mock_s3:
            mock_response = Mock()
            mock_response.Body.read.return_value.decode.return_value = str({
                'date': '2026-02-01',
                'reconciliations': test_recommendations
            }).replace("'", '"')
            mock_s3.get_object.return_value = mock_response
            
            summary = self.recon_service.get_recon_summary(days=30)
            
            # Verify accuracy
            assert summary['total_reconciled'] == 3, "Should count all recommendations"
            assert summary['targets_met'] == 2, "Should count only targets met"
            assert summary['stop_losses_hit'] == 1, "Should count only stop losses hit"
            assert summary['avg_days_to_target'] == 7.5, "Should average only targets met days: (10+5)/2"
            
            # Verify recommendation type breakdown
            buy_perf = summary['performance_by_recommendation']['Buy']
            assert buy_perf['count'] == 2, "Should count Buy recommendations correctly"
            assert buy_perf['targets_met'] == 2, "Should count Buy targets met correctly"
            assert buy_perf['stop_losses_hit'] == 0, "Should count Buy stop losses correctly"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
