"""
Meta (Facebook/Instagram) publishing adapter for Phase 8
Handles Meta Graph API publishing with proper error mapping
"""
import logging
from typing import Tuple, Optional, List
import httpx
from datetime import datetime

from backend.db.models import SocialConnection
from backend.core.encryption import decrypt_token
from backend.services.rate_limit import RetryableError, FatalError
from backend.core.config import get_settings

logger = logging.getLogger(__name__)


class MetaAdapter:
    """Adapter for publishing to Meta platforms (Facebook/Instagram)"""
    
    def __init__(self):
        self.settings = get_settings()
        self.graph_version = getattr(self.settings, 'meta_graph_version', 'v18.0')
        self.base_url = f"https://graph.facebook.com/{self.graph_version}"
    
    async def publish(
        self, 
        connection: SocialConnection, 
        content: str, 
        media_urls: List[str]
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Publish content to Meta platform
        
        Args:
            connection: SocialConnection with Meta tokens
            content: Content text to publish
            media_urls: List of media URLs
            
        Returns:
            Tuple of (success, platform_post_id, error_message)
            
        Raises:
            RetryableError: For 429, 5xx, network errors
            FatalError: For auth failures, policy violations
        """
        try:
            # Validate connection
            if connection.platform != "meta":
                raise FatalError(f"Invalid platform: {connection.platform}")
            
            # Get page access token
            page_token = connection.access_tokens.get("page_token")
            if not page_token:
                raise FatalError("No page access token found")
            
            # Decrypt token (don't log the actual token)
            try:
                decrypted_token = decrypt_token(page_token)
            except Exception as e:
                raise FatalError(f"Failed to decrypt access token: {str(e)}")
            
            # Get page ID from metadata
            page_id = connection.platform_metadata.get("page_id")
            if not page_id:
                raise FatalError("No page ID found in connection metadata")
            
            logger.info(
                f"Publishing to Meta page {page_id} for connection {connection.id}, "
                f"content length: {len(content)}, media count: {len(media_urls)}"
            )
            
            # Prepare request
            url = f"{self.base_url}/{page_id}/feed"
            
            data = {
                "message": content,
                "access_token": decrypted_token
            }
            
            # Add media if provided
            if media_urls:
                # For simplicity, add first media URL as link
                # In production, you'd upload media separately and reference
                data["link"] = media_urls[0]
            
            # Make API request
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.post(url, data=data)
                    
                    # Log request without sensitive data
                    logger.debug(
                        f"Meta API request: POST {url} (token omitted), "
                        f"status: {response.status_code}"
                    )
                    
                    # Handle different response status codes
                    if response.status_code == 200:
                        result = response.json()
                        post_id = result.get("id")
                        
                        if not post_id:
                            raise FatalError("No post ID returned from Meta API")
                        
                        logger.info(f"Successfully published to Meta: {post_id}")
                        return True, post_id, None
                    
                    elif response.status_code == 429:
                        # Rate limiting - should retry
                        error_msg = "Rate limited by Meta API"
                        logger.warning(f"Meta API rate limit: {error_msg}")
                        raise RetryableError(error_msg)
                    
                    elif response.status_code in [500, 502, 503, 504]:
                        # Server errors - should retry
                        error_msg = f"Meta API server error: {response.status_code}"
                        logger.warning(f"Meta API server error: {error_msg}")
                        raise RetryableError(error_msg)
                    
                    elif response.status_code == 401:
                        # Authentication error - fatal
                        error_msg = "Authentication failed - token may be expired"
                        logger.error(f"Meta API auth error: {error_msg}")
                        raise FatalError(error_msg)
                    
                    elif response.status_code == 403:
                        # Permission error - fatal
                        error_msg = "Permission denied - insufficient privileges"
                        logger.error(f"Meta API permission error: {error_msg}")
                        raise FatalError(error_msg)
                    
                    elif response.status_code == 400:
                        # Bad request - check if retryable
                        try:
                            error_data = response.json()
                            error_code = error_data.get("error", {}).get("code")
                            error_message = error_data.get("error", {}).get("message", "Bad request")
                            
                            # Some 400 errors are retryable (temporary issues)
                            retryable_codes = [1, 2, 4, 17, 341]  # Common temporary error codes
                            
                            if error_code in retryable_codes:
                                logger.warning(f"Retryable Meta API error: {error_message}")
                                raise RetryableError(f"Meta API error: {error_message}")
                            else:
                                logger.error(f"Fatal Meta API error: {error_message}")
                                raise FatalError(f"Meta API error: {error_message}")
                                
                        except (ValueError, KeyError):
                            # Can't parse error - assume fatal
                            error_msg = f"Bad request to Meta API: {response.status_code}"
                            logger.error(f"Meta API bad request: {error_msg}")
                            raise FatalError(error_msg)
                    
                    else:
                        # Other HTTP errors - assume retryable
                        error_msg = f"Unexpected Meta API response: {response.status_code}"
                        logger.warning(f"Meta API unexpected response: {error_msg}")
                        raise RetryableError(error_msg)
                        
                except httpx.TimeoutException:
                    error_msg = "Meta API request timeout"
                    logger.warning(f"Meta API timeout: {error_msg}")
                    raise RetryableError(error_msg)
                
                except httpx.NetworkError as e:
                    error_msg = f"Meta API network error: {str(e)}"
                    logger.warning(f"Meta API network error: {error_msg}")
                    raise RetryableError(error_msg)
                
                except httpx.HTTPError as e:
                    error_msg = f"Meta API HTTP error: {str(e)}"
                    logger.warning(f"Meta API HTTP error: {error_msg}")
                    raise RetryableError(error_msg)
            
        except RetryableError:
            # Re-raise retryable errors
            raise
            
        except FatalError:
            # Re-raise fatal errors
            raise
            
        except Exception as e:
            # Unexpected errors - log and treat as retryable
            error_msg = f"Unexpected error in Meta adapter: {str(e)}"
            logger.error(f"Meta adapter unexpected error: {error_msg}")
            raise RetryableError(error_msg)
    
    def validate_connection(self, connection: SocialConnection) -> Tuple[bool, Optional[str]]:
        """
        Validate that connection has required data for publishing
        
        Args:
            connection: SocialConnection to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if connection.platform != "meta":
            return False, f"Invalid platform: {connection.platform}"
        
        if not connection.access_tokens.get("page_token"):
            return False, "No page access token found"
        
        if not connection.platform_metadata.get("page_id"):
            return False, "No page ID found in metadata"
        
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
            "max_content_length": 63206,  # Facebook post limit
            "max_media_count": 10,
            "supported_media_types": ["image/jpeg", "image/png", "video/mp4"],
            "rate_limits": {
                "posts_per_hour": 200,
                "posts_per_day": 1000
            }
        }