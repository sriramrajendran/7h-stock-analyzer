"""
Purge service for cleaning up old recommendations and data
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from app.models import PurgeRequest

logger = logging.getLogger(__name__)

class PurgeService:
    """Service for purging old recommendations and data"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
    
    def purge_old_recommendations(self, request: PurgeRequest) -> Dict[str, Any]:
        """Purge recommendations older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=request.days_threshold)
            
            # Get list of files to purge
            files_to_purge = self._get_files_to_purge(cutoff_date)
            
            if request.dry_run:
                return {
                    'success': True,
                    'dry_run': True,
                    'files_to_purge': files_to_purge,
                    'count': len(files_to_purge),
                    'cutoff_date': cutoff_date.isoformat()
                }
            
            # Actually purge files
            purged_files = []
            for file_key in files_to_purge:
                try:
                    self.s3_client.delete_object(
                        Bucket=self.bucket_name,
                        Key=file_key
                    )
                    purged_files.append(file_key)
                    logger.info(f"Purged file: {file_key}")
                except Exception as e:
                    logger.error(f"Failed to purge {file_key}: {str(e)}")
            
            return {
                'success': True,
                'dry_run': False,
                'purged_files': purged_files,
                'count': len(purged_files),
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Purge operation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _get_files_to_purge(self, cutoff_date: datetime) -> List[str]:
        """Get list of files older than cutoff date"""
        files_to_purge = []
        
        # Purge daily recommendation files
        daily_files = self._list_daily_files('data/daily/')
        for file_key, file_date in daily_files:
            if file_date < cutoff_date:
                files_to_purge.append(file_key)
        
        # Purge recon files
        recon_files = self._list_daily_files('recon/daily/')
        for file_key, file_date in recon_files:
            if file_date < cutoff_date:
                files_to_purge.append(file_key)
        
        # Purge old chart files
        chart_files = self._list_chart_files()
        for file_key, file_date in chart_files:
            if file_date < cutoff_date:
                files_to_purge.append(file_key)
        
        return files_to_purge
    
    def _list_daily_files(self, prefix: str) -> List[tuple]:
        """List daily files with their dates"""
        files = []
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                for obj in page.get('Contents', []):
                    file_key = obj['Key']
                    
                    # Extract date from filename (YYYY-MM-DD.json)
                    try:
                        date_str = file_key.split('/')[-1].replace('.json', '')
                        file_date = datetime.strptime(date_str, '%Y-%m-%d')
                        files.append((file_key, file_date))
                    except ValueError:
                        # Skip files that don't match the expected format
                        continue
        
        except Exception as e:
            logger.error(f"Error listing files with prefix {prefix}: {str(e)}")
        
        return files
    
    def _list_chart_files(self) -> List[tuple]:
        """List chart files with their dates"""
        files = []
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix='charts/'):
                for obj in page.get('Contents', []):
                    file_key = obj['Key']
                    last_modified = obj['LastModified'].replace(tzinfo=None)
                    files.append((file_key, last_modified))
        
        except Exception as e:
            logger.error(f"Error listing chart files: {str(e)}")
        
        return files
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            stats = {
                'total_files': 0,
                'total_size_mb': 0,
                'daily_recommendations': 0,
                'recon_files': 0,
                'chart_files': 0,
                'oldest_file': None,
                'newest_file': None
            }
            
            oldest_date = None
            newest_date = None
            
            # List all files in the bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket_name):
                for obj in page.get('Contents', []):
                    file_key = obj['Key']
                    file_size = obj['Size']
                    last_modified = obj['LastModified'].replace(tzinfo=None)
                    
                    stats['total_files'] += 1
                    stats['total_size_mb'] += file_size / (1024 * 1024)  # Convert to MB
                    
                    # Update oldest/newest dates
                    if oldest_date is None or last_modified < oldest_date:
                        oldest_date = last_modified
                    if newest_date is None or last_modified > newest_date:
                        newest_date = last_modified
                    
                    # Categorize files
                    if 'data/daily/' in file_key:
                        stats['daily_recommendations'] += 1
                    elif 'recon/daily/' in file_key:
                        stats['recon_files'] += 1
                    elif 'charts/' in file_key:
                        stats['chart_files'] += 1
            
            # Format dates
            if oldest_date:
                stats['oldest_file'] = oldest_date.isoformat()
            if newest_date:
                stats['newest_file'] = newest_date.isoformat()
            
            # Round size
            stats['total_size_mb'] = round(stats['total_size_mb'], 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {'error': str(e)}
    
    def cleanup_duplicates(self) -> Dict[str, Any]:
        """Clean up duplicate files"""
        try:
            duplicates_found = []
            duplicates_removed = []
            
            # Check for duplicate daily files
            daily_files = self._list_daily_files('data/daily/')
            date_groups = {}
            
            for file_key, file_date in daily_files:
                date_str = file_date.strftime('%Y-%m-%d')
                if date_str not in date_groups:
                    date_groups[date_str] = []
                date_groups[date_str].append(file_key)
            
            # Remove duplicates (keep the newest)
            for date_str, files in date_groups.items():
                if len(files) > 1:
                    # Sort by last modified and keep the newest
                    files.sort(key=lambda x: self._get_file_last_modified(x), reverse=True)
                    files_to_remove = files[1:]  # Remove all but the newest
                    
                    for file_key in files_to_remove:
                        try:
                            self.s3_client.delete_object(
                                Bucket=self.bucket_name,
                                Key=file_key
                            )
                            duplicates_removed.append(file_key)
                            logger.info(f"Removed duplicate file: {file_key}")
                        except Exception as e:
                            logger.error(f"Failed to remove duplicate {file_key}: {str(e)}")
                    
                    duplicates_found.extend(files[1:])
            
            return {
                'success': True,
                'duplicates_found': len(duplicates_found),
                'duplicates_removed': len(duplicates_removed),
                'files_removed': duplicates_removed
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up duplicates: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _get_file_last_modified(self, file_key: str) -> datetime:
        """Get last modified date for a file"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return response['LastModified'].replace(tzinfo=None)
        except Exception:
            return datetime.min

def run_purge_operation(days_threshold: int = 1000, dry_run: bool = True) -> Dict[str, Any]:
    """Main function to run purge operation"""
    purge_service = PurgeService()
    request = PurgeRequest(days_threshold=days_threshold, dry_run=dry_run)
    return purge_service.purge_old_recommendations(request)
