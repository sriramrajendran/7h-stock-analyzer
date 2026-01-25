#!/usr/bin/env python3
"""
Tests for Portfolio Forklift Module
"""

import pytest
import os
import tempfile
import pandas as pd
from core.portfolio_forklift import PortfolioForklift


class TestPortfolioForklift:
    """Test suite for PortfolioForklift class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.forklift = PortfolioForklift()
        
    def create_test_csv(self, data, filename='test_portfolio.csv'):
        """Create a temporary CSV file for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        df = pd.DataFrame(data)
        df.to_csv(temp_file.name, index=False)
        temp_file.close()
        return temp_file.name
    
    def test_init(self):
        """Test PortfolioForklift initialization"""
        assert self.forklift.supported_brokers == ['robinhood', 'etrade', 'csv', 'fidelity', 'schwab']
        assert self.forklift.portfolio_data == []
    
    def test_import_from_robinhood_success(self):
        """Test successful Robinhood import"""
        data = {
            'symbol': ['AAPL', 'MSFT', 'GOOGL'],
            'quantity': [10, 5, 15],
            'average_buy_price': [150.0, 250.0, 100.0],
            'current_price': [160.0, 260.0, 110.0],
            'equity': [1600.0, 1300.0, 1650.0]
        }
        
        csv_file = self.create_test_csv(data)
        try:
            result = self.forklift.import_from_robinhood(csv_file)
            
            assert result['success'] is True
            assert result['broker'] == 'robinhood'
            assert result['total_holdings'] == 3
            
            portfolio = result['portfolio']
            assert len(portfolio) == 3
            assert portfolio[0]['symbol'] == 'AAPL'
            assert portfolio[0]['quantity'] == 10.0
            assert portfolio[0]['average_cost'] == 150.0
            assert portfolio[0]['current_price'] == 160.0
            
        finally:
            os.unlink(csv_file)
    
    def test_import_from_robinhood_missing_columns(self):
        """Test Robinhood import with missing required columns"""
        data = {'symbol': ['AAPL', 'MSFT']}  # Missing quantity
        
        csv_file = self.create_test_csv(data)
        try:
            result = self.forklift.import_from_robinhood(csv_file)
            
            assert result['success'] is False
            assert 'Missing required columns' in result['error']
            assert result['broker'] == 'robinhood'
            
        finally:
            os.unlink(csv_file)
    
    def test_import_from_etrade_success(self):
        """Test successful E-Trade import"""
        data = {
            'Symbol': ['AAPL', 'MSFT'],
            'Quantity': [10, 5],
            'Price': [160.0, 260.0],
            'Value': [1600.0, 1300.0],
            'Cost Basis': [1500.0, 1250.0]
        }
        
        csv_file = self.create_test_csv(data)
        try:
            result = self.forklift.import_from_etrade(csv_file)
            
            assert result['success'] is True
            assert result['broker'] == 'etrade'
            assert result['total_holdings'] == 2
            
            portfolio = result['portfolio']
            assert len(portfolio) == 2
            assert portfolio[0]['symbol'] == 'AAPL'
            assert portfolio[0]['quantity'] == 10.0
            assert portfolio[0]['average_cost'] == 150.0  # Cost Basis / Quantity
            
        finally:
            os.unlink(csv_file)
    
    def test_import_from_csv_success(self):
        """Test successful generic CSV import"""
        data = {
            'Symbol': ['AAPL', 'MSFT'],
            'Quantity': [10, 5],
            'Average Cost': [150.0, 250.0],
            'Last Price': [160.0, 260.0]
        }
        
        csv_file = self.create_test_csv(data)
        try:
            result = self.forklift.import_from_csv(csv_file)
            
            assert result['success'] is True
            assert result['broker'] == 'csv'
            assert result['total_holdings'] == 2
            
            portfolio = result['portfolio']
            assert len(portfolio) == 2
            assert portfolio[0]['symbol'] == 'AAPL'
            assert portfolio[0]['quantity'] == 10.0
            
        finally:
            os.unlink(csv_file)
    
    def test_validate_portfolio_data_success(self):
        """Test successful portfolio data validation"""
        portfolio_data = [
            {
                'symbol': 'AAPL',
                'quantity': 10,
                'average_cost': 150.0,
                'current_price': 160.0,
                'broker': 'test'
            },
            {
                'symbol': 'MSFT',
                'quantity': 5,
                'average_cost': 250.0,
                'current_price': 260.0,
                'broker': 'test'
            }
        ]
        
        result = self.forklift.validate_portfolio_data(portfolio_data)
        
        assert result['valid'] is True
        assert len(result['validated_data']) == 2
        assert len(result['errors']) == 0
        assert result['total_processed'] == 2
        assert result['total_valid'] == 2
    
    def test_validate_portfolio_data_errors(self):
        """Test portfolio data validation with errors"""
        portfolio_data = [
            {'symbol': '', 'quantity': 10, 'broker': 'test'},  # Missing symbol
            {'symbol': 'MSFT', 'quantity': -5, 'broker': 'test'},  # Invalid quantity
            {'symbol': 'GOOGL', 'quantity': 15, 'broker': 'test'}  # Valid
        ]
        
        result = self.forklift.validate_portfolio_data(portfolio_data)
        
        assert result['valid'] is False
        assert len(result['validated_data']) == 1  # Only GOOGL is valid
        assert len(result['errors']) == 2
        assert result['total_processed'] == 3
        assert result['total_valid'] == 1
    
    def test_get_portfolio_summary(self):
        """Test portfolio summary generation"""
        portfolio_data = [
            {
                'symbol': 'AAPL',
                'quantity': 10,
                'current_price': 160.0,
                'equity_value': 1600.0,
                'gain_loss': 100.0,
                'gain_loss_pct': 6.67
            },
            {
                'symbol': 'MSFT',
                'quantity': 5,
                'current_price': 260.0,
                'equity_value': 1300.0,
                'gain_loss': 50.0,
                'gain_loss_pct': 4.0
            },
            {
                'symbol': 'TSLA',
                'quantity': 8,
                'current_price': 200.0,
                'equity_value': 1600.0,
                'gain_loss': -80.0,
                'gain_loss_pct': -4.76
            }
        ]
        
        summary = self.forklift.get_portfolio_summary(portfolio_data)
        
        assert summary['total_holdings'] == 3
        assert summary['total_equity_value'] == 4500.0
        assert summary['total_gain_loss'] == 70.0
        assert summary['gainers_count'] == 2
        assert summary['losers_count'] == 1
        assert summary['best_performer']['symbol'] == 'AAPL'
        assert summary['worst_performer']['symbol'] == 'TSLA'
    
    def test_auto_detect_broker_robinhood(self):
        """Test auto-detection of Robinhood files"""
        # Test by filename
        assert self.forklift.auto_detect_broker('robinhood_portfolio.csv') == 'robinhood'
        assert self.forklift.auto_detect_broker('rh_export.csv') == 'robinhood'
        
        # Test by content
        data = {'symbol': ['AAPL'], 'average_buy_price': [150.0], 'quantity': [10]}
        csv_file = self.create_test_csv(data)
        try:
            assert self.forklift.auto_detect_broker(csv_file) == 'robinhood'
        finally:
            os.unlink(csv_file)
    
    def test_auto_detect_broker_etrade(self):
        """Test auto-detection of E-Trade files"""
        # Test by filename
        assert self.forklift.auto_detect_broker('etrade_portfolio.csv') == 'etrade'
        assert self.forklift.auto_detect_broker('e-trade_export.csv') == 'etrade'
        
        # Test by content
        data = {'Symbol': ['AAPL'], 'Cost Basis': [1500.0], 'Quantity': [10]}
        csv_file = self.create_test_csv(data)
        try:
            assert self.forklift.auto_detect_broker(csv_file) == 'etrade'
        finally:
            os.unlink(csv_file)
    
    def test_import_portfolio_auto_detect(self):
        """Test main import method with auto-detection"""
        data = {
            'symbol': ['AAPL', 'MSFT'],
            'quantity': [10, 5],
            'average_buy_price': [150.0, 250.0],
            'current_price': [160.0, 260.0]
        }
        
        csv_file = self.create_test_csv(data)
        try:
            result = self.forklift.import_portfolio(csv_file)  # Auto-detect
            
            assert result['success'] is True
            assert result['broker'] == 'robinhood'  # Should detect based on average_buy_price column
            assert 'validated_portfolio' in result
            assert 'summary' in result
            
        finally:
            os.unlink(csv_file)
    
    def test_import_portfolio_file_not_found(self):
        """Test import with non-existent file"""
        result = self.forklift.import_portfolio('non_existent_file.csv')
        
        assert result['success'] is False
        assert 'File not found' in result['error']
    
    def test_save_portfolio_to_config(self):
        """Test saving portfolio to config file"""
        portfolio_data = [
            {'symbol': 'AAPL', 'quantity': 10},
            {'symbol': 'MSFT', 'quantity': 5},
            {'symbol': 'GOOGL', 'quantity': 15}
        ]
        
        temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_config.close()
        
        try:
            result = self.forklift.save_portfolio_to_config(portfolio_data, temp_config.name)
            
            assert result['success'] is True
            assert result['symbols_saved'] == 3
            assert set(result['symbols']) == {'AAPL', 'MSFT', 'GOOGL'}
            
            # Verify file content
            with open(temp_config.name, 'r') as f:
                content = f.read()
                assert 'AAPL' in content
                assert 'MSFT' in content
                assert 'GOOGL' in content
                assert 'Import date:' in content
                
        finally:
            os.unlink(temp_config.name)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
