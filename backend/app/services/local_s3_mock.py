"""
Local S3 storage mock for testing without AWS credentials
"""

import os
import json
import boto3
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class LocalS3Mock:
    """Mock S3 storage using local filesystem"""
    
    def __init__(self, bucket_name: str = "stock-ui-test"):
        self.bucket_name = bucket_name
        self.base_path = Path(__file__).parent.parent.parent / "s3_data" / bucket_name
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create data directory structure
        (self.base_path / "data").mkdir(exist_ok=True)
        (self.base_path / "data" / "daily").mkdir(exist_ok=True)
        
        print(f"🗂️  Local S3 mock initialized at: {self.base_path}")
    
    def put_object(self, Bucket: str = None, Key: str = None, Body: str = None, **kwargs):
        """Mock S3 put_object"""
        if Key is None or Body is None:
            raise Exception("Key and Body parameters are required")
        
        file_path = self.base_path / Key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write(Body)
        
        print(f"💾 Saved to local S3: {Key}")
        return True
    
    def get_object(self, Bucket: str = None, Key: str = None, **kwargs):
        """Mock S3 get_object"""
        if Key is None:
            raise Exception("Key parameter is required")
        
        file_path = self.base_path / Key
        
        if not file_path.exists():
            raise Exception(f"Key not found: {Key}")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        class MockResponse:
            def __init__(self, content):
                self.body = MockBody(content)
        
        class MockBody:
            def __init__(self, content):
                self.content = content
                self._content = content.encode()
            
            def read(self):
                return self._content
            
            def decode(self, encoding='utf-8'):
                return self.content
        
        return {'Body': MockBody(content)}
    
    def list_objects_v2(self, Bucket: str, Prefix: str = ""):
        """Mock S3 list_objects_v2"""
        search_path = self.base_path / Prefix if Prefix else self.base_path
        
        objects = []
        for file_path in search_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(self.base_path)
                objects.append({
                    'Key': str(relative_path),
                    'LastModified': datetime.fromtimestamp(file_path.stat().st_mtime),
                    'Size': file_path.stat().st_size
                })
        
        class MockResponse:
            def __init__(self, objects):
                self.get = lambda key: {'Contents': objects} if key == 'Contents' else None
        
        return MockResponse(objects)


def get_s3_client():
    """Get S3 client - use local mock if no AWS credentials"""
    try:
        # Try real AWS S3 first
        s3 = boto3.client('s3')
        # Test credentials
        s3.list_buckets()
        return s3
    except:
        # Fall back to local mock
        print("⚠️  No AWS credentials - using local S3 mock")
        return LocalS3Mock()


def get_bucket_name():
    """Get bucket name - use local test bucket if no AWS credentials"""
    try:
        # Try to get real bucket name from environment
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        if bucket_name:
            return bucket_name
        
        # Test if we can access real S3
        s3 = boto3.client('s3')
        s3.list_buckets()
        return os.environ.get('S3_BUCKET_NAME', 'stock-analyzer-default')
    except:
        # Use local test bucket
        return 'stock-ui-test'
