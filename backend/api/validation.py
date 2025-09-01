"""
API validation utilities and common validators
Enhanced with security features and comprehensive input validation
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator
from datetime import datetime, date
from fastapi import HTTPException, status, Request
import re
import html
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    pass

class APIResponse(BaseModel):
    """Standard API response format"""
    status: str = "success"
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    page: int = 1
    limit: int = 50
    offset: Optional[int] = None
    
    @field_validator('page')
    @classmethod
    def page_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('Page must be positive')
        return v
    
    @field_validator('limit')
    @classmethod
    def limit_must_be_reasonable(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Limit must be between 1 and 100')
        return v
    
    def get_offset(self) -> int:
        """Calculate offset from page and limit"""
        if self.offset is not None:
            return self.offset
        return (self.page - 1) * self.limit

class DateRangeParams(BaseModel):
    """Standard date range parameters"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days: Optional[int] = None
    
    @field_validator('end_date')
    @classmethod
    def end_date_after_start(cls, v, info):
        if v and info.data.get('start_date') and v < info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @field_validator('days')
    @classmethod  
    def days_must_be_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError('Days must be positive')
        return v

def validate_platform(platform: str) -> str:
    """Validate social media platform"""
    valid_platforms = ['twitter', 'instagram', 'facebook', 'tiktok', 'youtube']
    if platform.lower() not in valid_platforms:
        raise ValidationError(f"Invalid platform. Must be one of: {', '.join(valid_platforms)}")
    return platform.lower()

def validate_content_type(content_type: str) -> str:
    """Validate content type"""
    valid_types = ['text', 'image', 'video', 'carousel', 'story', 'reel']
    if content_type.lower() not in valid_types:
        raise ValidationError(f"Invalid content type. Must be one of: {', '.join(valid_types)}")
    return content_type.lower()

def validate_goal_type(goal_type: str) -> str:
    """Validate goal type"""
    valid_types = ['follower_growth', 'engagement_rate', 'reach_increase', 'content_volume', 'custom']
    if goal_type.lower() not in valid_types:
        raise ValidationError(f"Invalid goal type. Must be one of: {', '.join(valid_types)}")
    return goal_type.lower()

def validate_workflow_type(workflow_type: str) -> str:
    """Validate workflow type"""
    valid_types = ['daily', 'optimization', 'manual', 'research', 'content_generation']
    if workflow_type.lower() not in valid_types:
        raise ValidationError(f"Invalid workflow type. Must be one of: {', '.join(valid_types)}")
    return workflow_type.lower()

def sanitize_text(text: str, max_length: int = 10000) -> str:
    """Sanitize text input"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    sanitized = ' '.join(text.split())
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized

def validate_text_length(text: str, min_length: int = 1, max_length: int = 10000) -> str:
    """Validate text length"""
    if not text:
        raise ValidationError(f"Text is required (minimum {min_length} characters)")
    
    text = text.strip()
    if len(text) < min_length:
        raise ValidationError(f"Text must be at least {min_length} characters long")
    
    if len(text) > max_length:
        raise ValidationError(f"Text must not exceed {max_length} characters")
    
    return text

def clean_text_input(text: str, max_length: int = 10000) -> str:
    """Clean and sanitize text input"""
    if not text:
        return ""
    
    # Remove control characters and normalize whitespace
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    text = ' '.join(text.split())
    
    # HTML escape for safety
    text = html.escape(text)
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()

def validate_tags(tags: List[str]) -> List[str]:
    """Validate and sanitize tags"""
    if not tags:
        return []
    
    validated_tags = []
    for tag in tags:
        # Remove whitespace and convert to lowercase
        clean_tag = tag.strip().lower()
        
        # Skip empty tags
        if not clean_tag:
            continue
        
        # Validate tag format (alphanumeric and underscores only)
        if not clean_tag.replace('_', '').replace('-', '').isalnum():
            continue
        
        # Limit tag length
        if len(clean_tag) > 50:
            clean_tag = clean_tag[:50]
        
        validated_tags.append(clean_tag)
    
    # Remove duplicates and limit total number
    return list(set(validated_tags))[:20]

def validate_engagement_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate engagement data structure"""
    if not data:
        return {}
    
    # Define expected fields and their types
    expected_fields = {
        'likes': int,
        'comments': int,
        'shares': int,
        'views': int,
        'clicks': int,
        'saves': int,
        'impressions': int,
        'reach': int
    }
    
    validated_data = {}
    for field, field_type in expected_fields.items():
        if field in data:
            try:
                value = field_type(data[field])
                if value >= 0:  # Ensure non-negative
                    validated_data[field] = value
            except (ValueError, TypeError):
                continue  # Skip invalid values
    
    return validated_data

def create_error_response(message: str, errors: List[str] = None) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "status": "error",
        "message": message,
        "errors": errors or [],
        "data": None
    }

def create_success_response(data: Any = None, message: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create standardized success response"""
    return {
        "status": "success",
        "message": message,
        "data": data,
        "metadata": metadata
    }

def validate_json_field(data: Any, max_size_kb: int = 100) -> Dict[str, Any]:
    """Validate JSON field size and structure"""
    if not data:
        return {}
    
    if not isinstance(data, dict):
        raise ValidationError("JSON field must be a dictionary")
    
    # Check size
    import json
    json_str = json.dumps(data)
    size_kb = len(json_str.encode('utf-8')) / 1024
    
    if size_kb > max_size_kb:
        raise ValidationError(f"JSON field too large. Maximum size: {max_size_kb}KB")
    
    return data

# Common HTTP exception handlers
def validation_exception_handler(error: ValidationError) -> HTTPException:
    """Convert validation error to HTTP exception"""
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(error)
    )

def not_found_exception(resource: str, resource_id: Any = None) -> HTTPException:
    """Create not found exception"""
    message = f"{resource} not found"
    if resource_id:
        message += f" (ID: {resource_id})"
    
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=message
    )

def forbidden_exception(message: str = "Access forbidden") -> HTTPException:
    """Create forbidden exception"""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message
    )

def bad_request_exception(message: str) -> HTTPException:
    """Create bad request exception"""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message
    )

# Enhanced Security Validation Features

class RequestSizeValidator:
    """Validate request size limits"""
    
    @staticmethod
    def validate_request_size(request: Request, max_size_mb: int = 10):
        """Validate request size"""
        content_length = request.headers.get('content-length')
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > max_size_mb:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Request too large. Maximum size: {max_size_mb}MB"
                )

class SQLInjectionValidator:
    """Validate against SQL injection patterns"""
    
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\'\s*(OR|AND)\s*\'\w*\'\s*=\s*\'\w*\')",
        r"(\bUNION\s+SELECT\b)",
        r"(\bEXEC\s*\()",
    ]
    
    @classmethod
    def validate_sql_injection(cls, text: str) -> str:
        """Validate text for SQL injection patterns"""
        if not text:
            return text
            
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Potential SQL injection attempt detected: {pattern}")
                raise ValidationError("Invalid input detected")
        
        return text

class XSSValidator:
    """Validate against XSS attacks"""
    
    @staticmethod
    def sanitize_html(text: str, allowed_tags: List[str] = None) -> str:
        """Sanitize HTML to prevent XSS"""
        if not text:
            return text
        
        # Default: escape all HTML
        if allowed_tags is None or len(allowed_tags) == 0:
            return html.escape(text)
        
        # For basic HTML sanitization without bleach
        # Remove script tags and dangerous attributes
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
            r'on\w+\s*=\s*["\'][^"\']*["\']',
            r'javascript:',
            r'vbscript:',
            r'data:text/html'
        ]
        
        cleaned = text
        for pattern in dangerous_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        
        return cleaned

class InputValidator:
    """Comprehensive input validation"""
    
    @staticmethod
    def validate_text_input(
        text: str,
        min_length: int = 0,
        max_length: int = 10000,
        allow_html: bool = False,
        check_sql_injection: bool = True
    ) -> str:
        """Comprehensive text input validation"""
        if not text and min_length > 0:
            raise ValidationError(f"Text must be at least {min_length} characters")
        
        if len(text) > max_length:
            raise ValidationError(f"Text must be at most {max_length} characters")
        
        # SQL injection check
        if check_sql_injection:
            SQLInjectionValidator.validate_sql_injection(text)
        
        # HTML sanitization
        if not allow_html:
            text = XSSValidator.sanitize_html(text, allowed_tags=[])
        
        return text.strip()
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format"""
        if not email:
            raise ValidationError("Email is required")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format")
        
        return email.lower().strip()
    
    @staticmethod
    def validate_url(url: str, allow_local: bool = False) -> str:
        """Validate URL format"""
        if not url:
            raise ValidationError("URL is required")
        
        # Basic URL pattern
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url):
            raise ValidationError("Invalid URL format")
        
        # Check for local URLs if not allowed
        if not allow_local:
            local_patterns = [
                r'localhost',
                r'127\.0\.0\.1',
                r'0\.0\.0\.0',
                r'10\.\d+\.\d+\.\d+',
                r'192\.168\.\d+\.\d+',
                r'172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+'
            ]
            
            for pattern in local_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    raise ValidationError("Local URLs not allowed")
        
        return url.strip()
    
    @staticmethod
    def validate_username(username: str) -> str:
        """Validate username format"""
        if not username:
            raise ValidationError("Username is required")
        
        if len(username) < 3 or len(username) > 30:
            raise ValidationError("Username must be between 3 and 30 characters")
        
        # Only alphanumeric characters, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError("Username can only contain letters, numbers, underscores, and hyphens")
        
        return username.lower().strip()

class RateLimitValidator:
    """Rate limiting validation helpers"""
    
    @staticmethod
    def check_rate_limit_headers(request: Request) -> Dict[str, Any]:
        """Extract rate limiting information from request"""
        return {
            'client_ip': request.client.host if request.client else None,
            'user_agent': request.headers.get('user-agent'),
            'referer': request.headers.get('referer'),
            'forwarded_for': request.headers.get('x-forwarded-for'),
            'real_ip': request.headers.get('x-real-ip')
        }

# Enhanced validation functions
def validate_api_key(api_key: str) -> str:
    """Validate API key format"""
    if not api_key:
        raise ValidationError("API key is required")
    
    # Basic API key format validation
    if not re.match(r'^[a-zA-Z0-9]{32,128}$', api_key):
        raise ValidationError("Invalid API key format")
    
    return api_key

def validate_file_upload(file_content: bytes, max_size_mb: int = 10, allowed_types: List[str] = None) -> bool:
    """Validate file upload with comprehensive file type checking"""
    if not file_content:
        raise ValidationError("File content is required")
    
    # Check file size
    size_mb = len(file_content) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValidationError(f"File too large. Maximum size: {max_size_mb}MB")
    
    # File type validation using magic bytes detection
    if allowed_types:
        detected_type = _detect_file_type(file_content)
        if detected_type not in allowed_types:
            raise ValidationError(f"File type '{detected_type}' not allowed. Allowed types: {', '.join(allowed_types)}")
        
        # Additional security checks for dangerous file types
        _validate_file_security(file_content, detected_type)
    
    return True

def _detect_file_type(file_content: bytes) -> str:
    """Detect file type using magic bytes (file signatures)"""
    if len(file_content) < 16:
        return "unknown"
    
    # Define magic bytes for common file types
    magic_bytes_map = {
        # Images
        b'\xFF\xD8\xFF': 'jpeg',
        b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A': 'png',
        b'GIF87a': 'gif',
        b'GIF89a': 'gif',
        b'RIFF': 'webp',  # WebP files start with RIFF
        b'BM': 'bmp',
        b'\x00\x00\x01\x00': 'ico',
        b'II*\x00': 'tiff',
        b'MM\x00*': 'tiff',
        
        # Documents
        b'%PDF': 'pdf',
        b'\x50\x4B\x03\x04': 'zip',  # Also covers docx, xlsx, pptx
        b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1': 'doc',  # MS Office legacy
        b'{\\rtf': 'rtf',
        
        # Video/Audio
        b'\x00\x00\x00\x20\x66\x74\x79\x70': 'mp4',
        b'\x00\x00\x00\x18\x66\x74\x79\x70': 'mp4',
        b'ID3': 'mp3',
        b'\xFF\xFB': 'mp3',
        b'OggS': 'ogg',
        b'RIFF': 'avi',  # AVI also uses RIFF
        
        # Executables and dangerous files
        b'MZ': 'exe',
        b'\x7FELF': 'elf',
        b'\xFE\xED\xFA\xCE': 'macho',
        b'\xFE\xED\xFA\xCF': 'macho',
        b'\xCF\xFA\xED\xFE': 'macho',
        b'\xCA\xFE\xBA\xBE': 'java_class',
        b'\xCA\xFE\xD0\x0D': 'java_class',
    }
    
    # Check magic bytes
    for magic, file_type in magic_bytes_map.items():
        if file_content.startswith(magic):
            # Special handling for WebP vs AVI (both use RIFF)
            if magic == b'RIFF':
                if len(file_content) > 12 and file_content[8:12] == b'WEBP':
                    return 'webp'
                elif len(file_content) > 12 and file_content[8:12] == b'AVI ':
                    return 'avi'
            return file_type
    
    # Check for text-based files
    try:
        text_content = file_content[:1024].decode('utf-8', errors='strict')
        if text_content.strip().startswith('<?xml'):
            return 'xml'
        elif text_content.strip().startswith('<html'):
            return 'html'
        elif text_content.strip().startswith('{') or text_content.strip().startswith('['):
            return 'json'
        elif text_content.strip().startswith('<!DOCTYPE html'):
            return 'html'
        return 'text'
    except UnicodeDecodeError:
        pass
    
    return "unknown"

def _validate_file_security(file_content: bytes, file_type: str) -> None:
    """Additional security validation for file content"""
    
    # Block dangerous file types completely
    dangerous_types = [
        'exe', 'bat', 'cmd', 'com', 'scr', 'pif', 'vbs', 'js', 'jar',
        'elf', 'macho', 'java_class', 'msi', 'dll', 'so', 'dylib'
    ]
    
    if file_type in dangerous_types:
        raise ValidationError(f"File type '{file_type}' is not allowed for security reasons")
    
    # Check for embedded executables in archives
    if file_type == 'zip':
        _validate_zip_security(file_content)
    
    # Check for malicious patterns in document files
    if file_type in ['pdf', 'doc', 'docx']:
        _validate_document_security(file_content, file_type)
    
    # Check for script injections in image files
    if file_type in ['jpeg', 'png', 'gif', 'webp']:
        _validate_image_security(file_content)

def _validate_zip_security(file_content: bytes) -> None:
    """Validate ZIP files for security threats"""
    try:
        import zipfile
        import io
        
        # Check for zip bombs and path traversal
        zip_buffer = io.BytesIO(file_content)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            total_size = 0
            for file_info in zip_file.filelist:
                # Check for path traversal attempts
                if '..' in file_info.filename or file_info.filename.startswith('/'):
                    raise ValidationError("Archive contains unsafe file paths")
                
                # Check for zip bombs (excessive compression ratio)
                total_size += file_info.file_size
                if total_size > 100 * 1024 * 1024:  # 100MB uncompressed limit
                    raise ValidationError("Archive too large when uncompressed")
                
                # Check for dangerous file extensions in archive
                dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.js', '.vbs', '.jar']
                if any(file_info.filename.lower().endswith(ext) for ext in dangerous_extensions):
                    raise ValidationError("Archive contains executable files")
                    
    except zipfile.BadZipFile:
        raise ValidationError("Invalid or corrupted ZIP file")
    except Exception as e:
        logger.warning(f"ZIP validation error: {e}")
        raise ValidationError("Unable to validate ZIP file security")

def _validate_document_security(file_content: bytes, file_type: str) -> None:
    """Validate documents for embedded scripts and macros"""
    
    # Check for common malicious patterns
    malicious_patterns = [
        b'javascript:',
        b'vbscript:',
        b'<script',
        b'eval(',
        b'exec(',
        b'system(',
        b'shell(',
        b'ActiveXObject',
        b'WScript.Shell',
        b'CreateObject'
    ]
    
    content_lower = file_content.lower()
    for pattern in malicious_patterns:
        if pattern in content_lower:
            raise ValidationError("Document contains potentially malicious content")
    
    # PDF-specific checks
    if file_type == 'pdf':
        if b'/JavaScript' in file_content or b'/JS' in file_content:
            raise ValidationError("PDF contains JavaScript which is not allowed")
        if b'/Launch' in file_content or b'/EmbeddedFile' in file_content:
            raise ValidationError("PDF contains embedded files or launch actions")

def _validate_image_security(file_content: bytes) -> None:
    """Validate images for embedded scripts and metadata exploits"""
    
    # Check for script injections in image metadata
    script_patterns = [
        b'<script',
        b'javascript:',
        b'vbscript:',
        b'onload=',
        b'onerror=',
        b'eval(',
        b'document.',
        b'window.'
    ]
    
    content_lower = file_content.lower()
    for pattern in script_patterns:
        if pattern in content_lower:
            raise ValidationError("Image contains embedded scripts or malicious content")
    
    # Check for excessive metadata size (potential exploit)
    if len(file_content) > 50 * 1024 * 1024:  # 50MB limit for images
        raise ValidationError("Image file suspiciously large, may contain hidden content")

# Predefined safe file type lists
SAFE_IMAGE_TYPES = ['jpeg', 'jpg', 'png', 'gif', 'webp', 'bmp']
SAFE_DOCUMENT_TYPES = ['pdf', 'txt', 'rtf']
SAFE_MEDIA_TYPES = ['mp3', 'mp4', 'ogg', 'wav']

def create_validation_middleware():
    """Create validation middleware for FastAPI"""
    async def validation_middleware(request: Request, call_next):
        try:
            # Validate request size
            RequestSizeValidator.validate_request_size(request)
            
            # Log rate limiting info for monitoring
            rate_limit_info = RateLimitValidator.check_rate_limit_headers(request)
            logger.debug(f"Request validation: {rate_limit_info}")
            
            response = await call_next(request)
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Validation middleware error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal validation error"
            )
    
    return validation_middleware