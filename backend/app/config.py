"""
Configuration settings for the Stock Recommendation Engine
"""

import os
from typing import List


# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', '7h-stock-analyzer')

# Pushover Configuration
PUSHOVER_TOKEN = os.getenv('PUSHOVER_TOKEN', '')
PUSHOVER_USER = os.getenv('PUSHOVER_USER', '')

# Analysis Configuration
DEFAULT_PERIOD = os.getenv('DEFAULT_PERIOD', '6mo')
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '50'))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))

# Stock Symbols Configuration
def load_symbols_from_config() -> List[str]:
    """Load stock symbols from configuration files"""
    symbols = []
    
    # Try to load from portfolio config first
    config_files = [
        'input/config_portfolio.txt',
        'input/config_watchlist.txt',
        'input/config_us_stocks.txt',
        'input/config_etfs.txt'
    ]
    
    for config_file in config_files:
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('//'):
                            symbols.append(line.upper().strip())
                print(f"Loaded {len([s for s in symbols if s])} symbols from {config_file}")
                break  # Use first available config file
        except Exception as e:
            print(f"Error loading {config_file}: {e}")
            continue
    
    # Fallback symbols if no config files found
    if not symbols:
        symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 
            'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'BAC', 'XOM', 'PFE', 'CSCO', 'ADBE'
        ]
        print("Using fallback symbol list")
    
    return symbols

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
ENABLE_DEBUG_LOGGING = LOG_LEVEL.upper() == 'DEBUG'
ENABLE_VERBOSE_LOGGING = os.getenv('ENABLE_VERBOSE_LOGGING', 'false').lower() == 'true'
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')

# Cost-optimized logging settings
# AWS Lambda defaults to WARNING level, localhost defaults to INFO
DEFAULT_LOG_LEVEL = 'WARNING' if os.getenv('AWS_LAMBDA_FUNCTION_NAME') else 'INFO'
LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '7'))
ENABLE_STRUCTURED_LOGGING = os.getenv('ENABLE_STRUCTURED_LOGGING', 'true').lower() == 'true'

# API Configuration
API_TITLE = "Stock Recommendation Engine"
API_VERSION = "1.0.0"
API_DESCRIPTION = "Serverless stock analysis API"

# S3 Configuration
S3_DATA_PREFIX = 'data'
S3_LATEST_KEY = f'{S3_DATA_PREFIX}/latest.json'
S3_DAILY_PREFIX = f'{S3_DATA_PREFIX}/daily'

# Notification Configuration
ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'true').lower() == 'true'
NOTIFICATION_PRIORITY_THRESHOLD = int(os.getenv('NOTIFICATION_PRIORITY_THRESHOLD', '3'))

# Performance Configuration
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '10'))

# Environment Detection
IS_LAMBDA = os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None
IS_LOCAL = not IS_LAMBDA

# Cache Configuration (for future use)
ENABLE_CACHE = os.getenv('ENABLE_CACHE', 'false').lower() == 'true'
CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))  # 5 minutes

# Security Configuration
ENABLE_CORS = os.getenv('ENABLE_CORS', 'true').lower() == 'true'
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')

# Rate Limiting (for future use)
ENABLE_RATE_LIMITING = os.getenv('ENABLE_RATE_LIMITING', 'false').lower() == 'true'
RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))

# Feature Flags
ENABLE_ADVANCED_ANALYSIS = os.getenv('ENABLE_ADVANCED_ANALYSIS', 'true').lower() == 'true'
ENABLE_FUNDAMENTAL_ANALYSIS = os.getenv('ENABLE_FUNDAMENTAL_ANALYSIS', 'true').lower() == 'true'
ENABLE_PATTERN_RECOGNITION = os.getenv('ENABLE_PATTERN_RECOGNITION', 'false').lower() == 'true'
