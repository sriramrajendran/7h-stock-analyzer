"""
Configuration management service for updating stock lists
"""

import os
import boto3
from typing import List, Dict, Any
from botocore.exceptions import ClientError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Configuration
BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'stock-analyzer-local')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Initialize S3 client
s3_client = boto3.client('s3')

# Config file mappings
CONFIG_FILES = {
    'portfolio': 'input/config_portfolio.txt',
    'watchlist': 'input/config_watchlist.txt',
    'us_stocks': 'input/config_us_stocks.txt',
    'etfs': 'input/config_etfs.txt'
}


def load_config_from_s3(config_type: str) -> Dict[str, Any]:
    """
    Load configuration from S3 with enhanced error handling
    
    Args:
        config_type: Type of config ('portfolio', 'watchlist', 'us_stocks', 'etfs')
        
    Returns:
        Dict with success status and symbols list
    """
    try:
        if config_type not in CONFIG_FILES:
            return {'success': False, 'error': f'Invalid config type: {config_type}'}
        
        config_file = CONFIG_FILES[config_type]
        key = f'config/{config_file}'
        
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
            content = response['Body'].read().decode('utf-8')
            
            symbols = []
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('//'):
                    symbols.append(line.upper().strip())
            
            return {
                'success': True,
                'config_type': config_type,
                'symbols': symbols,
                'count': len(symbols),
                'source': 's3',
                'last_modified': response['LastModified'].isoformat()
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                # Config doesn't exist in S3, try local file
                return load_config_from_local(config_type)
            else:
                logger.error(f"S3 error loading config: {str(e)}")
                return {'success': False, 'error': f'S3 error: {str(e)}'}
                
    except Exception as e:
        logger.error(f"Error loading config from S3: {str(e)}")
        # Fallback to local config on any error
        return load_config_from_local(config_type)


def load_config_from_local(config_type: str) -> Dict[str, Any]:
    """
    Load configuration from local file
    
    Args:
        config_type: Type of config ('portfolio', 'watchlist', 'us_stocks', 'etfs')
        
    Returns:
        Dict with success status and symbols list
    """
    try:
        if config_type not in CONFIG_FILES:
            return {'success': False, 'error': f'Invalid config type: {config_type}'}
        
        config_file = CONFIG_FILES[config_type]
        
        if not os.path.exists(config_file):
            return {'success': False, 'error': f'Config file not found: {config_file}'}
        
        symbols = []
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('//'):
                    symbols.append(line.upper().strip())
        
        return {
            'success': True,
            'config_type': config_type,
            'symbols': symbols,
            'count': len(symbols)
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Error loading local config: {str(e)}'}


def update_config_in_s3(config_type: str, symbols: List[str], backup: bool = True) -> Dict[str, Any]:
    """
    Update configuration in S3 with enhanced security and validation
    
    Args:
        config_type: Type of config to update
        symbols: List of stock symbols
        backup: Whether to backup existing config
        
    Returns:
        Dict with success status
    """
    try:
        if config_type not in CONFIG_FILES:
            return {'success': False, 'error': f'Invalid config type: {config_type}'}
        
        # Validate symbols before updating
        validation_result = validate_symbols(symbols)
        if not validation_result['success']:
            return {'success': False, 'error': 'Symbol validation failed'}
        
        config_file = CONFIG_FILES[config_type]
        key = f'config/{config_file}'
        
        # Backup existing config if requested
        if backup:
            backup_result = backup_config_in_s3(config_type)
            if not backup_result['success']:
                logger.warning(f"Failed to backup config: {backup_result['error']}")
        
        # Prepare new config content
        content = "# Stock Configuration\n"
        content += f"# Updated: {datetime.utcnow().isoformat()}\n"
        content += "# Format: One symbol per line\n"
        content += "# Lines starting with # are ignored\n\n"
        
        # Add only valid symbols
        valid_symbols = validation_result['valid_symbols']
        for symbol in valid_symbols:
            content += f"{symbol}\n"
        
        # Upload to S3 with encryption
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=content,
            ContentType='text/plain',
            ServerSideEncryption='AES256'
        )
        
        logger.info(f"Successfully updated {config_type} configuration with {len(valid_symbols)} symbols")
        
        return {
            'success': True,
            'config_type': config_type,
            'symbols_count': len(valid_symbols),
            'valid_symbols': valid_symbols,
            'invalid_symbols': validation_result['invalid_symbols'],
            'message': f'Successfully updated {config_type} configuration'
        }
        
    except Exception as e:
        logger.error(f"Error updating config in S3: {str(e)}")
        # Fallback to local config on any error
        return save_config_to_local(config_type, symbols)


def backup_config_in_s3(config_type: str) -> Dict[str, Any]:
    """
    Backup existing configuration in S3 with encryption
    
    Args:
        config_type: Type of config to backup
        
    Returns:
        Dict with success status
    """
    try:
        if config_type not in CONFIG_FILES:
            return {'success': False, 'error': f'Invalid config type: {config_type}'}
        
        config_file = CONFIG_FILES[config_type]
        key = f'config/{config_file}'
        
        # Check if config exists
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
            content = response['Body'].read()
            
            # Create backup with timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_key = f'config/backups/{config_type}_{timestamp}.txt'
            
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=backup_key,
                Body=content,
                ContentType='text/plain',
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Successfully backed up {config_type} config to {backup_key}")
            
            return {
                'success': True,
                'backup_key': backup_key,
                'message': f'Successfully backed up {config_type} config'
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {'success': True, 'message': 'No existing config to backup'}
            else:
                logger.error(f"S3 error backing up config: {str(e)}")
                return {'success': False, 'error': f'S3 error: {str(e)}'}
                
    except Exception as e:
        logger.error(f"Error backing up config: {str(e)}")
        return {'success': False, 'error': f'Error backing up config: {str(e)}'}


def get_all_configs() -> Dict[str, Any]:
    """
    Get all configurations with metadata
    
    Returns:
        Dict with all config types and their symbols
    """
    configs = {}
    total_symbols = 0
    
    for config_type in CONFIG_FILES.keys():
        result = load_config_from_s3(config_type)
        configs[config_type] = result
        if result['success']:
            total_symbols += result['count']
    
    return {
        'success': True,
        'configs': configs,
        'available_types': list(CONFIG_FILES.keys()),
        'total_symbols': total_symbols,
        'timestamp': datetime.utcnow().isoformat()
    }


def validate_symbols(symbols: List[str]) -> Dict[str, Any]:
    """
    Validate stock symbols with enhanced error handling
    
    Args:
        symbols: List of symbols to validate
        
    Returns:
        Dict with validation results
    """
    try:
        import yfinance as yf
        
        valid_symbols = []
        invalid_symbols = []
        
        # Test each symbol
        for symbol in symbols:
            symbol = symbol.upper().strip()
            if not symbol:
                continue
                
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Check if we got valid data
                if info and ('symbol' in info or 'shortName' in info):
                    valid_symbols.append(symbol)
                else:
                    invalid_symbols.append(symbol)
                    
            except Exception as e:
                logger.debug(f"Invalid symbol {symbol}: {str(e)}")
                invalid_symbols.append(symbol)
        
        return {
            'success': True,
            'valid_symbols': valid_symbols,
            'invalid_symbols': invalid_symbols,
            'valid_count': len(valid_symbols),
            'invalid_count': len(invalid_symbols),
            'total_count': len(symbols)
        }
        
    except Exception as e:
        logger.error(f"Symbol validation failed: {str(e)}")
        return {
            'success': False,
            'error': f'Validation service unavailable: {str(e)}',
            'valid_symbols': [],
            'invalid_symbols': symbols,
            'valid_count': 0,
            'invalid_count': len(symbols),
            'total_count': len(symbols)
        }


def sync_configs_to_local() -> Dict[str, Any]:
    """
    Sync all configurations from S3 to local files
    
    Returns:
        Dict with sync results
    """
    try:
        results = {}
        synced_count = 0
        
        for config_type in CONFIG_FILES.keys():
            # Load from S3
            s3_result = load_config_from_s3(config_type)
            
            if s3_result['success']:
                # Write to local file
                config_file = CONFIG_FILES[config_type]
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                
                # Prepare content
                content = "# Stock Configuration\n"
                content += f"# Synced from S3: {datetime.utcnow().isoformat()}\n"
                content += "# Format: One symbol per line\n"
                content += "# Lines starting with # are ignored\n\n"
                
                for symbol in s3_result['symbols']:
                    content += f"{symbol}\n"
                
                # Write to local file
                with open(config_file, 'w') as f:
                    f.write(content)
                
                results[config_type] = {
                    'success': True,
                    'symbols_count': s3_result['count'],
                    'local_file': config_file,
                    'source': s3_result.get('source', 's3')
                }
                synced_count += 1
            else:
                results[config_type] = {
                    'success': False,
                    'error': s3_result['error']
                }
        
        logger.info(f"Synced {synced_count} configurations from S3 to local files")
        
        return {
            'success': True,
            'synced_count': synced_count,
            'total_count': len(CONFIG_FILES),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Sync error: {str(e)}")
        return {
            'success': False,
            'error': f'Sync error: {str(e)}'
        }


def save_config_to_local(config_type: str, symbols: List[str]) -> Dict[str, Any]:
    """
    Save configuration to local file
    
    Args:
        config_type: Type of config to save
        symbols: List of stock symbols
        
    Returns:
        Dict with success status
    """
    try:
        if config_type not in CONFIG_FILES:
            return {'success': False, 'error': f'Invalid config type: {config_type}'}
        
        config_file = CONFIG_FILES[config_type]
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # Prepare content
        content = "# Stock Configuration\n"
        content += f"# Updated: {datetime.utcnow().isoformat()}\n"
        content += "# Format: One symbol per line\n"
        content += "# Lines starting with # are ignored\n\n"
        
        for symbol in symbols:
            symbol = symbol.upper().strip()
            if symbol and len(symbol) > 0:
                content += f"{symbol}\n"
        
        # Write to local file
        with open(config_file, 'w') as f:
            f.write(content)
        
        return {
            'success': True,
            'config_type': config_type,
            'symbols_count': len(symbols),
            'local_file': config_file
        }
        
    except Exception as e:
        logger.error(f"Error saving local config: {str(e)}")
        return {'success': False, 'error': f'Error saving local config: {str(e)}'}


def get_config_history(config_type: str, limit: int = 10) -> Dict[str, Any]:
    """
    Get configuration backup history from S3
    
    Args:
        config_type: Type of config
        limit: Maximum number of backups to return
        
    Returns:
        Dict with backup history
    """
    try:
        if config_type not in CONFIG_FILES:
            return {'success': False, 'error': f'Invalid config type: {config_type}'}
        
        prefix = f'config/backups/{config_type}_'
        backups = []
        
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
            for obj in page.get('Contents', []):
                key = obj['Key']
                last_modified = obj['LastModified']
                size = obj['Size']
                
                # Extract timestamp from filename
                timestamp_str = key.split('_')[-1].replace('.txt', '')
                
                backups.append({
                    'key': key,
                    'timestamp': timestamp_str,
                    'last_modified': last_modified.isoformat(),
                    'size': size
                })
        
        # Sort by timestamp (newest first) and limit
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        backups = backups[:limit]
        
        return {
            'success': True,
            'config_type': config_type,
            'backups': backups,
            'count': len(backups)
        }
        
    except Exception as e:
        logger.error(f"Error getting config history: {str(e)}")
        return {'success': False, 'error': f'Error getting config history: {str(e)}'}
