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
import logging

logger = logging.getLogger(__name__)

# Configuration
BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'stock-analyzer-local')
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
        
        # Convert recommendations to dicts
        recommendations_data = [rec.dict() for rec in recommendations]
        
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
        
        return True
        
    except ClientError as e:
        logger.error(f"S3 client error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error persisting results: {e}")
        return False


def get_latest_results() -> Dict[str, Any]:
    """Get the latest recommendations from S3"""
    try:
        response = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key='data/latest.json'
        )
        
        data = json.loads(response['Body'].read().decode('utf-8'))
        return data
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return {'error': 'No latest results found'}
        print(f"S3 client error: {e}")
        return {'error': f'S3 error: {str(e)}'}
    except Exception as e:
        print(f"Error getting latest results: {e}")
        return {'error': f'Error: {str(e)}'}


def get_historical_results(date: str) -> Dict[str, Any]:
    """
    Get historical recommendations for a specific date
    
    Args:
        date: Date string in YYYY-MM-DD format
    """
    try:
        # Validate date format
        datetime.strptime(date, '%Y-%m-%d')
        
        response = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key=f'data/daily/{date}.json'
        )
        
        data = json.loads(response['Body'].read().decode('utf-8'))
        return data
        
    except ValueError:
        return {'error': 'Invalid date format. Use YYYY-MM-DD'}
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return {'error': f'No data found for date {date}'}
        print(f"S3 client error: {e}")
        return {'error': f'S3 error: {str(e)}'}
    except Exception as e:
        print(f"Error getting historical results: {e}")
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
        print(f"Error listing available dates: {e}")
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
        print(f"Error getting recommendations summary: {e}")
        return {'error': f'Error: {str(e)}'}


def create_bucket_if_not_exists() -> bool:
    """Create S3 bucket if it doesn't exist (for local testing)"""
    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        print(f"Bucket {BUCKET_NAME} already exists")
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
                print(f"Created bucket {BUCKET_NAME}")
                return True
                
            except ClientError as create_error:
                print(f"Error creating bucket: {create_error}")
                return False
        else:
            print(f"Error checking bucket: {e}")
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
