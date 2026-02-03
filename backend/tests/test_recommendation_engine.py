"""
Tests for recommendation engine to ensure logic integrity
"""

import pytest
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.modules.recommendation_engine import RecommendationEngine


class TestRecommendationEngine:
    """Test suite for recommendation engine logic integrity"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.engine = RecommendationEngine()
        
        # Create sample data for testing
        self.sample_df = pd.DataFrame({
            'Close': [100.0, 102.0, 98.0, 105.0, 103.0],
            'High': [101.0, 103.0, 99.0, 106.0, 104.0],
            'Low': [99.0, 101.0, 97.0, 104.0, 102.0],
            'Volume': [1000000, 1100000, 900000, 1200000, 1050000],
            'RSI_Signal': [1, 1, -1, 1, 0],
            'MACD_Signal': [1, 1, -1, 1, 0],
            'EMA_Signal': [1, 1, -1, 1, 0],
            'SMA_Signal': [1, 1, -1, 1, 0],
            'BB_Signal': [1, 1, -1, 1, 0],
            'OBV_Signal': [1, 1, -1, 1, 0],
            'Stoch_Signal': [1, 1, -1, 1, 0],
            'ADX_Signal': [1, 1, -1, 1, 0],
            'ATR_Signal': [1, 1, -1, 1, 0],
            'WilliamsR_Signal': [1, 1, -1, 1, 0],
            'CCI_Signal': [1, 1, -1, 1, 0],
            'ROC_Signal': [1, 1, -1, 1, 0],
            'Volume_SMA_Signal': [1, 1, -1, 1, 0],
            'VWAP_Signal': [1, 1, -1, 1, 0],
            'Volume_Ratio_Signal': [1, 1, -1, 1, 0]
        })
    
    def test_target_price_calculation_integrity(self):
        """Test that target price calculations are correct and consistent"""
        current_price = 100.0
        
        # Test Strong Buy target (20% profit)
        target_strong_buy = self.engine._calculate_target_price(current_price, 'Strong Buy')
        assert target_strong_buy == 120.0, f"Strong Buy target should be 120.0, got {target_strong_buy}"
        
        # Test Buy target (10% profit)
        target_buy = self.engine._calculate_target_price(current_price, 'Buy')
        assert target_buy == 110.0, f"Buy target should be 110.0, got {target_buy}"
        
        # Test Hold target (2% profit)
        target_hold = self.engine._calculate_target_price(current_price, 'Hold')
        assert target_hold == 102.0, f"Hold target should be 102.0, got {target_hold}"
        
        # Test Sell target (5% loss)
        target_sell = self.engine._calculate_target_price(current_price, 'Sell')
        assert target_sell == 95.0, f"Sell target should be 95.0, got {target_sell}"
        
        # Test Strong Sell target (20% loss)
        target_strong_sell = self.engine._calculate_target_price(current_price, 'Strong Sell')
        assert target_strong_sell == 80.0, f"Strong Sell target should be 80.0, got {target_strong_sell}"
        
        # Test unknown recommendation (defaults to 1.0)
        target_unknown = self.engine._calculate_target_price(current_price, 'Unknown')
        assert target_unknown == 100.0, f"Unknown target should be 100.0, got {target_unknown}"
    
    def test_stop_loss_calculation_integrity(self):
        """Test that stop loss calculations are correct and favorable"""
        current_price = 100.0
        
        # Test Strong Buy stop loss (8% loss)
        stop_strong_buy = self.engine._calculate_stop_loss(current_price, 'Strong Buy')
        expected_strong_buy = 100.0 * (1 - 0.08)
        assert stop_strong_buy == expected_strong_buy, f"Strong Buy stop loss should be {expected_strong_buy}, got {stop_strong_buy}"
        
        # Test Buy stop loss (6% loss)
        stop_buy = self.engine._calculate_stop_loss(current_price, 'Buy')
        expected_buy = 100.0 * (1 - 0.06)
        assert stop_buy == expected_buy, f"Buy stop loss should be {expected_buy}, got {stop_buy}"
        
        # Test Hold stop loss (1.5% loss)
        stop_hold = self.engine._calculate_stop_loss(current_price, 'Hold')
        expected_hold = 100.0 * (1 - 0.015)
        assert stop_hold == expected_hold, f"Hold stop loss should be {expected_hold}, got {stop_hold}"
        
        # Test Sell stop loss (4% gain - for bearish positions)
        stop_sell = self.engine._calculate_stop_loss(current_price, 'Sell')
        expected_sell = 100.0 * (1 + 0.04)
        assert stop_sell == expected_sell, f"Sell stop loss should be {expected_sell}, got {stop_sell}"
        
        # Test Strong Sell stop loss (6% gain)
        stop_strong_sell = self.engine._calculate_stop_loss(current_price, 'Strong Sell')
        expected_strong_sell = 100.0 * (1 + 0.06)
        assert stop_strong_sell == expected_strong_sell, f"Strong Sell stop loss should be {expected_strong_sell}, got {stop_strong_sell}"
    
    def test_risk_reward_ratios_integrity(self):
        """Test that risk/reward ratios are always favorable"""
        test_cases = [
            ('Strong Buy', 100.0, 20.0, 8.0),   # 20% profit, 8% loss
            ('Buy', 100.0, 10.0, 6.0),          # 10% profit, 6% loss
            ('Hold', 100.0, 2.0, 1.5),           # 2% profit, 1.5% loss
            ('Sell', 100.0, 5.0, 4.0),           # 5% profit (from current), 4% loss
            ('Strong Sell', 100.0, 20.0, 6.0)    # 20% profit (from current), 6% loss
        ]
        
        for recommendation, current_price, profit_pct, loss_pct in test_cases:
            target = self.engine._calculate_target_price(current_price, recommendation)
            stop_loss = self.engine._calculate_stop_loss(current_price, recommendation)
            
            # Calculate actual profit and loss amounts
            if recommendation in ['Sell', 'Strong Sell']:
                # For sell recommendations, profit is from current price downwards
                profit_amount = abs(current_price - target)
                loss_amount = abs(stop_loss - current_price)
            else:
                # For buy/hold recommendations, profit is upwards
                profit_amount = target - current_price
                loss_amount = current_price - stop_loss
            
            # Risk/reward ratio should be favorable (profit > risk)
            assert profit_amount > loss_amount, \
                f"Risk/reward not favorable for {recommendation}: profit=${profit_amount:.2f}, risk=${loss_amount:.2f}"
            
            # Verify percentages are correct
            expected_profit = current_price * (profit_pct / 100)
            expected_loss = current_price * (loss_pct / 100)
            
            assert abs(profit_amount - expected_profit) < 0.01, \
                f"Profit amount mismatch for {recommendation}: expected ${expected_profit:.2f}, got ${profit_amount:.2f}"
            
            assert abs(loss_amount - expected_loss) < 0.01, \
                f"Loss amount mismatch for {recommendation}: expected ${expected_loss:.2f}, got ${loss_amount:.2f}"
    
    def test_recommendation_scoring_integrity(self):
        """Test that recommendation scoring logic is consistent"""
        # Test score to recommendation mapping
        test_scores = [
            (0.8, 'Strong Buy'),
            (0.4, 'Buy'),
            (0.1, 'Hold'),
            (-0.1, 'Sell'),
            (-0.5, 'Strong Sell'),
            (0.0, 'Hold'),  # Edge case
            (1.0, 'Strong Buy'),  # Edge case
            (-1.0, 'Strong Sell')  # Edge case
        ]
        
        for score, expected_recommendation in test_scores:
            actual_recommendation = self.engine._score_to_recommendation(score)
            assert actual_recommendation == expected_recommendation, \
                f"Score {score} should give {expected_recommendation}, got {actual_recommendation}"
    
    def test_confidence_calculation_integrity(self):
        """Test confidence level calculation"""
        # Test high confidence (strong score)
        confidence_high = self.engine._calculate_confidence(0.8, self.sample_df)
        assert confidence_high in ['High', 'Medium'], f"High score should give High/Medium confidence, got {confidence_high}"
        
        # Test low confidence (weak score)
        confidence_low = self.engine._calculate_confidence(0.05, self.sample_df)
        assert confidence_low in ['Low', 'Medium'], f"Low score should give Low/Medium confidence, got {confidence_low}"
        
        # Test negative confidence (sell signal)
        confidence_negative = self.engine._calculate_confidence(-0.3, self.sample_df)
        assert confidence_negative in ['Low', 'Medium'], f"Negative score should give Low/Medium confidence, got {confidence_negative}"
    
    def test_batch_recommendations_structure(self):
        """Test that batch recommendations return proper structure"""
        # Create sample data dictionary
        data_dict = {'AAPL': self.sample_df}
        
        recommendations = self.engine.batch_recommendations(data_dict)
        
        # Should return list of recommendations
        assert isinstance(recommendations, list), "Batch recommendations should return a list"
        assert len(recommendations) > 0, "Should return at least one recommendation"
        
        # Check structure of first recommendation
        rec = recommendations[0]
        required_fields = [
            'symbol', 'company', 'price', 'change_pct', 'recommendation',
            'score', 'target_price', 'stop_loss', 'confidence_level',
            'technical_indicators', 'reasoning', 'timestamp'
        ]
        
        for field in required_fields:
            assert field in rec, f"Recommendation missing required field: {field}"
        
        # Verify data types
        assert isinstance(rec['symbol'], str), "Symbol should be string"
        assert isinstance(rec['price'], (int, float)), "Price should be numeric"
        assert isinstance(rec['target_price'], (int, float)), "Target price should be numeric"
        assert isinstance(rec['stop_loss'], (int, float)), "Stop loss should be numeric"
        assert rec['recommendation'] in ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell'], \
            f"Invalid recommendation: {rec['recommendation']}"
    
    def test_empty_recommendation_structure(self):
        """Test that empty recommendations have proper structure"""
        empty_rec = self.engine._empty_recommendation('TEST')
        
        required_fields = [
            'symbol', 'recommendation', 'score', 'confidence_level',
            'reasoning', 'timestamp', 'detailed_analysis'
        ]
        
        for field in required_fields:
            assert field in empty_rec, f"Empty recommendation missing field: {field}"
        
        assert empty_rec['symbol'] == 'TEST', "Empty recommendation should preserve symbol"
        assert empty_rec['recommendation'] == 'Hold', "Empty recommendation should be Hold"
        assert empty_rec['score'] == 0.0, "Empty recommendation should have 0 score"
        assert empty_rec['confidence_level'] == 'Low', "Empty recommendation should have Low confidence"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
