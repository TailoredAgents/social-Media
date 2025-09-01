#!/usr/bin/env python3
"""
Debug script to check authentication configuration in production
"""
import os
import sys
import logging
from datetime import datetime, timezone

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from core.config import get_settings
    from core.security import JWTHandler
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_auth_config():
    """Debug authentication configuration"""
    try:
        logger.info("🔧 Debugging authentication configuration...")
        
        # Check settings
        settings = get_settings()
        
        # Check critical auth settings
        logger.info(f"SECRET_KEY configured: {bool(settings.SECRET_KEY and settings.SECRET_KEY != 'your-secret-key-change-this-in-production')}")
        logger.info(f"SECRET_KEY length: {len(settings.SECRET_KEY) if settings.SECRET_KEY else 0}")
        
        # Check JWT handler
        jwt_handler = JWTHandler()
        logger.info(f"JWT Algorithm: {jwt_handler.algorithm}")
        logger.info(f"Access token expire minutes: {jwt_handler.access_token_expire_minutes}")
        logger.info(f"Refresh token expire days: {jwt_handler.refresh_token_expire_days}")
        
        # Test token creation
        test_payload = {"sub": "1", "email": "test@example.com"}
        try:
            access_token = jwt_handler.create_access_token(test_payload)
            logger.info("✅ Access token creation: SUCCESS")
            
            # Test token verification
            payload = jwt_handler.verify_token(access_token)
            logger.info("✅ Token verification: SUCCESS")
            logger.info(f"Decoded payload: {payload}")
            
        except Exception as token_error:
            logger.error(f"❌ Token creation/verification failed: {token_error}")
        
        # Check database connection
        try:
            from db.database import get_db, engine
            logger.info("✅ Database connection: Available")
        except Exception as db_error:
            logger.error(f"❌ Database connection failed: {db_error}")
        
        logger.info("🎉 Authentication debug completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Authentication debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_auth_config()
    sys.exit(0 if success else 1)