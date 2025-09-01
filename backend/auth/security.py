"""
Security utilities for API key management and validation
"""
import secrets
import string
from typing import Dict, Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import User
from backend.core.config import get_settings

settings = get_settings()

class APIKeyManager:
    """Manage API keys for external integrations"""
    
    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """Generate a secure API key"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def validate_api_key_format(api_key: str) -> bool:
        """Validate API key format"""
        if not api_key or len(api_key) < 16:
            return False
        
        # Check if it contains only valid characters
        valid_chars = set(string.ascii_letters + string.digits + '-_')
        return all(c in valid_chars for c in api_key)

class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, bool]:
        """Validate password strength"""
        checks = {
            "min_length": len(password) >= 8,
            "has_upper": any(c.isupper() for c in password),
            "has_lower": any(c.islower() for c in password),
            "has_digit": any(c.isdigit() for c in password),
            "has_special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        }
        
        checks["is_strong"] = all([
            checks["min_length"],
            checks["has_upper"],
            checks["has_lower"],
            checks["has_digit"]
        ])
        
        return checks
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize user input"""
        if not text:
            return ""
        
        # Trim whitespace and limit length
        sanitized = text.strip()[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ["<", ">", "&", "\"", "'", "/", "\\"]
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        return sanitized
    
    @staticmethod
    def validate_email_domain(email: str, allowed_domains: Optional[list] = None) -> bool:
        """Validate email domain against allowlist"""
        if not allowed_domains:
            return True
        
        domain = email.split("@")[-1].lower()
        return domain in [d.lower() for d in allowed_domains]

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self._requests = {}
    
    def is_allowed(self, key: str, limit: int = 100, window: int = 3600) -> bool:
        """Check if request is allowed within rate limit"""
        import time
        
        current_time = time.time()
        window_start = current_time - window
        
        # Clean old requests
        if key in self._requests:
            self._requests[key] = [
                req_time for req_time in self._requests[key] 
                if req_time > window_start
            ]
        else:
            self._requests[key] = []
        
        # Check limit
        if len(self._requests[key]) >= limit:
            return False
        
        # Add current request
        self._requests[key].append(current_time)
        return True

# Global instances
api_key_manager = APIKeyManager()
security_validator = SecurityValidator()
rate_limiter = RateLimiter()

# Security dependencies
async def validate_rate_limit(
    user_id: str = None,
    ip_address: str = "unknown",
    limit: int = 100
):
    """Rate limiting dependency"""
    key = user_id or ip_address
    
    if not rate_limiter.is_allowed(key, limit):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )

async def validate_api_key(api_key: str) -> bool:
    """Validate API key format and return validity"""
    if not api_key_manager.validate_api_key_format(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )
    return True

# Secure headers middleware
def add_security_headers(response):
    """Add security headers to response"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response