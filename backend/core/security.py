"""
JWT Authentication and Password Security
Handles JWT token generation, validation, and password hashing
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class JWTHandler:
    """
    JWT token generation and validation with password security
    
    Features:
    - JWT access and refresh token generation
    - Password hashing and verification using bcrypt
    - Token expiration and validation
    - Secure random token generation
    """
    
    def __init__(self):
        """Initialize JWT handler with settings"""
        self.secret_key = settings.SECRET_KEY
        self.algorithm = getattr(settings, 'jwt_algorithm', 'HS256')
        self.access_token_expire_minutes = getattr(settings, 'jwt_access_ttl_seconds', 900) // 60  # Convert to minutes
        self.refresh_token_expire_days = getattr(settings, 'jwt_refresh_ttl_seconds', 604800) // 86400  # Convert to days
        
        if not self.secret_key or self.secret_key == "your-secret-key-change-this-in-production":
            logger.warning("Using default JWT secret key - change this in production!")
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token
        
        Args:
            data: Payload data to encode in token
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Created access token for user: {data.get('sub', 'unknown')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT refresh token
        
        Args:
            data: Payload data to encode in token
            
        Returns:
            Encoded JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh"})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Created refresh token for user: {data.get('sub', 'unknown')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string to verify
            
        Returns:
            Decoded payload if valid
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.debug(f"Token validation failed: {e}")
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        try:
            hashed = pwd_context.hash(password)
            logger.debug("Password hashed successfully")
            return hashed
        except Exception as e:
            logger.error(f"Failed to hash password: {e}")
            raise
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            result = pwd_context.verify(plain_password, hashed_password)
            logger.debug(f"Password verification: {'success' if result else 'failed'}")
            return result
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Alias for hash_password for backwards compatibility"""
        return self.hash_password(password)


# Global instance for convenience
jwt_handler = JWTHandler()


def get_current_time() -> datetime:
    """Get current UTC time with timezone awareness"""
    return datetime.now(timezone.utc)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Convenience function for creating access tokens"""
    return jwt_handler.create_access_token(data, expires_delta)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Convenience function for password verification"""
    return jwt_handler.verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Convenience function for password hashing"""
    return jwt_handler.hash_password(password)