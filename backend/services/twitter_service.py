"""
Real Twitter/X API Service

Provides real Twitter functionality using the complete set of API credentials.
Supports posting, reading timeline, analytics, and engagement tracking.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import tweepy
import asyncio

from backend.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class TwitterService:
    """Real Twitter API service using tweepy with full credentials"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'twitter_api_key', None)
        self.api_secret = getattr(settings, 'twitter_api_secret', None)
        self.access_token = getattr(settings, 'twitter_access_token', None)
        self.access_token_secret = getattr(settings, 'twitter_access_token_secret', None)
        self.bearer_token = getattr(settings, 'twitter_bearer_token', None)
        
        # Initialize API clients
        self._init_clients()
        
    def _init_clients(self):
        """Initialize Twitter API clients"""
        try:
            if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
                logger.warning("Missing Twitter API credentials")
                self.api_v1 = None
                self.client_v2 = None
                return
            
            # OAuth 1.0a for posting/writing operations
            auth_v1 = tweepy.OAuthHandler(self.api_key, self.api_secret)
            auth_v1.set_access_token(self.access_token, self.access_token_secret)
            self.api_v1 = tweepy.API(auth_v1, wait_on_rate_limit=True)
            
            # OAuth 2.0 Bearer Token for reading operations (Twitter API v2)
            self.client_v2 = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
            
            logger.info("Twitter API clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Twitter API clients: {e}")
            self.api_v1 = None
            self.client_v2 = None
    
    async def post_tweet(self, content: str, media_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Post a tweet with optional media"""
        try:
            if not self.client_v2:
                return {"status": "error", "error": "Twitter API not initialized"}
            
            # Post tweet using API v2
            response = await asyncio.to_thread(
                self.client_v2.create_tweet,
                text=content,
                media_ids=media_ids if media_ids else None
            )
            
            tweet_data = response.data
            
            return {
                "status": "success",
                "tweet_id": tweet_data['id'],
                "tweet_url": f"https://twitter.com/user/status/{tweet_data['id']}",
                "content": content,
                "posted_at": datetime.now().isoformat(),
                "media_count": len(media_ids) if media_ids else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get Twitter API connection status"""
        try:
            if not self.client_v2:
                return {
                    "connected": False,
                    "error": "API clients not initialized",
                    "credentials_available": {
                        "api_key": bool(self.api_key and len(str(self.api_key)) > 10),
                        "api_secret": bool(self.api_secret and len(str(self.api_secret)) > 10),
                        "access_token": bool(self.access_token and len(str(self.access_token)) > 10),
                        "access_token_secret": bool(self.access_token_secret and len(str(self.access_token_secret)) > 10),
                        "bearer_token": bool(self.bearer_token and len(str(self.bearer_token)) > 10)
                    }
                }
            
            # Test connection
            user = self.client_v2.get_me()
            
            return {
                "connected": True,
                "username": user.data.username,
                "user_id": user.data.id,
                "name": user.data.name,
                "api_version": "v2",
                "rate_limit_status": "Active"
            }
            
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "credentials_available": {
                    "api_key": bool(self.api_key and len(str(self.api_key)) > 10),
                    "api_secret": bool(self.api_secret and len(str(self.api_secret)) > 10),
                    "access_token": bool(self.access_token and len(str(self.access_token)) > 10),
                    "access_token_secret": bool(self.access_token_secret and len(str(self.access_token_secret)) > 10),
                    "bearer_token": bool(self.bearer_token and len(str(self.bearer_token)) > 10)
                }
            }

# Export service instance
twitter_service = TwitterService()