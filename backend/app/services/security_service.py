"""
Security service for API key management and access control
"""

import os
import hashlib
import hmac
import secrets
from typing import Dict, Any, Optional
import boto3
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SecurityService:
    """Service for managing API security and access control"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.api_keys_file = 'config/api_keys.json'
    
    def generate_api_key(self, name: str, permissions: list = None) -> Dict[str, Any]:
        """Generate a new API key"""
        try:
            if permissions is None:
                permissions = ['read', 'run']  # Default permissions
            
            # Generate secure API key
            api_key = secrets.token_urlsafe(32)
            key_hash = self._hash_api_key(api_key)
            
            # Create key record
            key_record = {
                'name': name,
                'key_hash': key_hash,
                'permissions': permissions,
                'created_at': datetime.utcnow().isoformat(),
                'last_used': None,
                'usage_count': 0,
                'active': True
            }
            
            # Save to S3
            self._save_api_key(key_record)
            
            return {
                'success': True,
                'api_key': api_key,  # Return only the actual key once
                'name': name,
                'permissions': permissions,
                'created_at': key_record['created_at']
            }
            
        except Exception as e:
            logger.error(f"Error generating API key: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def validate_api_key(self, api_key: str, required_permission: str = None) -> Dict[str, Any]:
        """Validate API key and check permissions"""
        try:
            # Load API keys
            api_keys = self._load_api_keys()
            
            # Find matching key
            key_record = None
            for key_data in api_keys:
                if self._verify_api_key(api_key, key_data['key_hash']):
                    key_record = key_data
                    break
            
            if not key_record:
                return {'valid': False, 'error': 'Invalid API key'}
            
            if not key_record['active']:
                return {'valid': False, 'error': 'API key is inactive'}
            
            # Check permissions
            if required_permission and required_permission not in key_record['permissions']:
                return {'valid': False, 'error': f'Insufficient permissions. Required: {required_permission}'}
            
            # Update usage stats
            self._update_key_usage(key_record['key_hash'])
            
            return {
                'valid': True,
                'name': key_record['name'],
                'permissions': key_record['permissions']
            }
            
        except Exception as e:
            logger.error(f"Error validating API key: {str(e)}")
            return {'valid': False, 'error': str(e)}
    
    def revoke_api_key(self, key_name: str) -> Dict[str, Any]:
        """Revoke an API key"""
        try:
            api_keys = self._load_api_keys()
            
            # Find and deactivate the key
            key_found = False
            for key_data in api_keys:
                if key_data['name'] == key_name:
                    key_data['active'] = False
                    key_data['revoked_at'] = datetime.utcnow().isoformat()
                    key_found = True
                    break
            
            if not key_found:
                return {'success': False, 'error': 'API key not found'}
            
            # Save updated keys
            self._save_api_keys(api_keys)
            
            return {'success': True, 'message': f'API key {key_name} has been revoked'}
            
        except Exception as e:
            logger.error(f"Error revoking API key: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def list_api_keys(self) -> Dict[str, Any]:
        """List all API keys (without sensitive data)"""
        try:
            api_keys = self._load_api_keys()
            
            safe_keys = []
            for key_data in api_keys:
                safe_key = {
                    'name': key_data['name'],
                    'permissions': key_data['permissions'],
                    'created_at': key_data['created_at'],
                    'last_used': key_data.get('last_used'),
                    'usage_count': key_data['usage_count'],
                    'active': key_data['active']
                }
                if 'revoked_at' in key_data:
                    safe_key['revoked_at'] = key_data['revoked_at']
                
                safe_keys.append(safe_key)
            
            return {'success': True, 'api_keys': safe_keys}
            
        except Exception as e:
            logger.error(f"Error listing API keys: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def _verify_api_key(self, api_key: str, key_hash: str) -> bool:
        """Verify API key against stored hash"""
        return hmac.compare_digest(self._hash_api_key(api_key), key_hash)
    
    def _load_api_keys(self) -> list:
        """Load API keys from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self.api_keys_file
            )
            return json.loads(response['Body'].read().decode('utf-8'))
        except self.s3_client.exceptions.NoSuchKey:
            # File doesn't exist, return empty list
            return []
        except Exception as e:
            logger.error(f"Error loading API keys: {str(e)}")
            return []
    
    def _save_api_key(self, key_record: dict):
        """Save a single API key"""
        api_keys = self._load_api_keys()
        api_keys.append(key_record)
        self._save_api_keys(api_keys)
    
    def _save_api_keys(self, api_keys: list):
        """Save API keys to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self.api_keys_file,
                Body=json.dumps(api_keys, indent=2),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
        except Exception as e:
            logger.error(f"Error saving API keys: {str(e)}")
            raise
    
    def _update_key_usage(self, key_hash: str):
        """Update key usage statistics"""
        try:
            api_keys = self._load_api_keys()
            
            for key_data in api_keys:
                if key_data['key_hash'] == key_hash:
                    key_data['last_used'] = datetime.utcnow().isoformat()
                    key_data['usage_count'] += 1
                    break
            
            self._save_api_keys(api_keys)
            
        except Exception as e:
            logger.error(f"Error updating key usage: {str(e)}")
    
    def create_default_admin_key(self) -> Dict[str, Any]:
        """Create default admin key if none exists"""
        try:
            api_keys = self._load_api_keys()
            
            # Check if admin key already exists
            for key_data in api_keys:
                if key_data['name'] == 'admin' and key_data['active']:
                    return {'success': True, 'message': 'Admin key already exists'}
            
            # Create admin key
            return self.generate_api_key('admin', ['read', 'write', 'run', 'admin'])
            
        except Exception as e:
            logger.error(f"Error creating admin key: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def validate_request_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Validate webhook signature"""
        try:
            expected_signature = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error validating signature: {str(e)}")
            return False
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data (placeholder - use AWS KMS in production)"""
        # In production, use AWS KMS for encryption
        # For now, just return the data (not secure for production)
        logger.warning("Using placeholder encryption - implement AWS KMS for production")
        return data
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data (placeholder - use AWS KMS in production)"""
        # In production, use AWS KMS for decryption
        logger.warning("Using placeholder decryption - implement AWS KMS for production")
        return encrypted_data

# Global security service instance
security_service = SecurityService()
