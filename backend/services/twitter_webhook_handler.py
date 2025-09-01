"""
X/Twitter API v2 Webhook Handler

Handles incoming webhooks from X/Twitter for:
- Mentions in tweets
- Replies to tweets
- Direct messages
- Quote tweets

Uses Account Activity API with $200/month plan for real-time webhooks.
"""

import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from urllib.parse import quote

logger = logging.getLogger(__name__)

class TwitterWebhookHandler:
    """Handles X/Twitter webhook events using Account Activity API"""
    
    def __init__(self, consumer_secret: str, webhook_service=None):
        self.consumer_secret = consumer_secret
        self.webhook_service = webhook_service
        
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Twitter webhook signature"""
        if not signature:
            return False
            
        # Twitter sends signature as sha256=<base64_hash>
        if not signature.startswith('sha256='):
            return False
            
        expected_signature = signature[7:]  # Remove 'sha256=' prefix
        
        # Calculate HMAC-SHA256 and base64 encode
        calculated = hmac.new(
            self.consumer_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).digest()
        calculated_b64 = base64.b64encode(calculated).decode('utf-8')
        
        return hmac.compare_digest(calculated_b64, expected_signature)
    
    def create_crc_response(self, crc_token: str) -> str:
        """Create CRC response for Twitter webhook validation"""
        # Twitter requires CRC check during webhook registration
        signature = hmac.new(
            self.consumer_secret.encode('utf-8'),
            crc_token.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')
    
    async def process_webhook(self, payload: bytes, signature: str, user_id: int) -> Dict[str, Any]:
        """Process incoming Twitter webhook"""
        
        # Verify signature
        if not self.verify_signature(payload, signature):
            raise HTTPException(status_code=403, detail="Invalid webhook signature")
        
        try:
            data = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        results = []
        
        # Process different event types
        if 'tweet_create_events' in data:
            for tweet in data['tweet_create_events']:
                result = await self._process_tweet_event(tweet, user_id)
                if result:
                    results.append(result)
        
        if 'direct_message_events' in data:
            for dm in data['direct_message_events']:
                result = await self._process_dm_event(dm, data.get('users', {}), user_id)
                if result:
                    results.append(result)
        
        if 'tweet_delete_events' in data:
            # Handle tweet deletions if needed
            pass
        
        return {"processed_events": len(results), "events": results}
    
    async def _process_tweet_event(self, tweet: Dict[str, Any], user_id: int) -> Optional[Dict[str, Any]]:
        """Process a tweet event (mention, reply, etc.)"""
        tweet_id = tweet.get('id_str')
        text = tweet.get('text', '')
        user = tweet.get('user', {})
        created_at = tweet.get('created_at')
        
        # Skip tweets from the authenticated user (our own tweets)
        # This should be filtered by user ID comparison
        
        # Determine interaction type
        interaction_type = 'mention'
        parent_id = None
        
        if tweet.get('in_reply_to_status_id_str'):
            interaction_type = 'reply'
            parent_id = tweet.get('in_reply_to_status_id_str')
        elif 'RT @' in text:
            interaction_type = 'retweet'
        elif tweet.get('is_quote_status'):
            interaction_type = 'quote_tweet'
            parent_id = tweet.get('quoted_status_id_str')
        
        # Parse created_at timestamp
        try:
            # Twitter format: "Wed Oct 10 20:19:24 +0000 2018"
            dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
            created_at_iso = dt.isoformat()
        except (ValueError, TypeError):
            created_at_iso = datetime.now(timezone.utc).isoformat()
        
        interaction_data = {
            'platform': 'twitter',
            'platform_id': tweet_id,
            'platform_created_at': created_at_iso,
            'interaction_type': interaction_type,
            'author_id': user.get('id_str'),
            'author_username': user.get('screen_name'),
            'author_display_name': user.get('name'),
            'author_profile_image': user.get('profile_image_url_https'),
            'author_verified': user.get('verified', False),
            'content': text,
            'parent_id': parent_id,
            'platform_metadata': {
                'tweet_id': tweet_id,
                'user_id': user.get('id_str'),
                'screen_name': user.get('screen_name'),
                'retweet_count': tweet.get('retweet_count', 0),
                'favorite_count': tweet.get('favorite_count', 0),
                'in_reply_to_user_id': tweet.get('in_reply_to_user_id_str'),
                'in_reply_to_screen_name': tweet.get('in_reply_to_screen_name'),
                'is_quote_status': tweet.get('is_quote_status', False),
                'lang': tweet.get('lang'),
                'source': tweet.get('source'),
                'platform': 'twitter'
            }
        }
        
        # Store interaction and trigger processing
        if self.webhook_service:
            await self.webhook_service.store_interaction(user_id, interaction_data)
        
        return {
            'type': interaction_type,
            'platform': 'twitter',
            'processed': True,
            'interaction_id': tweet_id
        }
    
    async def _process_dm_event(self, dm: Dict[str, Any], users: Dict[str, Any], user_id: int) -> Optional[Dict[str, Any]]:
        """Process a direct message event"""
        dm_id = dm.get('id')
        message_create = dm.get('message_create', {})
        
        # Skip if this is an outgoing message (sent by us)
        sender_id = message_create.get('sender_id')
        # Should check if sender_id matches our authenticated user ID
        
        message_data = message_create.get('message_data', {})
        text = message_data.get('text', '')
        
        # Get sender info
        sender = users.get(sender_id, {})
        
        # Parse timestamp
        created_timestamp = int(dm.get('created_timestamp', 0))
        created_at_iso = datetime.fromtimestamp(
            created_timestamp / 1000, 
            tz=timezone.utc
        ).isoformat()
        
        interaction_data = {
            'platform': 'twitter',
            'platform_id': dm_id,
            'platform_created_at': created_at_iso,
            'interaction_type': 'direct_message',
            'author_id': sender_id,
            'author_username': sender.get('screen_name'),
            'author_display_name': sender.get('name'),
            'author_profile_image': sender.get('profile_image_url_https'),
            'author_verified': sender.get('verified', False),
            'content': text,
            'parent_id': None,
            'platform_metadata': {
                'dm_id': dm_id,
                'sender_id': sender_id,
                'recipient_id': message_create.get('target', {}).get('recipient_id'),
                'created_timestamp': created_timestamp,
                'platform': 'twitter'
            }
        }
        
        # Store interaction and trigger processing
        if self.webhook_service:
            await self.webhook_service.store_interaction(user_id, interaction_data)
        
        return {
            'type': 'direct_message',
            'platform': 'twitter', 
            'processed': True,
            'interaction_id': dm_id
        }

class TwitterV2WebhookHandler:
    """Enhanced Twitter webhook handler for API v2"""
    
    def __init__(self, consumer_secret: str, webhook_service=None):
        self.consumer_secret = consumer_secret
        self.webhook_service = webhook_service
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Twitter API v2 webhook signature"""
        # Same signature verification as v1.1
        if not signature:
            return False
            
        if not signature.startswith('sha256='):
            return False
            
        expected_signature = signature[7:]
        
        calculated = hmac.new(
            self.consumer_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).digest()
        calculated_b64 = base64.b64encode(calculated).decode('utf-8')
        
        return hmac.compare_digest(calculated_b64, expected_signature)
    
    async def process_webhook(self, payload: bytes, signature: str, user_id: int) -> Dict[str, Any]:
        """Process Twitter API v2 webhook"""
        
        if not self.verify_signature(payload, signature):
            raise HTTPException(status_code=403, detail="Invalid webhook signature")
        
        try:
            data = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        results = []
        
        # Process tweets with mentions
        if 'data' in data and isinstance(data['data'], list):
            for tweet_data in data['data']:
                result = await self._process_v2_tweet(tweet_data, data.get('includes', {}), user_id)
                if result:
                    results.append(result)
        
        return {"processed_events": len(results), "events": results}
    
    async def _process_v2_tweet(self, tweet_data: Dict[str, Any], includes: Dict[str, Any], user_id: int) -> Optional[Dict[str, Any]]:
        """Process a Twitter API v2 tweet"""
        tweet_id = tweet_data.get('id')
        text = tweet_data.get('text', '')
        author_id = tweet_data.get('author_id')
        created_at = tweet_data.get('created_at')
        
        # Get user info from includes
        users = {user['id']: user for user in includes.get('users', [])}
        author = users.get(author_id, {})
        
        # Determine interaction type
        interaction_type = 'mention'
        parent_id = None
        
        if tweet_data.get('in_reply_to_user_id'):
            interaction_type = 'reply'
            parent_id = tweet_data.get('referenced_tweets', [{}])[0].get('id')
        
        interaction_data = {
            'platform': 'twitter',
            'platform_id': tweet_id,
            'platform_created_at': created_at,
            'interaction_type': interaction_type,
            'author_id': author_id,
            'author_username': author.get('username'),
            'author_display_name': author.get('name'),
            'author_profile_image': author.get('profile_image_url'),
            'author_verified': author.get('verified', False),
            'content': text,
            'parent_id': parent_id,
            'platform_metadata': {
                'tweet_id': tweet_id,
                'author_id': author_id,
                'public_metrics': tweet_data.get('public_metrics', {}),
                'context_annotations': tweet_data.get('context_annotations', []),
                'lang': tweet_data.get('lang'),
                'platform': 'twitter'
            }
        }
        
        if self.webhook_service:
            await self.webhook_service.store_interaction(user_id, interaction_data)
        
        return {
            'type': interaction_type,
            'platform': 'twitter',
            'processed': True,
            'interaction_id': tweet_id
        }