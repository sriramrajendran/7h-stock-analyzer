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
# For local development, use dev bucket; for AWS, use production bucket
if os.getenv('ENVIRONMENT') == 'production':
    BUCKET_NAME = os.getenv('S3_BUCKET_NAME_PROD', '7h-stock-analyzer')
else:
    BUCKET_NAME = os.getenv('S3_BUCKET_NAME_LOCAL', os.getenv('S3_BUCKET_NAME', '7h-stock-analyzer-dev'))

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Initialize S3 client
s3_client = boto3.client('s3')

# Config file mapping - single consolidated file
CONFIG_FILE = 'config.json'


def load_config_from_s3(config_type: str) -> Dict[str, Any]:
    """
    Load configuration from consolidated JSON file in S3
    
    Args:
        config_type: Type of config ('portfolio', 'watchlist', 'us_stocks', 'etfs')
        
    Returns:
        Dict with success status and symbols list
    """
    try:
        # Validate config type
        valid_types = ['portfolio', 'watchlist', 'us_stocks', 'etfs']
        if config_type not in valid_types:
            return {'success': False, 'error': f'Invalid config type: {config_type}'}
        
        key = CONFIG_FILE
        
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
            content = response['Body'].read().decode('utf-8')
            
            # Parse JSON content
            import json
            config_data = json.loads(content)
            
            # Validate JSON structure
            if not isinstance(config_data, dict) or 'configurations' not in config_data:
                return {'success': False, 'error': 'Invalid JSON configuration format'}
            
            configurations = config_data.get('configurations', {})
            if config_type not in configurations:
                return {'success': False, 'error': f'Configuration type {config_type} not found in consolidated config'}
            
            category_config = configurations[config_type]
            if not isinstance(category_config, dict) or 'symbols' not in category_config:
                return {'success': False, 'error': f'Invalid configuration structure for {config_type}'}
            
            symbols = category_config.get('symbols', [])
            if not isinstance(symbols, list):
                return {'success': False, 'error': f'Symbols must be a list for {config_type}'}
            
            # Clean up symbols (remove empty strings, convert to uppercase)
            clean_symbols = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
            
            return {
                'success': True,
                'config_type': config_type,
                'symbols': clean_symbols,
                'count': len(clean_symbols),
                'name': category_config.get('name', config_type.title()),
                'description': category_config.get('description', ''),
                'source': 's3',
                'last_modified': response['LastModified'].isoformat(),
                'config_last_updated': config_data.get('last_updated', '')
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {'success': False, 'error': f'Configuration file {key} not found in S3'}
            elif e.response['Error']['Code'] == 'NoSuchBucket':
                return {'success': False, 'error': f'S3 bucket {BUCKET_NAME} not found'}
            else:
                logger.warning(f"S3 error loading config: {str(e)}")
                return {'success': False, 'error': f'S3 error: {str(e)}'}
        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'Invalid JSON in configuration file: {str(e)}'}
                
    except Exception as e:
        logger.error(f"Error loading config from S3: {str(e)}")
        return {'success': False, 'error': f'Failed to load configuration: {str(e)}'}


def load_config_from_local(config_type: str) -> Dict[str, Any]:
    """
    Load configuration from local consolidated JSON file
    
    Args:
        config_type: Type of config ('portfolio', 'watchlist', 'us_stocks', 'etfs')
        
    Returns:
        Dict with success status and symbols list
    """
    try:
        # Validate config type
        valid_types = ['portfolio', 'watchlist', 'us_stocks', 'etfs']
        if config_type not in valid_types:
            return {'success': False, 'error': f'Invalid config type: {config_type}'}
        
        config_file = CONFIG_FILE
        
        if not os.path.exists(config_file):
            return {'success': False, 'error': f'Configuration file {config_file} not found'}
        
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Parse JSON content
        import json
        config_data = json.loads(content)
        
        # Validate JSON structure
        if not isinstance(config_data, dict) or 'configurations' not in config_data:
            return {'success': False, 'error': 'Invalid JSON configuration format'}
        
        configurations = config_data.get('configurations', {})
        if config_type not in configurations:
            return {'success': False, 'error': f'Configuration type {config_type} not found in consolidated config'}
        
        category_config = configurations[config_type]
        if not isinstance(category_config, dict) or 'symbols' not in category_config:
            return {'success': False, 'error': f'Invalid configuration structure for {config_type}'}
        
        symbols = category_config.get('symbols', [])
        if not isinstance(symbols, list):
            return {'success': False, 'error': f'Symbols must be a list for {config_type}'}
        
        # Clean up symbols (remove empty strings, convert to uppercase)
        clean_symbols = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
        
        return {
            'success': True,
            'config_type': config_type,
            'symbols': clean_symbols,
            'count': len(clean_symbols),
            'name': category_config.get('name', config_type.title()),
            'description': category_config.get('description', ''),
            'source': 'local',
            'config_last_updated': config_data.get('last_updated', '')
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Error loading local config: {str(e)}'}


def update_config_in_s3(config_type: str, symbols: List[str], backup: bool = True) -> Dict[str, Any]:
    """
    Update configuration in consolidated S3 JSON file
    
    Args:
        config_type: Type of config to update
        symbols: List of stock symbols
        backup: Whether to backup existing config
        
    Returns:
        Dict with success status
    """
    try:
        # Validate config type
        valid_types = ['portfolio', 'watchlist', 'us_stocks', 'etfs']
        if config_type not in valid_types:
            return {'success': False, 'error': f'Invalid config type: {config_type}'}
        
        # Validate symbols before updating
        validation_result = validate_symbols(symbols)
        if not validation_result['success']:
            return {'success': False, 'error': 'Symbol validation failed'}
        
        key = CONFIG_FILE
        
        # Backup existing config if requested
        if backup:
            backup_result = backup_config_in_s3(config_type)
            if not backup_result['success']:
                logger.warning(f"Failed to backup config: {backup_result['error']}")
        
        # Load existing consolidated config
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
            existing_content = response['Body'].read().decode('utf-8')
            import json
            config_data = json.loads(existing_content)
        except:
            # Create new config if doesn't exist
            config_data = {
                'success': True,
                'last_updated': datetime.utcnow().isoformat(),
                'description': 'Consolidated stock configuration for 7H Stock Analyzer',
                'configurations': {},
                'total_symbols': 0,
                'categories': 0
            }
        
        # Update the specific configuration type
        if 'configurations' not in config_data:
            config_data['configurations'] = {}
        
        # Get valid symbols
        valid_symbols = validation_result['valid_symbols']
        
        # Update the configuration
        config_data['configurations'][config_type] = {
            'name': config_type.title().replace('_', ' '),
            'description': f'{config_type.title().replace('_', ' ')} stocks',
            'symbols': valid_symbols,
            'count': len(valid_symbols),
            'last_updated': datetime.utcnow().isoformat()
        }
        
        # Update totals
        total_symbols = sum(len(config['symbols']) for config in config_data['configurations'].values())
        config_data['total_symbols'] = total_symbols
        config_data['categories'] = len(config_data['configurations'])
        config_data['last_updated'] = datetime.utcnow().isoformat()
        
        # Upload updated config to S3
        updated_content = json.dumps(config_data, indent=2)
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=updated_content,
            ContentType='application/json',
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
    Backup existing consolidated configuration in S3
    
    Args:
        config_type: Type of config to backup
        
    Returns:
        Dict with success status
    """
    try:
        # Validate config type
        valid_types = ['portfolio', 'watchlist', 'us_stocks', 'etfs']
        if config_type not in valid_types:
            return {'success': False, 'error': f'Invalid config type: {config_type}'}
        
        key = CONFIG_FILE
        
        # Check if config exists
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
            content = response['Body'].read()
            
            # Create backup with timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_key = f'config/backups/config_{timestamp}.json'
            
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=backup_key,
                Body=content,
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Successfully backed up config to {backup_key}")
            
            return {
                'success': True,
                'backup_key': backup_key,
                'message': f'Successfully backed up consolidated config'
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {'success': True, 'message': 'No existing config to backup'}
            else:
                raise e
                
    except Exception as e:
        logger.error(f"Error backing up config: {str(e)}")
        return {'success': False, 'error': f'Failed to backup config: {str(e)}'}


def get_all_configs() -> Dict[str, Any]:
    """
    Get all configurations from consolidated JSON file
    
    Returns:
        Dict with all config types and their symbols
    """
    try:
        key = CONFIG_FILE
        
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
            content = response['Body'].read().decode('utf-8')
            
            import json
            config_data = json.loads(content)
            
            return {
                'success': True,
                'config_data': config_data,
                'configurations': config_data.get('configurations', {}),
                'total_symbols': config_data.get('total_symbols', 0),
                'categories': config_data.get('categories', 0),
                'last_updated': config_data.get('last_updated', ''),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {
                    'success': False,
                    'error': f'Configuration file {key} not found in S3'
                }
            else:
                raise e
                
    except Exception as e:
        logger.error(f"Error getting all configs: {str(e)}")
        return {'success': False, 'error': f'Failed to get configurations: {str(e)}'}


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
    Sync consolidated configuration from S3 to local JSON file
    
    Returns:
        Dict with sync results
    """
    try:
        key = CONFIG_FILE
        
        # Load from S3
        s3_result = load_config_from_s3('portfolio')  # Just to check if S3 is accessible
        
        if s3_result['success'] or 'Configuration file' not in s3_result.get('error', ''):
            # Get the full consolidated config
            try:
                response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
                content = response['Body'].read().decode('utf-8')
                
                # Write to local file
                os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
                with open(CONFIG_FILE, 'w') as f:
                    f.write(content)
                
                logger.info(f"Synced consolidated config from S3 to local file: {CONFIG_FILE}")
                
                return {
                    'success': True,
                    'local_file': CONFIG_FILE,
                    'source': 's3',
                    'message': 'Successfully synced consolidated configuration'
                }
                
            except Exception as e:
                return {'success': False, 'error': f'Failed to sync from S3: {str(e)}'}
        else:
            return {'success': False, 'error': 'S3 configuration not accessible'}
            
    except Exception as e:
        logger.error(f"Sync error: {str(e)}")
        return {
            'success': False,
            'error': f'Sync error: {str(e)}'
        }


def save_config_to_local(config_type: str, symbols: List[str]) -> Dict[str, Any]:
    """
    Save configuration to local consolidated JSON file
    
    Args:
        config_type: Type of config to save
        symbols: List of stock symbols
        
    Returns:
        Dict with success status
    """
    try:
        # Validate config type
        valid_types = ['portfolio', 'watchlist', 'us_stocks', 'etfs']
        if config_type not in valid_types:
            return {'success': False, 'error': f'Invalid config type: {config_type}'}
        
        # Load existing config or create new
        config_data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                import json
                config_data = json.load(f)
        else:
            config_data = {
                'success': True,
                'last_updated': datetime.utcnow().isoformat(),
                'description': 'Consolidated stock configuration for 7H Stock Analyzer',
                'configurations': {},
                'total_symbols': 0,
                'categories': 0
            }
        
        # Update the specific configuration
        if 'configurations' not in config_data:
            config_data['configurations'] = {}
        
        config_data['configurations'][config_type] = {
            'name': config_type.title().replace('_', ' '),
            'description': f'{config_type.title().replace('_', ' ')} stocks',
            'symbols': symbols,
            'count': len(symbols),
            'last_updated': datetime.utcnow().isoformat()
        }
        
        # Update totals
        total_symbols = sum(len(config['symbols']) for config in config_data['configurations'].values())
        config_data['total_symbols'] = total_symbols
        config_data['categories'] = len(config_data['configurations'])
        config_data['last_updated'] = datetime.utcnow().isoformat()
        
        # Write to local file
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            import json
            json.dump(config_data, f, indent=2)
        
        return {
            'success': True,
            'config_type': config_type,
            'symbols_count': len(symbols),
            'local_file': CONFIG_FILE,
            'total_symbols': total_symbols
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Failed to save local config: {str(e)}'}


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
