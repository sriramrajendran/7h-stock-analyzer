"""
Pushover notification service
"""

import requests
import os
from typing import List, Dict, Any
from datetime import datetime
import logging
from app.models import Recommendation

logger = logging.getLogger(__name__)

# Configuration
PUSHOVER_TOKEN = os.getenv('PUSHOVER_TOKEN')
PUSHOVER_USER = os.getenv('PUSHOVER_USER')
PUSHOVER_API_URL = 'https://api.pushover.net/1/messages.json'


def send_push_notification(recommendations: List[Recommendation]) -> bool:
    """
    Send enhanced Pushover notification with recommendation summary
    
    Args:
        recommendations: List of enhanced stock recommendations
        
    Returns:
        bool: True if notification sent successfully
    """
    if not PUSHOVER_TOKEN or not PUSHOVER_USER:
        logger.warning("Pushover credentials not configured, skipping notification")
        return True  # Don't fail the process if notifications aren't configured
    
    try:
        # Prepare enhanced message
        message = build_enhanced_notification_message(recommendations)
        
        # Send notification
        data = {
            'token': PUSHOVER_TOKEN,
            'user': PUSHOVER_USER,
            'message': message['text'],
            'title': message['title'],
            'priority': message.get('priority', 0),
            'sound': message.get('sound', 'pushover')
        }
        
        # Add URL if there are recommendations
        if recommendations:
            data['url'] = f"https://{os.getenv('S3_BUCKET_NAME', 'stock-ui')}.s3-website-{os.getenv('AWS_REGION', 'us-east-1')}.amazonaws.com"
            data['url_title'] = "View Dashboard"
        
        response = requests.post(PUSHOVER_API_URL, data=data, timeout=10)
        
        if response.status_code == 200:
            logger.info("Pushover notification sent successfully")
            return True
        else:
            logger.error(f"Failed to send Pushover notification: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error sending Pushover notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending Pushover notification: {e}")
        return False


def build_enhanced_notification_message(recommendations: List[Recommendation]) -> Dict[str, Any]:
    """
    Build enhanced notification message content with target prices and confidence levels
    
    Args:
        recommendations: List of enhanced stock recommendations (can be objects or dicts)
        
    Returns:
        Dict with title, text, priority, and sound
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    if not recommendations:
        return {
            'title': 'Stock Analysis Complete',
            'text': f'No significant recommendations found as of {timestamp}',
            'priority': -1,  # Low priority
            'sound': 'none'
        }
    
    # Handle both Recommendation objects and dictionaries
    significant_recs = []
    for r in recommendations:
        if hasattr(r, 'recommendation'):
            # It's a Recommendation object
            if r.recommendation in ['Strong Buy', 'Buy']:
                significant_recs.append(r)
        elif isinstance(r, dict):
            # It's a dictionary
            if r.get('recommendation') in ['Strong Buy', 'Buy']:
                significant_recs.append(r)
    
    if not significant_recs:
        return {
            'title': 'Stock Analysis Complete',
            'text': f'No BUY recommendations found as of {timestamp}',
            'priority': -1,
            'sound': 'none'
        }
    
    count = len(significant_recs)
    top_3 = significant_recs[:3]
    
    # Format top recommendations with enhanced data
    top_stocks = []
    for rec in top_3:
        if hasattr(rec, 'symbol'):
            # Recommendation object
            symbol = rec.symbol
            price = rec.price
            change = rec.change_pct
            confidence = getattr(rec, 'confidence_level', 'Medium')
            target_price = getattr(rec, 'target_price', None)
        else:
            # Dictionary
            symbol = rec.get('symbol', 'N/A')
            price = rec.get('price', 0)
            change = rec.get('change_pct', 0)
            confidence = rec.get('confidence_level', 'Medium')
            target_price = rec.get('target_price')
        
        change_str = f"+{change:.1f}%" if change > 0 else f"{change:.1f}%"
        target_str = f" (Target: ${target_price:.2f})" if target_price else ""
        
        top_stocks.append(f"{symbol} ${price:.2f} ({change_str}) [{confidence}]{target_str}")
    
    # Build enhanced message
    if count == 1:
        text = f"Found 1 BUY recommendation:\n{top_stocks[0]}"
    elif count <= 3:
        text = f"Found {count} BUY recommendations:\n" + "\n".join(top_stocks)
    else:
        text = (f"Found {count} BUY recommendations as of {timestamp}\n\n"
                f"Top picks:\n" + "\n".join(top_stocks) + 
                f"\n\n... and {count - 3} more")
    
    # Determine priority based on count and confidence levels
    priority = 0
    sound = 'pushover'
    
    # High confidence recommendations
    high_confidence_count = 0
    for rec in significant_recs:
        conf = getattr(rec, 'confidence_level', 'Medium') if hasattr(rec, 'confidence_level') else rec.get('confidence_level', 'Medium')
        if conf == 'High':
            high_confidence_count += 1
    
    if count >= 5 or high_confidence_count >= 3:
        priority = 1  # High priority
        sound = 'spacealarm'
    elif count >= 3 or high_confidence_count >= 1:
        priority = 0  # Normal priority
        sound = 'pushover'
    else:
        priority = -1  # Low priority
        sound = 'none'
    
    # Check for exceptional scores
    if significant_recs and hasattr(significant_recs[0], 'score'):
        if significant_recs[0].score >= 0.8:
            priority = 1
            sound = 'spacealarm'
    elif significant_recs and isinstance(significant_recs[0], dict):
        if significant_recs[0].get('score', 0) >= 0.8:
            priority = 1
            sound = 'spacealarm'
    
    return {
        'title': f'Stock Analysis: {count} BUY Recommendations',
        'text': text,
        'priority': priority,
        'sound': sound
    }


def build_notification_message(recommendations: List[Dict]) -> Dict:
    """
    Build notification message content
    
    Args:
        recommendations: List of stock recommendations
        
    Returns:
        Dict with title, text, priority, and sound
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    if not recommendations:
        return {
            'title': 'Stock Analysis Complete',
            'text': f'No BUY recommendations found as of {timestamp}',
            'priority': -1,  # Low priority
            'sound': 'none'
        }
    
    # Build summary message
    count = len(recommendations)
    top_3 = recommendations[:3]
    
    # Format top recommendations
    top_stocks = []
    for rec in top_3:
        symbol = rec.get('symbol', 'N/A')
        price = rec.get('price', 0)
        change = rec.get('change_pct', 0)
        score = rec.get('score', 0)
        
        change_str = f"+{change:.1f}%" if change > 0 else f"{change:.1f}%"
        top_stocks.append(f"{symbol} ${price:.2f} ({change_str}) [Score: {score}]")
    
    # Build message
    if count == 1:
        text = f"Found 1 BUY recommendation:\n{top_stocks[0]}"
    elif count <= 3:
        text = f"Found {count} BUY recommendations:\n" + "\n".join(top_stocks)
    else:
        text = (f"Found {count} BUY recommendations as of {timestamp}\n\n"
                f"Top picks:\n" + "\n".join(top_stocks) + 
                f"\n\n... and {count - 3} more")
    
    # Determine priority based on count and scores
    priority = 0
    sound = 'pushover'
    
    if count >= 5:
        priority = 1  # High priority
        sound = 'spacealarm'
    elif count >= 3:
        priority = 0  # Normal priority
        sound = 'pushover'
    else:
        priority = -1  # Low priority
        sound = 'none'
    
    # Check for exceptional scores
    if recommendations and recommendations[0].get('score', 0) >= 5:
        priority = 1
        sound = 'spacealarm'
    
    return {
        'title': f'Stock Analysis: {count} BUY Recommendations',
        'text': text,
        'priority': priority,
        'sound': sound
    }


def send_target_alert(recommendation: Recommendation, current_price: float) -> bool:
    """
    Send alert when target price is reached
    
    Args:
        recommendation: Original recommendation
        current_price: Current market price
        
    Returns:
        bool: True if notification sent successfully
    """
    if not PUSHOVER_TOKEN or not PUSHOVER_USER:
        logger.warning("Pushover credentials not configured, skipping target alert")
        return True
    
    try:
        days_to_target = (datetime.utcnow() - datetime.fromisoformat(recommendation.timestamp.replace('Z', '+00:00'))).days
        
        message = (f"Target reached for {recommendation.symbol}!\n"
                   f"Target: ${recommendation.target_price:.2f}\n"
                   f"Current: ${current_price:.2f}\n"
                   f"Days to target: {days_to_target}\n"
                   f"Original recommendation: {recommendation.recommendation}")
        
        data = {
            'token': PUSHOVER_TOKEN,
            'user': PUSHOVER_USER,
            'message': message,
            'title': f'Target Reached: {recommendation.symbol}',
            'priority': 1,  # High priority
            'sound': 'cashregister',
            'url': f"https://{os.getenv('S3_BUCKET_NAME', 'stock-ui')}.s3-website-{os.getenv('AWS_REGION', 'us-east-1')}.amazonaws.com",
            'url_title': 'View Dashboard'
        }
        
        response = requests.post(PUSHOVER_API_URL, data=data, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Target alert sent for {recommendation.symbol}")
            return True
        else:
            logger.error(f"Failed to send target alert: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending target alert: {e}")
        return False


def send_stop_loss_alert(recommendation: Recommendation, current_price: float) -> bool:
    """
    Send alert when stop loss is hit
    
    Args:
        recommendation: Original recommendation
        current_price: Current market price
        
    Returns:
        bool: True if notification sent successfully
    """
    if not PUSHOVER_TOKEN or not PUSHOVER_USER:
        logger.warning("Pushover credentials not configured, skipping stop loss alert")
        return True
    
    try:
        days_to_stop = (datetime.utcnow() - datetime.fromisoformat(recommendation.timestamp.replace('Z', '+00:00'))).days
        
        message = (f"Stop loss hit for {recommendation.symbol}!\n"
                   f"Stop loss: ${recommendation.stop_loss:.2f}\n"
                   f"Current: ${current_price:.2f}\n"
                   f"Days held: {days_to_stop}\n"
                   f"Original recommendation: {recommendation.recommendation}")
        
        data = {
            'token': PUSHOVER_TOKEN,
            'user': PUSHOVER_USER,
            'message': message,
            'title': f'Stop Loss Hit: {recommendation.symbol}',
            'priority': 1,  # High priority
            'sound': 'siren',
            'url': f"https://{os.getenv('S3_BUCKET_NAME', 'stock-ui')}.s3-website-{os.getenv('AWS_REGION', 'us-east-1')}.amazonaws.com",
            'url_title': 'View Dashboard'
        }
        
        response = requests.post(PUSHOVER_API_URL, data=data, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Stop loss alert sent for {recommendation.symbol}")
            return True
        else:
            logger.error(f"Failed to send stop loss alert: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending stop loss alert: {e}")
        return False


def send_test_notification() -> bool:
    """Send a test notification to verify Pushover configuration"""
    if not PUSHOVER_TOKEN or not PUSHOVER_USER:
        print("Pushover credentials not configured")
        return False
    
    try:
        data = {
            'token': PUSHOVER_TOKEN,
            'user': PUSHOVER_USER,
            'message': 'Test notification from Stock Analyzer',
            'title': 'Test Notification',
            'priority': 0,
            'sound': 'pushover'
        }
        
        response = requests.post(PUSHOVER_API_URL, data=data, timeout=10)
        
        if response.status_code == 200:
            print("Test notification sent successfully")
            return True
        else:
            print(f"Failed to send test notification: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error sending test notification: {e}")
        return False


def send_error_notification(error_message: str) -> bool:
    """
    Send error notification
    
    Args:
        error_message: Error message to send
        
    Returns:
        bool: True if notification sent successfully
    """
    if not PUSHOVER_TOKEN or not PUSHOVER_USER:
        print("Pushover credentials not configured, skipping error notification")
        return True
    
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        data = {
            'token': PUSHOVER_TOKEN,
            'user': PUSHOVER_USER,
            'message': f"Error at {timestamp}:\n{error_message}",
            'title': 'Stock Analyzer Error',
            'priority': 1,  # High priority for errors
            'sound': 'siren'
        }
        
        response = requests.post(PUSHOVER_API_URL, data=data, timeout=10)
        
        if response.status_code == 200:
            print("Error notification sent successfully")
            return True
        else:
            print(f"Failed to send error notification: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error sending error notification: {e}")
        return False


def validate_pushover_config() -> Dict[str, bool]:
    """
    Validate Pushover configuration
    
    Returns:
        Dict with validation results
    """
    results = {
        'token_configured': bool(PUSHOVER_TOKEN),
        'user_configured': bool(PUSHOVER_USER),
        'test_sent': False,
        'test_successful': False
    }
    
    if results['token_configured'] and results['user_configured']:
        results['test_sent'] = True
        results['test_successful'] = send_test_notification()
    
    return results


def get_notification_stats(recommendations: List[Recommendation]) -> Dict[str, Any]:
    """
    Get notification statistics for recommendations
    
    Args:
        recommendations: List of recommendations
        
    Returns:
        Dict with notification statistics
    """
    if not recommendations:
        return {'total': 0, 'significant': 0, 'high_confidence': 0}
    
    significant_recs = [r for r in recommendations if r.recommendation in ['Strong Buy', 'Buy']]
    high_confidence_recs = [r for r in significant_recs if r.confidence_level == 'High']
    
    return {
        'total': len(recommendations),
        'significant': len(significant_recs),
        'high_confidence': len(high_confidence_recs),
        'will_notify': len(significant_recs) > 0,
        'priority': 'high' if len(significant_recs) >= 5 or len(high_confidence_recs) >= 3 else 'normal' if len(significant_recs) >= 3 else 'low'
    }
