"""
Cost-optimized logging configuration for CloudWatch
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any

class CostOptimizedLogger:
    """Structured logger with cost optimization features"""
    
    def __init__(self, name: str = "stock-analyzer"):
        self.logger = logging.getLogger(name)
        self._setup_logger()
        
    def _setup_logger(self):
        """Configure logger with cost optimization"""
        if self.logger.handlers:
            return
            
        # Auto-detect environment and set appropriate log level
        if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
            # AWS Lambda environment - use WARNING to minimize costs
            log_level = os.getenv('LOG_LEVEL', 'WARNING').upper()
        else:
            # Local development - use INFO for better debugging
            log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
            
        self.logger.setLevel(getattr(logging, log_level))
        
        # Create cost-optimized formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    def _should_log(self, level: str) -> bool:
        """Check if message should be logged based on environment and level"""
        # In AWS Lambda, only log WARNING and above unless explicitly enabled
        if os.getenv('AWS_LAMBDA_FUNCTION_NAME') and level in ['DEBUG', 'INFO']:
            return os.getenv('ENABLE_VERBOSE_LOGGING', 'false').lower() == 'true'
        return True
        
    def _log_structured(self, level: str, message: str, **kwargs):
        """Log structured message with cost optimization"""
        if not self._should_log(level):
            return
            
        # Create structured log entry
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'environment': 'aws' if os.getenv('AWS_LAMBDA_FUNCTION_NAME') else 'local',
            'lambda_function': os.getenv('AWS_LAMBDA_FUNCTION_NAME', 'local'),
            **kwargs
        }
        
        # Log the structured message
        getattr(self.logger, level.lower())(json.dumps(log_data))
        
    def debug(self, message: str, **kwargs):
        """Debug level logging"""
        self._log_structured('DEBUG', message, **kwargs)
        
    def info(self, message: str, **kwargs):
        """Info level logging"""
        self._log_structured('INFO', message, **kwargs)
        
    def warning(self, message: str, **kwargs):
        """Warning level logging"""
        self._log_structured('WARNING', message, **kwargs)
        
    def error(self, message: str, **kwargs):
        """Error level logging"""
        self._log_structured('ERROR', message, **kwargs)
        
    def critical(self, message: str, **kwargs):
        """Critical level logging"""
        self._log_structured('CRITICAL', message, **kwargs)
        
    def log_metric(self, metric_name: str, value: float, unit: str = 'Count', **kwargs):
        """Log CloudWatch metrics efficiently"""
        self.info(f"METRIC: {metric_name}={value}{unit}", 
                 metric_name=metric_name, 
                 metric_value=value, 
                 metric_unit=unit,
                 **kwargs)
        
    def log_api_call(self, endpoint: str, method: str, status_code: int, duration_ms: float, **kwargs):
        """Log API call with cost optimization"""
        self.info(f"API: {method} {endpoint} - {status_code} ({duration_ms}ms)",
                 api_endpoint=endpoint,
                 api_method=method,
                 status_code=status_code,
                 duration_ms=duration_ms,
                 **kwargs)
        
    def log_stock_analysis(self, symbols_count: int, recommendations_count: int, duration_ms: float, **kwargs):
        """Log stock analysis metrics"""
        self.info(f"ANALYSIS: {symbols_count} symbols -> {recommendations_count} recommendations ({duration_ms}ms)",
                 symbols_analyzed=symbols_count,
                 recommendations_generated=recommendations_count,
                 analysis_duration_ms=duration_ms,
                 **kwargs)

# Global logger instance
logger = CostOptimizedLogger()

def get_logger() -> CostOptimizedLogger:
    """Get the global logger instance"""
    return logger
