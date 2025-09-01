"""
X (Twitter) publishing adapter for Phase 8
Handles X API v2 publishing with proper error mapping
"""
import logging
from typing import Tuple, Optional, List
import httpx
import base64
from datetime import datetime

from backend.db.models import SocialConnection
from backend.core.encryption import decrypt_token
from backend.services.rate_limit import RetryableError, FatalError
from backend.core.config import get_settings

logger = logging.getLogger(__name__)


class XAdapter:
    """Adapter for publishing to X (Twitter)"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://api.twitter.com/2"
    
    async def publish(
        self, 
        connection: SocialConnection, 
        content: str, 
        media_urls: List[str]
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Publish content to X platform
        
        Args:
            connection: SocialConnection with X tokens
            content: Content text to publish (tweet)
            media_urls: List of media URLs
            
        Returns:
            Tuple of (success, platform_post_id, error_message)
            
        Raises:
            RetryableError: For 429, 5xx, network errors
            FatalError: For auth failures, policy violations
        """
        try:
            # Validate connection
            if connection.platform != "x":
                raise FatalError(f"Invalid platform: {connection.platform}")
            
            # Get access token
            access_token = connection.access_tokens.get("access_token")
            if not access_token:
                raise FatalError("No access token found")
            
            # Decrypt token (don't log the actual token)
            try:
                decrypted_token = decrypt_token(access_token)
            except Exception as e:
                raise FatalError(f"Failed to decrypt access token: {str(e)}")
            
            logger.info(
                f"Publishing to X for connection {connection.id}, "
                f"content length: {len(content)}, media count: {len(media_urls)}"
            )
            
            # Prepare tweet data
            tweet_data = {
                "text": content
            }
            
            # Add media if provided (simplified - in production you'd upload media first)
            if media_urls:
                logger.info(f"Media URLs provided but not implemented: {len(media_urls)} items")
                # Note: X API requires media to be uploaded separately first
                # This would be implemented in production
            
            # Prepare request
            url = f"{self.base_url}/tweets"
            
            headers = {
                "Authorization": f"Bearer {decrypted_token}",
                "Content-Type": "application/json"
            }
            
            # Make API request
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.post(url, json=tweet_data, headers=headers)
                    
                    # Log request without sensitive data
                    logger.debug(
                        f"X API request: POST {url} (token omitted), "
                        f"status: {response.status_code}"
                    )
                    
                    # Handle different response status codes
                    if response.status_code == 201:
                        # Success for tweet creation
                        result = response.json()
                        tweet_id = result.get("data", {}).get("id")
                        
                        if not tweet_id:
                            raise FatalError("No tweet ID returned from X API")
                        
                        logger.info(f"Successfully published to X: {tweet_id}")
                        return True, tweet_id, None
                    
                    elif response.status_code == 429:
                        # Rate limiting - should retry
                        reset_time = response.headers.get("x-rate-limit-reset")
                        error_msg = f"Rate limited by X API (reset: {reset_time})"
                        logger.warning(f"X API rate limit: {error_msg}")
                        raise RetryableError(error_msg)
                    
                    elif response.status_code in [500, 502, 503, 504]:
                        # Server errors - should retry
                        error_msg = f"X API server error: {response.status_code}"
                        logger.warning(f"X API server error: {error_msg}")
                        raise RetryableError(error_msg)
                    
                    elif response.status_code == 401:
                        # Authentication error - fatal
                        error_msg = "Authentication failed - token may be expired or invalid"
                        logger.error(f"X API auth error: {error_msg}")
                        raise FatalError(error_msg)
                    
                    elif response.status_code == 403:
                        # Forbidden - could be permissions or policy violation
                        try:
                            error_data = response.json()
                            error_detail = error_data.get("detail", "Permission denied")
                            
                            # Check for specific error types
                            if "suspended" in error_detail.lower():
                                error_msg = "Account suspended"
                                raise FatalError(error_msg)
                            elif "duplicate" in error_detail.lower():
                                error_msg = "Duplicate tweet detected"
                                raise FatalError(error_msg)
                            else:
                                error_msg = f"Permission denied: {error_detail}"
                                raise FatalError(error_msg)
                                
                        except (ValueError, KeyError):
                            error_msg = "Permission denied by X API"
                            logger.error(f"X API permission error: {error_msg}")
                            raise FatalError(error_msg)
                    
                    elif response.status_code == 400:
                        # Bad request - check if retryable
                        try:
                            error_data = response.json()
                            errors = error_data.get("errors", [])
                            
                            # Check for specific error types
                            for error in errors:
                                error_type = error.get("type", "")
                                
                                # Some errors are retryable (temporary issues)
                                if error_type in ["temporarily_unavailable", "rate_limit_exceeded"]:
                                    error_msg = f"Temporary X API error: {error.get('message', 'Unknown')}"
                                    logger.warning(f"Retryable X API error: {error_msg}")
                                    raise RetryableError(error_msg)
                                else:
                                    # Assume fatal for other errors
                                    error_msg = f"X API error: {error.get('message', 'Bad request')}"
                                    logger.error(f"Fatal X API error: {error_msg}")
                                    raise FatalError(error_msg)
                            
                            # No specific errors found
                            error_msg = "Bad request to X API"
                            raise FatalError(error_msg)
                                
                        except (ValueError, KeyError):
                            # Can't parse error - assume fatal
                            error_msg = f"Bad request to X API: {response.status_code}"
                            logger.error(f"X API bad request: {error_msg}")
                            raise FatalError(error_msg)
                    
                    elif response.status_code == 422:
                        # Unprocessable entity - content issues, usually fatal
                        try:
                            error_data = response.json()
                            error_msg = error_data.get("detail", "Content validation failed")
                            logger.error(f"X API content validation error: {error_msg}")
                            raise FatalError(f"Content validation failed: {error_msg}")
                        except (ValueError, KeyError):
                            error_msg = "Content validation failed"
                            raise FatalError(error_msg)
                    
                    else:
                        # Other HTTP errors - assume retryable
                        error_msg = f"Unexpected X API response: {response.status_code}"
                        logger.warning(f"X API unexpected response: {error_msg}")
                        raise RetryableError(error_msg)
                        
                except httpx.TimeoutException:
                    error_msg = "X API request timeout"
                    logger.warning(f"X API timeout: {error_msg}")
                    raise RetryableError(error_msg)
                
                except httpx.NetworkError as e:
                    error_msg = f"X API network error: {str(e)}"
                    logger.warning(f"X API network error: {error_msg}")
                    raise RetryableError(error_msg)
                
                except httpx.HTTPError as e:
                    error_msg = f"X API HTTP error: {str(e)}"
                    logger.warning(f"X API HTTP error: {error_msg}")
                    raise RetryableError(error_msg)
            
        except RetryableError:
            # Re-raise retryable errors
            raise
            
        except FatalError:
            # Re-raise fatal errors
            raise
            
        except Exception as e:
            # Unexpected errors - log and treat as retryable
            error_msg = f"Unexpected error in X adapter: {str(e)}"
            logger.error(f"X adapter unexpected error: {error_msg}")
            raise RetryableError(error_msg)
    
    def validate_connection(self, connection: SocialConnection) -> Tuple[bool, Optional[str]]:
        """
        Validate that connection has required data for publishing
        
        Args:
            connection: SocialConnection to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if connection.platform != "x":
            return False, f"Invalid platform: {connection.platform}"
        
        if not connection.access_tokens.get("access_token"):
            return False, "No access token found"
        
        if not connection.is_active:
            return False, "Connection is not active"
        
        if connection.revoked_at:
            return False, "Connection has been revoked"
        
        return True, None
    
    def get_platform_limits(self) -> dict:
        """
        Get platform-specific limits
        
        Returns:
            Dictionary with platform limits
        """
        return {
            "max_content_length": 280,  # Twitter character limit
            "max_media_count": 4,
            "supported_media_types": ["image/jpeg", "image/png", "image/gif", "video/mp4"],
            "rate_limits": {
                "posts_per_15min": 300,  # X API v2 limit
                "posts_per_day": 2400
            }
        }
    
    async def upload_media(
        self, 
        connection: SocialConnection, 
        media_url: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload media to X platform (placeholder implementation)
        
        Args:
            connection: SocialConnection with X tokens
            media_url: URL of media to upload
            
        Returns:
            Tuple of (success, media_id, error_message)
        """
        # This would be implemented in production to upload media
        # using the X API media upload endpoints
        logger.info(f"Media upload not implemented for URL: {media_url}")
        return False, None, "Media upload not implemented"