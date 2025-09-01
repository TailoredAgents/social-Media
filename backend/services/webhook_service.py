"""
Webhook Service for Real-Time Platform Updates
Handles incoming webhooks from social media platforms for instant cache invalidation and updates
"""
import asyncio
import hmac
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from enum import Enum
from fastapi import HTTPException, Request

from backend.services.redis_cache import redis_cache
from backend.services.cache_decorators import cache_manager
from backend.db.database_optimized import get_db_connection
from backend.db.models import ContentItem, User, ContentPerformanceSnapshot

logger = logging.getLogger(__name__)

class WebhookEventType(Enum):
    """Types of webhook events"""
    POST_PUBLISHED = "post_published"
    POST_UPDATED = "post_updated"
    POST_DELETED = "post_deleted"
    ENGAGEMENT_UPDATE = "engagement_update"
    PROFILE_UPDATED = "profile_updated"
    METRICS_UPDATE = "metrics_update"
    FOLLOWER_UPDATE = "follower_update"
    COMMENT_ADDED = "comment_added"
    LIKE_ADDED = "like_added"
    SHARE_ADDED = "share_added"

@dataclass
class WebhookEvent:
    """Webhook event data structure"""
    platform: str
    event_type: WebhookEventType
    user_id: Optional[int]
    resource_id: str
    data: Dict[str, Any]
    timestamp: datetime
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'platform': self.platform,
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'resource_id': self.resource_id,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'signature': self.signature
        }

class WebhookProcessor:
    """
    Process webhooks from social media platforms
    """
    
    def __init__(self):
        self.event_handlers = {}
        self.platform_secrets = {
            'twitter': None,  # Set from environment
            'facebook': None,
            'instagram': None,
            'linkedin': None,
            'tiktok': None
        }
        
        # Register default event handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default webhook event handlers"""
        self.register_handler(WebhookEventType.POST_PUBLISHED, self._handle_post_published)
        self.register_handler(WebhookEventType.POST_UPDATED, self._handle_post_updated)
        self.register_handler(WebhookEventType.POST_DELETED, self._handle_post_deleted)
        self.register_handler(WebhookEventType.ENGAGEMENT_UPDATE, self._handle_engagement_update)
        self.register_handler(WebhookEventType.PROFILE_UPDATED, self._handle_profile_updated)
        self.register_handler(WebhookEventType.METRICS_UPDATE, self._handle_metrics_update)
    
    def register_handler(self, event_type: WebhookEventType, handler: Callable):
        """Register a webhook event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type.value}")
    
    def verify_webhook_signature(self, platform: str, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature for security
        
        Args:
            platform: Social media platform
            payload: Raw webhook payload
            signature: Signature from platform
            
        Returns:
            True if signature is valid
        """
        secret = self.platform_secrets.get(platform)
        if not secret:
            logger.warning(f"No webhook secret configured for {platform}")
            return True  # Allow through if no secret configured (dev mode)
        
        try:
            if platform == 'twitter':
                # Twitter uses HMAC-SHA256
                expected_signature = hmac.new(
                    secret.encode(),
                    payload,
                    hashlib.sha256
                ).hexdigest()
                return hmac.compare_digest(f"sha256={expected_signature}", signature)
            
            elif platform == 'facebook' or platform == 'instagram':
                # Facebook/Instagram use HMAC-SHA1
                expected_signature = hmac.new(
                    secret.encode(),
                    payload,
                    hashlib.sha1
                ).hexdigest()
                return hmac.compare_digest(f"sha1={expected_signature}", signature)
            
            elif platform == 'linkedin':
                # LinkedIn uses HMAC-SHA256
                expected_signature = hmac.new(
                    secret.encode(),
                    payload,
                    hashlib.sha256
                ).hexdigest()
                return hmac.compare_digest(expected_signature, signature)
            
            else:
                logger.warning(f"Unknown signature verification for platform: {platform}")
                return True
                
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
    
    async def process_webhook(self, platform: str, payload: Dict[str, Any], signature: Optional[str] = None) -> Dict[str, Any]:
        """
        Process incoming webhook
        
        Args:
            platform: Source platform
            payload: Webhook payload
            signature: Webhook signature for verification
            
        Returns:
            Processing result
        """
        try:
            # Parse webhook event
            event = self._parse_webhook_event(platform, payload)
            
            if not event:
                return {'status': 'ignored', 'reason': 'Unable to parse event'}
            
            # Log webhook event
            logger.info(f"Processing webhook: {platform} {event.event_type.value} for user {event.user_id}")
            
            # Store webhook event for debugging/analytics
            await self._store_webhook_event(event)
            
            # Process event with registered handlers
            results = []
            handlers = self.event_handlers.get(event.event_type, [])
            
            for handler in handlers:
                try:
                    result = await handler(event)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Handler error for {event.event_type.value}: {e}")
                    results.append({'status': 'error', 'error': str(e)})
            
            return {
                'status': 'processed',
                'event_type': event.event_type.value,
                'platform': platform,
                'handlers_executed': len(handlers),
                'results': results,
                'processed_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _parse_webhook_event(self, platform: str, payload: Dict[str, Any]) -> Optional[WebhookEvent]:
        """Parse platform-specific webhook payload into standardized event"""
        try:
            if platform == 'twitter':
                return self._parse_twitter_webhook(payload)
            elif platform == 'facebook':
                return self._parse_facebook_webhook(payload)
            elif platform == 'instagram':
                return self._parse_instagram_webhook(payload)
            elif platform == 'linkedin':
                return self._parse_linkedin_webhook(payload)
            elif platform == 'tiktok':
                return self._parse_tiktok_webhook(payload)
            else:
                logger.warning(f"Unknown webhook platform: {platform}")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing {platform} webhook: {e}")
            return None
    
    def _parse_twitter_webhook(self, payload: Dict[str, Any]) -> Optional[WebhookEvent]:
        """Parse Twitter webhook payload"""
        # Twitter webhook format varies by event type
        if 'tweet_create_events' in payload:
            tweet = payload['tweet_create_events'][0]
            return WebhookEvent(
                platform='twitter',
                event_type=WebhookEventType.POST_PUBLISHED,
                user_id=None,  # Would need to map from Twitter user ID
                resource_id=tweet['id'],
                data=tweet,
                timestamp=datetime.now(timezone.utc)
            )
        
        elif 'tweet_delete_events' in payload:
            delete_event = payload['tweet_delete_events'][0]
            return WebhookEvent(
                platform='twitter',
                event_type=WebhookEventType.POST_DELETED,
                user_id=None,
                resource_id=delete_event['status']['id'],
                data=delete_event,
                timestamp=datetime.now(timezone.utc)
            )
        
        # Add more Twitter event types as needed
        return None
    
    def _parse_facebook_webhook(self, payload: Dict[str, Any]) -> Optional[WebhookEvent]:
        """Parse Facebook webhook payload"""
        if 'entry' in payload:
            entry = payload['entry'][0]
            if 'changes' in entry:
                change = entry['changes'][0]
                
                if change['field'] == 'feed':
                    value = change['value']
                    
                    if value.get('verb') == 'add':
                        return WebhookEvent(
                            platform='facebook',
                            event_type=WebhookEventType.POST_PUBLISHED,
                            user_id=None,
                            resource_id=value['post_id'],
                            data=value,
                            timestamp=datetime.now(timezone.utc)
                        )
                    
                    elif value.get('verb') == 'remove':
                        return WebhookEvent(
                            platform='facebook',
                            event_type=WebhookEventType.POST_DELETED,
                            user_id=None,
                            resource_id=value['post_id'],
                            data=value,
                            timestamp=datetime.now(timezone.utc)
                        )
        
        return None
    
    def _parse_instagram_webhook(self, payload: Dict[str, Any]) -> Optional[WebhookEvent]:
        """Parse Instagram webhook payload"""
        # Instagram webhooks are similar to Facebook
        return self._parse_facebook_webhook(payload)
    
    def _parse_linkedin_webhook(self, payload: Dict[str, Any]) -> Optional[WebhookEvent]:
        """Parse LinkedIn webhook payload"""
        if 'eventType' in payload:
            event_type_map = {
                'SHARE_CREATED': WebhookEventType.POST_PUBLISHED,
                'SHARE_UPDATED': WebhookEventType.POST_UPDATED,
                'SHARE_DELETED': WebhookEventType.POST_DELETED,
                'PROFILE_UPDATED': WebhookEventType.PROFILE_UPDATED
            }
            
            linkedin_event_type = payload['eventType']
            mapped_event_type = event_type_map.get(linkedin_event_type)
            
            if mapped_event_type:
                return WebhookEvent(
                    platform='linkedin',
                    event_type=mapped_event_type,
                    user_id=None,
                    resource_id=payload.get('resourceId', ''),
                    data=payload,
                    timestamp=datetime.now(timezone.utc)
                )
        
        return None
    
    def _parse_tiktok_webhook(self, payload: Dict[str, Any]) -> Optional[WebhookEvent]:
        """Parse TikTok webhook payload"""
        if 'type' in payload:
            event_type_map = {
                'video.published': WebhookEventType.POST_PUBLISHED,
                'video.updated': WebhookEventType.POST_UPDATED,
                'video.deleted': WebhookEventType.POST_DELETED,
                'user.updated': WebhookEventType.PROFILE_UPDATED
            }
            
            tiktok_event_type = payload['type']
            mapped_event_type = event_type_map.get(tiktok_event_type)
            
            if mapped_event_type:
                return WebhookEvent(
                    platform='tiktok',
                    event_type=mapped_event_type,
                    user_id=None,
                    resource_id=payload.get('data', {}).get('video_id', ''),
                    data=payload,
                    timestamp=datetime.now(timezone.utc)
                )
        
        return None
    
    async def _store_webhook_event(self, event: WebhookEvent):
        """Store webhook event for analytics and debugging"""
        try:
            await redis_cache.set(
                'system',
                'webhook_event',
                event.to_dict(),
                resource_id=f"{event.platform}_{event.resource_id}_{int(event.timestamp.timestamp())}",
                ttl=86400  # Store for 24 hours
            )
        except Exception as e:
            logger.warning(f"Failed to store webhook event: {e}")
    
    # Event handlers
    async def _handle_post_published(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle post published event"""
        try:
            # Invalidate user's content cache
            if event.user_id:
                await cache_manager.invalidate_user_data(
                    event.user_id, 
                    [event.platform]
                )
            
            # Invalidate platform content caches
            await cache_manager.invalidate_platform_data(
                event.platform, 
                'recent_posts'
            )
            
            # Update database if this is our content
            await self._update_content_in_database(event)
            
            return {'status': 'success', 'action': 'cache_invalidated'}
            
        except Exception as e:
            logger.error(f"Error handling post published: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _handle_post_updated(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle post updated event"""
        try:
            # Similar to post published
            if event.user_id:
                await cache_manager.invalidate_user_data(
                    event.user_id, 
                    [event.platform]
                )
            
            await self._update_content_in_database(event)
            
            return {'status': 'success', 'action': 'content_updated'}
            
        except Exception as e:
            logger.error(f"Error handling post updated: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _handle_post_deleted(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle post deleted event"""
        try:
            # Invalidate related caches
            if event.user_id:
                await cache_manager.invalidate_user_data(
                    event.user_id, 
                    [event.platform]
                )
            
            # Mark content as deleted in database
            with get_db_connection() as db:
                content = db.query(ContentItem).filter(
                    ContentItem.platform_post_id == event.resource_id,
                    ContentItem.platform == event.platform
                ).first()
                
                if content:
                    content.status = 'deleted'
                    content.updated_at = datetime.now(timezone.utc)
                    db.commit()
            
            return {'status': 'success', 'action': 'content_deleted'}
            
        except Exception as e:
            logger.error(f"Error handling post deleted: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _handle_engagement_update(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle engagement update event"""
        try:
            # Update engagement metrics in database
            await self._update_engagement_metrics(event)
            
            # Invalidate analytics caches
            if event.user_id:
                await cache_manager.invalidate_platform_data(
                    event.platform, 
                    'analytics'
                )
            
            return {'status': 'success', 'action': 'engagement_updated'}
            
        except Exception as e:
            logger.error(f"Error handling engagement update: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _handle_profile_updated(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle profile updated event"""
        try:
            # Invalidate profile caches
            if event.user_id:
                await cache_manager.invalidate_user_data(
                    event.user_id, 
                    [event.platform]
                )
            
            await cache_manager.invalidate_platform_data(
                event.platform, 
                'profile'
            )
            
            return {'status': 'success', 'action': 'profile_cache_invalidated'}
            
        except Exception as e:
            logger.error(f"Error handling profile updated: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _handle_metrics_update(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle metrics update event"""
        try:
            # Update metrics in database
            await self._update_platform_metrics(event)
            
            # Invalidate metrics caches
            await cache_manager.invalidate_platform_data(
                event.platform, 
                'metrics'
            )
            
            return {'status': 'success', 'action': 'metrics_updated'}
            
        except Exception as e:
            logger.error(f"Error handling metrics update: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _update_content_in_database(self, event: WebhookEvent):
        """Update content information in database"""
        try:
            with get_db_connection() as db:
                content = db.query(ContentItem).filter(
                    ContentItem.platform_post_id == event.resource_id,
                    ContentItem.platform == event.platform
                ).first()
                
                if content:
                    # Update with webhook data
                    webhook_data = event.data
                    
                    # Platform-specific updates
                    if event.platform == 'twitter' and 'public_metrics' in webhook_data:
                        metrics = webhook_data['public_metrics']
                        content.like_count = metrics.get('like_count', 0)
                        content.share_count = metrics.get('retweet_count', 0)
                        content.comment_count = metrics.get('reply_count', 0)
                        content.view_count = metrics.get('impression_count', 0)
                    
                    content.updated_at = datetime.now(timezone.utc)
                    db.commit()
                    
                    logger.info(f"Updated content {content.id} from webhook")
                    
        except Exception as e:
            logger.error(f"Error updating content in database: {e}")
    
    async def _update_engagement_metrics(self, event: WebhookEvent):
        """Update engagement metrics from webhook"""
        try:
            with get_db_connection() as db:
                content = db.query(ContentItem).filter(
                    ContentItem.platform_post_id == event.resource_id,
                    ContentItem.platform == event.platform
                ).first()
                
                if content:
                    # Create performance snapshot
                    snapshot = ContentPerformanceSnapshot(
                        content_id=content.id,
                        like_count=event.data.get('like_count', content.like_count),
                        share_count=event.data.get('share_count', content.share_count),
                        comment_count=event.data.get('comment_count', content.comment_count),
                        view_count=event.data.get('view_count', content.view_count),
                        engagement_rate=event.data.get('engagement_rate', 0),
                        created_at=datetime.now(timezone.utc)
                    )
                    
                    db.add(snapshot)
                    db.commit()
                    
                    logger.info(f"Created performance snapshot for content {content.id}")
                    
        except Exception as e:
            logger.error(f"Error updating engagement metrics: {e}")
    
    async def _update_platform_metrics(self, event: WebhookEvent):
        """Update platform-wide metrics"""
        try:
            # Store platform metrics in cache for quick access
            await redis_cache.set(
                event.platform,
                'platform_metrics',
                event.data,
                ttl=3600  # 1 hour
            )
            
            logger.info(f"Updated platform metrics for {event.platform}")
            
        except Exception as e:
            logger.error(f"Error updating platform metrics: {e}")

# Global webhook processor
webhook_processor = WebhookProcessor()

# FastAPI webhook endpoints
class WebhookAPI:
    """FastAPI webhook endpoints"""
    
    def __init__(self, processor: WebhookProcessor):
        self.processor = processor
    
    async def handle_webhook(self, platform: str, request: Request) -> Dict[str, Any]:
        """Handle incoming webhook request"""
        try:
            # Get raw payload for signature verification
            payload_bytes = await request.body()
            
            # Get signature from headers
            signature = None
            if platform == 'twitter':
                signature = request.headers.get('x-twitter-webhooks-signature')
            elif platform in ['facebook', 'instagram']:
                signature = request.headers.get('x-hub-signature')
            elif platform == 'linkedin':
                signature = request.headers.get('x-li-signature')
            
            # Verify signature if provided
            if signature and not self.processor.verify_webhook_signature(platform, payload_bytes, signature):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
            # Parse JSON payload
            try:
                payload = json.loads(payload_bytes.decode())
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")
            
            # Process webhook
            result = await self.processor.process_webhook(platform, payload, signature)
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Webhook handling error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_webhook_stats(self) -> Dict[str, Any]:
        """Get webhook processing statistics"""
        try:
            # Get recent webhook events from cache
            stats = await redis_cache.get('system', 'webhook_stats')
            
            if not stats:
                stats = {
                    'total_webhooks': 0,
                    'successful_webhooks': 0,
                    'failed_webhooks': 0,
                    'last_webhook': None,
                    'platforms': {}
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting webhook stats: {e}")
            return {'error': str(e)}

# Global webhook API
webhook_api = WebhookAPI(webhook_processor)