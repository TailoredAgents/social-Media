"""
Comprehensive security configuration and hardening
"""
import secrets
import hashlib
import hmac
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ipaddress import ip_address, ip_network
import re
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
import logging

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Centralized security configuration"""
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 12
    MAX_PASSWORD_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL_CHARS = True
    PASSWORD_HISTORY_SIZE = 5
    
    # Rate limiting
    DEFAULT_RATE_LIMIT = 100  # requests per minute
    AUTHENTICATION_RATE_LIMIT = 10  # login attempts per minute
    API_BURST_LIMIT = 200  # burst capacity
    
    # Session security
    SESSION_TIMEOUT_MINUTES = 60
    REFRESH_TOKEN_ROTATION = True
    FORCE_HTTPS = True
    
    # Content security
    MAX_CONTENT_LENGTH = 10000
    ALLOWED_FILE_TYPES = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.pdf', '.txt'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # IP allowlisting/blocklisting
    BLOCKED_IP_RANGES = [
        '10.0.0.0/8',      # Private network
        '172.16.0.0/12',   # Private network
        '192.168.0.0/16',  # Private network
    ]
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }

class PasswordValidator:
    """Validate password strength and requirements"""
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """
        Validate password against security requirements
        
        Returns:
            Dict with validation results and feedback
        """
        issues = []
        score = 0
        
        # Length check
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            issues.append(f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters long")
        elif len(password) >= SecurityConfig.MIN_PASSWORD_LENGTH:
            score += 20
            
        if len(password) > SecurityConfig.MAX_PASSWORD_LENGTH:
            issues.append(f"Password must not exceed {SecurityConfig.MAX_PASSWORD_LENGTH} characters")
        
        # Character requirements
        if SecurityConfig.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        elif re.search(r'[A-Z]', password):
            score += 20
            
        if SecurityConfig.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        elif re.search(r'[a-z]', password):
            score += 20
            
        if SecurityConfig.REQUIRE_DIGITS and not re.search(r'\d', password):
            issues.append("Password must contain at least one digit")
        elif re.search(r'\d', password):
            score += 20
            
        if SecurityConfig.REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")
        elif re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 20
        
        # Common password patterns
        common_patterns = [
            r'123456',
            r'password',
            r'qwerty',
            r'admin',
            r'letmein'
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                issues.append("Password contains common patterns that are easily guessed")
                score -= 10
                break
        
        # Determine strength
        if score >= 80:
            strength = "strong"
        elif score >= 60:
            strength = "medium"
        else:
            strength = "weak"
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "strength": strength,
            "score": max(0, score)
        }
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self):
        self.requests = {}  # In production, use Redis
        self.blocked_ips = set()
    
    def is_allowed(self, client_ip: str, endpoint: str = "default") -> bool:
        """Check if request is within rate limits"""
        current_time = time.time()
        key = f"{client_ip}:{endpoint}"
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            return False
        
        # Get rate limit for endpoint
        if endpoint == "auth":
            rate_limit = SecurityConfig.AUTHENTICATION_RATE_LIMIT
        else:
            rate_limit = SecurityConfig.DEFAULT_RATE_LIMIT
        
        # Initialize or clean old requests
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests (older than 1 minute)
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < 60
        ]
        
        # Check rate limit
        if len(self.requests[key]) >= rate_limit:
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
            return False
        
        # Add current request
        self.requests[key].append(current_time)
        return True
    
    def block_ip(self, client_ip: str, duration_minutes: int = 60):
        """Block IP address temporarily"""
        self.blocked_ips.add(client_ip)
        logger.warning(f"Blocked IP {client_ip} for {duration_minutes} minutes")
        
        # In production, use a task scheduler to unblock
        # For now, just log the action

class InputSanitizer:
    """Sanitize and validate user inputs"""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            raise ValueError("Input must be a string")
        
        # Remove null bytes
        sanitized = input_str.replace('\x00', '')
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # Remove dangerous characters for SQL injection prevention
        # Note: This is secondary to parameterized queries
        dangerous_chars = ['<script', 'javascript:', 'onload=', 'onerror=']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format and safety"""
        # Basic URL pattern
        pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
        if not re.match(pattern, url):
            return False
        
        # Block dangerous protocols
        dangerous_protocols = ['javascript:', 'data:', 'file:']
        for protocol in dangerous_protocols:
            if url.lower().startswith(protocol):
                return False
        
        return True
    
    @staticmethod
    def validate_content_length(content: str) -> bool:
        """Validate content length"""
        return len(content) <= SecurityConfig.MAX_CONTENT_LENGTH

class IPValidator:
    """Validate and filter IP addresses"""
    
    @staticmethod
    def is_blocked_ip(client_ip: str) -> bool:
        """Check if IP is in blocked ranges"""
        try:
            ip = ip_address(client_ip)
            for blocked_range in SecurityConfig.BLOCKED_IP_RANGES:
                if ip in ip_network(blocked_range):
                    return True
            return False
        except ValueError:
            logger.warning(f"Invalid IP address: {client_ip}")
            return True  # Block invalid IPs
    
    @staticmethod
    def extract_client_ip(request: Request) -> str:
        """Extract real client IP from request"""
        # Check for forwarded headers (for load balancers/proxies)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Take the first IP (client)
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"

class CSRFProtection:
    """CSRF token generation and validation"""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_csrf_token(token: str, session_token: str) -> bool:
        """Validate CSRF token"""
        return hmac.compare_digest(token, session_token)

class SecurityMiddleware:
    """Security middleware for FastAPI"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
    
    async def __call__(self, request: Request, call_next):
        """Process request through security checks"""
        
        # Extract client IP
        client_ip = IPValidator.extract_client_ip(request)
        
        # Check blocked IPs
        if IPValidator.is_blocked_ip(client_ip):
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied from this IP address"
            )
        
        # Rate limiting
        endpoint = "auth" if "auth" in str(request.url) else "default"
        if not self.rate_limiter.is_allowed(client_ip, endpoint):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        
        return response

class ContentValidator:
    """Validate content for security issues"""
    
    @staticmethod
    def scan_for_malicious_content(content: str) -> Dict[str, Any]:
        """Scan content for potential security issues"""
        issues = []
        
        # Check for script injection
        if re.search(r'<script.*?>.*?</script>', content, re.IGNORECASE | re.DOTALL):
            issues.append("Potential script injection detected")
        
        # Check for SQL injection patterns
        sql_patterns = [
            r"union\s+select",
            r"drop\s+table",
            r"insert\s+into",
            r"delete\s+from",
            r"exec\s*\(",
            r"xp_cmdshell"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append("Potential SQL injection pattern detected")
                break
        
        # Check for XSS patterns
        xss_patterns = [
            r"javascript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"<iframe",
            r"<object",
            r"<embed"
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append("Potential XSS pattern detected")
                break
        
        return {
            "safe": len(issues) == 0,
            "issues": issues,
            "risk_level": "high" if issues else "low"
        }

class AuditLogger:
    """Security audit logging"""
    
    @staticmethod
    def log_security_event(
        event_type: str,
        user_id: Optional[int],
        ip_address: str,
        details: Dict[str, Any],
        risk_level: str = "medium"
    ):
        """Log security events for audit trail"""
        logger.warning(
            f"Security Event: {event_type}",
            extra={
                "event_type": event_type,
                "user_id": user_id,
                "ip_address": ip_address,
                "details": details,
                "risk_level": risk_level,
                "timestamp": datetime.utcnow().isoformat(),
                "category": "security_audit"
            }
        )
    
    @staticmethod
    def log_authentication_attempt(
        success: bool,
        username: str,
        ip_address: str,
        user_agent: str
    ):
        """Log authentication attempts"""
        AuditLogger.log_security_event(
            event_type="authentication_attempt",
            user_id=None,
            ip_address=ip_address,
            details={
                "success": success,
                "username": username,
                "user_agent": user_agent
            },
            risk_level="low" if success else "medium"
        )
    
    @staticmethod
    def log_privilege_escalation(
        user_id: int,
        from_role: str,
        to_role: str,
        ip_address: str
    ):
        """Log privilege escalation events"""
        AuditLogger.log_security_event(
            event_type="privilege_escalation",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "from_role": from_role,
                "to_role": to_role
            },
            risk_level="high"
        )

# Initialize global instances
rate_limiter = RateLimiter()
security_middleware = SecurityMiddleware()
audit_logger = AuditLogger()

# Utility functions
def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure token"""
    return secrets.token_urlsafe(length)

def constant_time_compare(a: str, b: str) -> bool:
    """Constant time string comparison to prevent timing attacks"""
    return hmac.compare_digest(a, b)

def hash_sensitive_data(data: str, salt: Optional[str] = None) -> str:
    """Hash sensitive data with optional salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    return hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000).hex()

def validate_request_signature(
    payload: str,
    signature: str,
    secret: str
) -> bool:
    """Validate webhook/API request signature"""
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return constant_time_compare(signature, expected_signature)