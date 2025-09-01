"""
X (Twitter) mentions polling service
Handles polling for mentions with since_id tracking, deduplication, and backoff
"""
import logging
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Set
import httpx

from backend.core.config import get_settings
from backend.core.encryption import decrypt_token
from backend.db.models import SocialConnection
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class XMentionsService:
    """Service for polling X mentions with rate limiting and deduplication"""
    
    def __init__(self, settings=None):
        """
        Initialize X mentions service
        
        Args:
            settings: Application settings (will get from config if not provided)
        """
        self.settings = settings or get_settings()
        self.base_url = "https://api.twitter.com/2"
        
        # Rate limiting and backoff configuration
        self.max_results = 100
        self.base_backoff_seconds = 60  # Start with 1 minute
        self.max_backoff_seconds = 3600  # Max 1 hour
        self.backoff_multiplier = 2
        self.jitter_max_seconds = 30
        
        # Track processed tweet IDs to avoid duplicates within session
        self._processed_tweet_ids: Set[str] = set()
    
    async def poll_mentions(self, connection: SocialConnection, db: Session) -> Dict[str, Any]:
        """
        Poll X mentions for a connection with since_id tracking and deduplication
        
        Args:
            connection: SocialConnection instance for X platform
            db: Database session
            
        Returns:
            Dictionary with polling results and statistics
        """
        try:
            logger.info(f"Starting X mentions poll for connection {connection.id}")
            
            # Get decrypted access token
            encrypted_token = connection.access_tokens.get("access_token")
            if not encrypted_token:
                return {"success": False, "error": "No access token found"}
            
            access_token = decrypt_token(encrypted_token)
            user_id = connection.platform_account_id
            
            # Get since_id from connection metadata
            since_id = connection.platform_metadata.get("mentions_since_id") if connection.platform_metadata else None
            
            # Poll mentions from X API
            try:
                mentions_data = await self._fetch_mentions(user_id, access_token, since_id)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limited - calculate backoff
                    backoff_seconds = self._calculate_rate_limit_backoff(e.response)
                    logger.warning(f"Rate limited on connection {connection.id}, backoff: {backoff_seconds}s")
                    return {
                        "success": False,
                        "error": "rate_limited",
                        "backoff_seconds": backoff_seconds,
                        "retry_after": datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
                    }
                else:
                    # Other HTTP error
                    logger.error(f"HTTP error polling mentions: {e.response.status_code} - {e.response.text}")
                    return {"success": False, "error": f"HTTP {e.response.status_code}"}
            
            except Exception as e:
                logger.error(f"Error fetching mentions for connection {connection.id}: {e}")
                return {"success": False, "error": str(e)}
            
            # Process mentions data
            tweets = mentions_data.get("data", [])
            new_mentions_count = 0
            processed_ids = []
            new_since_id = since_id
            
            if tweets:
                # Sort by ID to process in chronological order
                tweets.sort(key=lambda t: int(t["id"]))
                
                for tweet in tweets:
                    tweet_id = tweet["id"]
                    
                    # Skip if already processed in this session
                    if tweet_id in self._processed_tweet_ids:
                        logger.debug(f"Skipping duplicate tweet {tweet_id} in session")
                        continue
                    
                    # Process the mention
                    try:
                        await self._process_mention(tweet, connection)
                        processed_ids.append(tweet_id)
                        self._processed_tweet_ids.add(tweet_id)
                        new_mentions_count += 1
                        
                        # Update since_id to the highest processed ID
                        new_since_id = max(new_since_id or "0", tweet_id, key=int)
                        
                    except Exception as e:
                        logger.error(f"Error processing mention {tweet_id}: {e}")
                        # Don't update since_id if processing fails
                        continue
            
            # Only update since_id if we successfully processed at least one mention
            # or if we got a successful API response (even if no new mentions)
            if new_since_id != since_id:
                await self._update_since_id(connection, db, new_since_id)
                logger.info(f"Updated since_id for connection {connection.id}: {since_id} -> {new_since_id}")
            
            # Update last checked timestamp
            connection.last_checked_at = datetime.now(timezone.utc)
            db.commit()
            
            result = {
                "success": True,
                "new_mentions": new_mentions_count,
                "processed_ids": processed_ids,
                "since_id": new_since_id,
                "total_fetched": len(tweets)
            }
            
            logger.info(f"X mentions poll completed for connection {connection.id}: {result}")
            return result
            
        except Exception as e:
            error_msg = f"X mentions polling failed: {str(e)}"
            logger.error(f"X mentions poll error for connection {connection.id}: {error_msg}")
            return {"success": False, "error": error_msg}
    
    async def _fetch_mentions(self, user_id: str, access_token: str, since_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch mentions from X API
        
        Args:
            user_id: X user ID to fetch mentions for
            access_token: Bearer token for authentication
            since_id: Optional since_id parameter for pagination
            
        Returns:
            API response data
        """
        url = f"{self.base_url}/users/{user_id}/mentions"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "max_results": self.max_results,
            "tweet.fields": "author_id,created_at,conversation_id,public_metrics,context_annotations"
        }
        
        if since_id:
            params["since_id"] = since_id
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json()
    
    async def _process_mention(self, tweet: Dict[str, Any], connection: SocialConnection) -> None:
        """
        Process a single mention tweet
        
        This is a stub that can be extended to handle actual mention processing
        (e.g., enqueue for reply generation, sentiment analysis, etc.)
        
        Args:
            tweet: Tweet data from X API
            connection: SocialConnection instance
        """
        try:
            tweet_id = tweet["id"]
            author_id = tweet.get("author_id")
            text = tweet.get("text", "")
            created_at = tweet.get("created_at")
            
            # Log the mention for monitoring
            logger.info(
                f"Processing mention {tweet_id} for connection {connection.id}: "
                f"author={author_id}, created_at={created_at}"
            )
            
            # TODO: Add actual mention processing logic here
            # Examples:
            # - Enqueue for AI reply generation
            # - Store in database for review
            # - Trigger notifications
            # - Perform sentiment analysis
            # - Extract mentioned topics/entities
            
            # For now, just log that we processed it
            logger.debug(f"Mention processed: {tweet_id} - '{text[:100]}'...")
            
        except Exception as e:
            logger.error(f"Error in mention processing: {e}")
            raise
    
    def _calculate_rate_limit_backoff(self, response: httpx.Response) -> int:
        """
        Calculate backoff time for rate limiting
        
        Args:
            response: HTTP response with rate limit headers
            
        Returns:
            Backoff time in seconds
        """
        try:
            # Try to get rate limit reset time from headers
            reset_time = response.headers.get("x-rate-limit-reset")
            if reset_time:
                reset_timestamp = int(reset_time)
                current_timestamp = int(time.time())
                backoff_seconds = max(0, reset_timestamp - current_timestamp)
                
                # Add jitter to avoid thundering herd
                jitter = random.randint(1, self.jitter_max_seconds)
                backoff_seconds += jitter
                
                # Cap the backoff time
                backoff_seconds = min(backoff_seconds, self.max_backoff_seconds)
                
                return backoff_seconds
        except Exception as e:
            logger.warning(f"Error calculating rate limit backoff from headers: {e}")
        
        # Fallback to exponential backoff if headers not available
        # Use a simple exponential backoff with jitter
        backoff_seconds = self.base_backoff_seconds
        jitter = random.randint(1, self.jitter_max_seconds)
        total_backoff = min(backoff_seconds + jitter, self.max_backoff_seconds)
        
        return total_backoff
    
    async def _update_since_id(self, connection: SocialConnection, db: Session, new_since_id: str) -> None:
        """
        Update the since_id in connection metadata
        
        Args:
            connection: SocialConnection instance
            db: Database session
            new_since_id: New since_id value to store
        """
        try:
            # Initialize platform_metadata if it doesn't exist
            if not connection.platform_metadata:
                connection.platform_metadata = {}
            
            # Update the mentions since_id
            connection.platform_metadata["mentions_since_id"] = new_since_id
            
            # Mark the field as modified for SQLAlchemy to detect changes
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(connection, "platform_metadata")
            
            db.commit()
            db.refresh(connection)
            
        except Exception as e:
            logger.error(f"Error updating since_id: {e}")
            raise
    
    def reset_session_cache(self) -> None:
        """Reset the session-level processed tweet IDs cache"""
        self._processed_tweet_ids.clear()
        logger.debug("Reset X mentions service session cache")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about the current session"""
        return {
            "processed_tweet_ids_count": len(self._processed_tweet_ids),
            "session_start_time": datetime.now(timezone.utc).isoformat()
        }


# Singleton instance
_x_mentions_service = None


def get_x_mentions_service(settings=None) -> XMentionsService:
    """
    Get X mentions service instance
    
    Args:
        settings: Application settings (optional)
        
    Returns:
        XMentionsService instance
    """
    global _x_mentions_service
    
    if _x_mentions_service is None:
        _x_mentions_service = XMentionsService(settings)
    
    return _x_mentions_service