"""
S3 storage service for persisting and retrieving recommendations
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError
from app.models import Recommendation
from app.logger import get_logger

logger = get_logger()

# Configuration
BUCKET_NAME = os.getenv('S3_BUCKET_NAME', '7h-stock-analyzer-dev')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Initialize S3 client
s3_client = boto3.client('s3')


def persist_results(recommendations: List[Recommendation]) -> bool:
    """
    Persist enhanced recommendations to S3
    
    Saves to both latest.json and daily/YYYY-MM-DD.json
    Includes enhanced fields like target prices, stop losses, confidence levels
    """
    try:
        timestamp = datetime.utcnow()
        date_str = timestamp.strftime('%Y-%m-%d')
        
        # Convert recommendations to dicts (they're already dicts now)
        recommendations_data = recommendations
        
        # Prepare enhanced data with metadata
        data = {
            'timestamp': timestamp.isoformat(),
            'date': date_str,
            'count': len(recommendations),
            'recommendations': recommendations_data,
            'metadata': {
                'version': '2.0',
                'enhanced_features': ['target_prices', 'stop_losses', 'confidence_levels', 'technical_indicators'],
                'generated_by': '7h-stock-analyzer-v2'
            }
        }
        
        # Save latest.json (overwrites)
        latest_key = 'data/latest.json'
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=latest_key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json',
            ServerSideEncryption='AES256'
        )
        logger.info(f"Saved latest results to s3://{BUCKET_NAME}/{latest_key}")
        
        # Save daily file (immutable)
        daily_key = f'data/daily/{date_str}.json'
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=daily_key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json',
            ServerSideEncryption='AES256'
        )
        logger.info(f"Saved daily results to s3://{BUCKET_NAME}/{daily_key}")
        
        # Update dates.json file
        update_available_dates()
        
        return True
        
    except ClientError as e:
        logger.error(f"S3 client error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error persisting results: {e}")
        return False


def persist_enhanced_historical_data(date: str, enhanced_data: Dict[str, Any]) -> bool:
    """
    Persist enhanced historical data to S3 website path for direct access
    
    Args:
        date: Date string in YYYY-MM-DD format
        enhanced_data: Enhanced historical data with reconciliation info
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Prepare enhanced historical data
        data = {
            'date': date,
            'timestamp': datetime.utcnow().isoformat(),
            'enhanced_data': enhanced_data,
            'data_type': 'enhanced_historical',
            'version': '2.0'
        }
        
        # Save to website path for direct S3 access
        enhanced_key = f'data/enhanced/{date}.json'
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=enhanced_key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json',
            ServerSideEncryption='AES256'
        )
        logger.info(f"Saved enhanced historical data to s3://{BUCKET_NAME}/{enhanced_key}")
        
        return True
        
    except ClientError as e:
        logger.error(f"S3 client error saving enhanced historical data: {e}")
        return False
    except Exception as e:
        logger.error(f"Error saving enhanced historical data: {e}")
        return False


def get_available_dates() -> List[str]:
    """Get list of available dates with historical recommendations"""
    try:
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix='data/daily/'
        )
        
        dates = []
        for obj in response.get('Contents', []):
            key = obj['Key']
            if key.endswith('.json'):
                # Extract date from key like 'data/daily/2026-02-03.json'
                date_str = key.split('/')[-1].replace('.json', '')
                dates.append(date_str)
        
        # Sort dates in descending order (newest first)
        dates.sort(reverse=True)
        return dates
        
    except ClientError as e:
        logger.error(f"S3 error listing dates: {e}")
        return []
    except Exception as e:
        logger.error(f"Error listing available dates: {e}")
        return []


def get_latest_results() -> Dict[str, Any]:
    """Get the latest recommendations from S3"""
    try:
        response = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key='data/latest.json'
        )
        
        content = response['Body'].read().decode('utf-8')
        
        # Handle empty content
        if not content.strip():
            logger.warning("Empty latest.json content found in S3")
            return {'error': 'No data available'}
        
        data = json.loads(content)
        return data
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return {'error': 'No latest results found'}
        logger.error(f"S3 client error: {e}", error=str(e), operation="get_latest_results")
        return {'error': f'S3 error: {str(e)}'}
    except Exception as e:
        logger.error(f"Error getting latest results: {e}", error=str(e), operation="get_latest_results")
        return {'error': f'Error: {str(e)}'}


def get_historical_results(date: str, include_recon: bool = False) -> Dict[str, Any]:
    """
    Get historical recommendations for a specific date
    
    Args:
        date: Date string in YYYY-MM-DD format
        include_recon: Whether to include reconciliation data
    """
    try:
        # Validate date format
        datetime.strptime(date, '%Y-%m-%d')
        
        # Get the main historical data
        response = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key=f'data/daily/{date}.json'
        )
        
        data = json.loads(response['Body'].read().decode('utf-8'))
        
        # If reconciliation data is requested, try to enhance the recommendations
        if include_recon and 'recommendations' in data:
            # Try to get reconciliation data for the same date
            try:
                recon_response = s3_client.get_object(
                    Bucket=BUCKET_NAME,
                    Key=f'recon/daily/{date}.json'
                )
                recon_data = json.loads(recon_response['Body'].read().decode('utf-8'))
                
                # Merge reconciliation data into recommendations
                recon_lookup = {r['symbol']: r for r in recon_data.get('reconciliations', [])}
                
                for rec in data['recommendations']:
                    symbol = rec.get('symbol')
                    if symbol in recon_lookup:
                        recon_info = recon_lookup[symbol]
                        rec['result_status'] = recon_info.get('result_status', 'in_transit')
                        rec['days_to_target_result'] = recon_info.get('days_to_target')
                        rec['recon_current_price'] = recon_info.get('current_price')
                        rec['recon_days_elapsed'] = recon_info.get('days_elapsed')
                        rec['target_met'] = recon_info.get('target_met', False)
                        rec['stop_loss_hit'] = recon_info.get('stop_loss_hit', False)
                    else:
                        # Default values if no recon data found
                        rec['result_status'] = 'in_transit'
                        rec['days_to_target_result'] = None
                        rec['recon_current_price'] = rec.get('price')  # Use original price
                        rec['recon_days_elapsed'] = 0
                        rec['target_met'] = False
                        rec['stop_loss_hit'] = False
                        
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    # No reconciliation data available, add default fields
                    for rec in data['recommendations']:
                        rec['result_status'] = 'in_transit'
                        rec['days_to_target_result'] = None
                        rec['recon_current_price'] = rec.get('price')
                        rec['recon_days_elapsed'] = 0
                        rec['target_met'] = False
                        rec['stop_loss_hit'] = False
                else:
                    raise
            except Exception as e:
                logger.warning(f"Error merging recon data: {e}")
                # Add default fields on error
                for rec in data['recommendations']:
                    rec['result_status'] = 'in_transit'
                    rec['days_to_target_result'] = None
                    rec['recon_current_price'] = rec.get('price')
                    rec['recon_days_elapsed'] = 0
                    rec['target_met'] = False
                    rec['stop_loss_hit'] = False
        
        return data
        
    except ValueError:
        return {'error': 'Invalid date format. Use YYYY-MM-DD'}
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return {'error': f'No data found for date {date}'}
        logger.error(f"S3 client error: {e}", error=str(e), operation="get_historical_results", date=date)
        return {'error': f'S3 error: {str(e)}'}
    except Exception as e:
        logger.error(f"Error getting historical results: {e}", error=str(e), operation="get_historical_results", date=date)
        return {'error': f'Error: {str(e)}'}


def list_available_dates() -> List[str]:
    """List all available dates with historical data"""
    try:
        # Check if using local mock
        if hasattr(s3_client, 'list_objects_v2'):
            # Local mock
            response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix='data/daily/')
            objects = response.get('Contents', [])
        else:
            # Real S3
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(
                Bucket=BUCKET_NAME,
                Prefix='data/daily/'
            )
            
            objects = []
            for page in pages:
                if 'Contents' in page:
                    objects.extend(page['Contents'])
        
        dates = []
        for obj in objects:
            key = obj['Key']
            # Extract date from key format: data/daily/YYYY-MM-DD.json
            if key.endswith('.json'):
                date_str = key.replace('data/daily/', '').replace('.json', '')
                dates.append(date_str)
        
        # Sort dates in descending order (newest first)
        dates.sort(reverse=True)
        return dates
        
    except Exception as e:
        logger.error(f"Error listing available dates: {e}", error=str(e), operation="list_available_dates")
        return []


def get_recommendations_summary() -> Dict[str, Any]:
    """Get a summary of recommendations across available dates"""
    try:
        dates = list_available_dates()
        
        if not dates:
            return {'error': 'No historical data available'}
        
        # Get latest data
        latest_data = get_latest_results()
        if 'error' in latest_data:
            return latest_data
        
        # Get some historical stats
        total_days = len(dates)
        latest_count = latest_data.get('count', 0)
        
        # Try to get previous day's data for comparison
        previous_day_count = 0
        if len(dates) > 1:
            previous_data = get_historical_results(dates[1])
            if 'error' not in previous_data:
                previous_day_count = previous_data.get('count', 0)
        
        return {
            'summary': {
                'total_days_with_data': total_days,
                'latest_recommendations': latest_count,
                'previous_day_recommendations': previous_day_count,
                'latest_date': latest_data.get('date'),
                'available_dates': dates[:10]  # Return last 10 dates
            },
            'latest_data': latest_data
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations summary: {e}", error=str(e), operation="get_recommendations_summary")
        return {'error': f'Error: {str(e)}'}


def create_bucket_if_not_exists() -> bool:
    """Create S3 bucket if it doesn't exist (for local testing)"""
    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        logger.info(f"Bucket {BUCKET_NAME} already exists", bucket=BUCKET_NAME, operation="check_bucket")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            # Bucket doesn't exist, create it
            try:
                if AWS_REGION == 'us-east-1':
                    # us-east-1 requires different bucket creation
                    s3_client.create_bucket(Bucket=BUCKET_NAME)
                else:
                    s3_client.create_bucket(
                        Bucket=BUCKET_NAME,
                        CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                    )
                logger.info(f"Created bucket {BUCKET_NAME}", bucket=BUCKET_NAME, operation="create_bucket")
                return True
                
            except ClientError as create_error:
                logger.error(f"Error creating bucket: {create_error}", error=str(create_error), operation="create_bucket")
                return False
        else:
            logger.error(f"Error checking bucket: {e}", error=str(e), operation="check_bucket")
            return False


def configure_website_hosting() -> bool:
    """Configure S3 bucket for static website hosting with security"""
    try:
        # Website configuration
        website_config = {
            'ErrorDocument': {'Key': 'error.html'},
            'IndexDocument': {'Suffix': 'index.html'}
        }
        
        s3_client.put_bucket_website(
            Bucket=BUCKET_NAME,
            WebsiteConfiguration=website_config
        )
        
        # Set bucket policy for public read access (minimal permissions)
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{BUCKET_NAME}/public/*"
                },
                {
                    "Sid": "AllowPublicReadIndex",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{BUCKET_NAME}/index.html"
                }
            ]
        }
        
        s3_client.put_bucket_policy(
            Bucket=BUCKET_NAME,
            Policy=json.dumps(policy)
        )
        
        # Configure CORS for web access
        cors_config = {
            'CORSRules': [
                {
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'HEAD'],
                    'AllowedOrigins': ['*'],
                    'MaxAgeSeconds': 3600
                }
            ]
        }
        
        s3_client.put_bucket_cors(
            Bucket=BUCKET_NAME,
            CORSConfiguration=cors_config
        )
        
        logger.info(f"Configured website hosting for {BUCKET_NAME}")
        return True
        
    except Exception as e:
        logger.error(f"Error configuring website hosting: {e}")
        return False


def get_storage_stats() -> Dict[str, Any]:
    """Get storage statistics"""
    try:
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'daily_files': 0,
            'chart_files': 0,
            'config_files': 0
        }
        
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=BUCKET_NAME):
            for obj in page.get('Contents', []):
                file_key = obj['Key']
                file_size = obj['Size']
                
                stats['total_files'] += 1
                stats['total_size_mb'] += file_size / (1024 * 1024)
                
                if 'data/daily/' in file_key:
                    stats['daily_files'] += 1
                elif 'charts/' in file_key:
                    stats['chart_files'] += 1
                elif 'config/' in file_key:
                    stats['config_files'] += 1
        
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        return {'error': str(e)}


def cleanup_old_files(days_threshold: int = 1000) -> Dict[str, Any]:
    """Clean up files older than specified days"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        files_deleted = []
        
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=BUCKET_NAME):
            for obj in page.get('Contents', []):
                file_key = obj['Key']
                last_modified = obj['LastModified'].replace(tzinfo=None)
                
                # Skip essential files
                if file_key in ['data/latest.json', 'index.html']:
                    continue
                
                if last_modified < cutoff_date:
                    s3_client.delete_object(Bucket=BUCKET_NAME, Key=file_key)
                    files_deleted.append(file_key)
        
        return {
            'success': True,
            'files_deleted': len(files_deleted),
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old files: {e}")
        return {'success': False, 'error': str(e)}


def update_available_dates() -> bool:
    """
    Update the dates.json file with all available historical dates
    
    Scans the data/daily/ directory and creates/updates dates.json
    """
    try:
        # List all objects in data/daily/
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix='data/daily/')
        dates = []
        
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                if key.endswith('.json') and key != 'data/daily/dates.json':
                    # Extract date from filename (e.g., 'data/daily/2026-02-01.json' -> '2026-02-01')
                    date = key.split('/')[-1].replace('.json', '')
                    dates.append(date)
        
        # Sort dates in descending order (newest first)
        dates.sort(reverse=True)
        
        # Create dates.json data
        dates_data = {
            'success': True,
            'dates': dates,
            'count': len(dates),
            'last_updated': dates[0] if dates else None,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Upload dates.json to S3
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key='data/dates.json',
            Body=json.dumps(dates_data, indent=2),
            ContentType='application/json',
            ServerSideEncryption='AES256'
        )
        
        logger.info(f"Updated dates.json with {len(dates)} available dates")
        return True
        
    except ClientError as e:
        logger.error(f"S3 client error updating dates: {e}")
        return False
    except Exception as e:
        logger.error(f"Error updating available dates: {e}")
        return False


def get_available_dates() -> Dict[str, Any]:
    """
    Get available historical dates from dates.json
    
    Returns the dates.json content or generates it if missing
    """
    try:
        # Try to get existing dates.json
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key='data/dates.json')
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            # dates.json doesn't exist, create it
            logger.info("dates.json not found, creating it...")
            if update_available_dates():
                # Try again after creating
                response = s3_client.get_object(Bucket=BUCKET_NAME, Key='data/dates.json')
                content = response['Body'].read().decode('utf-8')
                return json.loads(content)
            else:
                return {'success': False, 'error': 'Failed to create dates.json'}
        else:
            raise e
    except Exception as e:
        logger.error(f"Error getting available dates: {e}")
        return {'success': False, 'error': str(e)}


def get_historical_data(date: str) -> Dict[str, Any]:
    """
    Get historical recommendations for a specific date
    
    Args:
        date: Date in YYYY-MM-DD format
    
    Returns:
        Historical data for the specified date
    """
    try:
        # Validate date format
        from datetime import datetime
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return {'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'}
        
        # Get historical data from S3
        key = f'data/daily/{date}.json'
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
        content = response['Body'].read().decode('utf-8')
        data = json.loads(content)
        
        # Add metadata
        data['retrieved_at'] = datetime.utcnow().isoformat()
        data['source'] = 's3'
        
        return data
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return {'success': False, 'error': f'No historical data found for date {date}'}
        else:
            raise e
    except Exception as e:
        logger.error(f"Error getting historical data for {date}: {e}")
        return {'success': False, 'error': str(e)}
