"""
API Gateway Lambda Authorizer for stock analyzer
"""

import json
import os

def handler(event, context):
    """Lambda authorizer handler"""
    try:
        # Extract API key from headers
        headers = event.get('headers', {})
        api_key = headers.get('x-api-key') or headers.get('X-API-Key')
        
        # Expected API key
        expected_api_key = 'e0fb50277426ebfb42e571710cade9a8e0d5cfb58738a199cd256408374a02a8'
        
        # Validate API key
        if api_key == expected_api_key:
            return {
                'isAuthorized': True,
                'context': {
                    'apiKey': api_key
                }
            }
        else:
            return {
                'isAuthorized': False
            }
            
    except Exception as e:
        return {
            'isAuthorized': False,
            'error': str(e)
        }
