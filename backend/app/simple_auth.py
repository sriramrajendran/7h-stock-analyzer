"""
Simple API Key Authentication - No Complexity, Good Security
"""

import os
from fastapi import HTTPException, Header, Depends
from functools import wraps

# Static API key from environment variables
API_KEY = os.getenv('API_KEY')
REQUIRE_AUTH = os.getenv('REQUIRE_AUTH', 'true').lower() == 'true'

def verify_api_key(x_api_key: str = Header(None, alias='X-API-Key')):
    """Simple API key verification"""
    if not REQUIRE_AUTH:
        return True  # Skip auth in development
    
    if not API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="API key not configured"
        )
    
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(
            status_code=403, 
            detail="Invalid API key"
        )
    
    return True

def require_auth(func):
    """Decorator for simple authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not REQUIRE_AUTH:
            return await func(*args, **kwargs)
        
        # Extract API key from request
        from fastapi import Request
        request = kwargs.get('request')
        if not request:
            raise HTTPException(status_code=500, detail="Request context required")
        
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_KEY:
            raise HTTPException(status_code=403, detail="Invalid API key")
        
        return await func(*args, **kwargs)
    return wrapper

# Usage examples:
# @app.get("/recommendations")
# def get_recommendations(auth: bool = Depends(verify_api_key)):
#     # Your code here

# OR
# @require_auth
# @app.get("/recommendations") 
# def get_recommendations():
#     # Your code here
