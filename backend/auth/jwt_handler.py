"""
Local JWT token handling for fallback authentication
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import uuid
import logging

from backend.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class JWTHandler:
    """Handle local JWT token creation and verification"""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_seconds = settings.jwt_access_ttl_seconds
        self.refresh_token_expire_seconds = settings.jwt_refresh_ttl_seconds
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        if not self.secret_key or self.secret_key == "your-secret-key-change-this-in-production":
            logger.warning("Using default JWT secret key - change this in production!")
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(seconds=self.access_token_expire_seconds)
        
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Created access token for user: {data.get('sub', 'unknown')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token has expired
            exp = payload.get("exp")
            if exp is None:
                logger.debug("Token validation failed: missing expiration")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing expiration"
                )
            
            if datetime.now(timezone.utc) > datetime.fromtimestamp(exp, tz=timezone.utc):
                logger.debug("Token validation failed: token expired")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return payload
            
        except JWTError as e:
            logger.debug(f"Token validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        except Exception as e:
            logger.error(f"Unexpected error verifying token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Create JWT refresh token with JTI"""
        to_encode = data.copy()
        jti = str(uuid.uuid4())
        expire = datetime.now(timezone.utc) + timedelta(seconds=self.refresh_token_expire_seconds)
        to_encode.update({
            "exp": expire, 
            "iat": datetime.now(timezone.utc), 
            "type": "refresh",
            "jti": jti
        })
        
        try:
            token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Created refresh token for user: {data.get('sub', 'unknown')}")
            return {"token": token, "jti": jti, "expires_at": expire}
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise
    
    def create_user_tokens(self, user_id: str, email: str, username: str) -> Dict[str, Any]:
        """Create access and refresh tokens for user"""
        token_data = {
            "sub": user_id,
            "email": email,
            "username": username,
        }
        access_token = self.create_access_token({**token_data, "type": "access"})
        refresh_data = self.create_refresh_token({**token_data})
        return {
            "access_token": access_token, 
            "refresh_token": refresh_data["token"],
            "refresh_jti": refresh_data["jti"],
            "refresh_expires_at": refresh_data["expires_at"]
        }
    
    def create_user_token(self, user_id: str, email: str, username: str) -> str:
        """Create token for user (deprecated - use create_user_tokens)"""
        token_data = {
            "sub": user_id,
            "email": email,
            "username": username,
            "type": "access_token"
        }
        return self.create_access_token(token_data)

# Global instance
jwt_handler = JWTHandler()