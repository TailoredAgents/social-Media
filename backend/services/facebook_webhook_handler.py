"""
Facebook and Instagram Graph API Webhook Handler

Handles incoming webhooks from Facebook and Instagram for:
- Comments on posts
- Mentions in posts/stories
- Direct messages (Facebook and Instagram)
- Page/profile interactions

Production-ready implementation with proper security validation
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class FacebookWebhookHandler:
    """Handles Facebook and Instagram webhook events"""
    
    def __init__(self, app_secret: str, webhook_service=None):
        self.app_secret = app_secret
        self.webhook_service = webhook_service
        
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Facebook webhook signature"""
        if not signature:
            return False
            
        # Facebook sends signature as sha256=<hash>
        if not signature.startswith('sha256='):
            return False
            
        expected_signature = signature[7:]  # Remove 'sha256=' prefix
        
        # Calculate HMAC-SHA256
        calculated = hmac.new(
            self.app_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(calculated, expected_signature)
    
    async def process_webhook(self, payload: bytes, signature: str, user_id: int) -> Dict[str, Any]:
        """Process incoming Facebook/Instagram webhook"""
        
        # Verify signature
        if not self.verify_signature(payload, signature):
            raise HTTPException(status_code=403, detail="Invalid webhook signature")
        
        try:
            data = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Process each entry
        results = []
        for entry in data.get('entry', []):
            entry_results = await self._process_entry(entry, user_id)
            results.extend(entry_results)
        
        return {"processed_events": len(results), "events": results}
    
    async def _process_entry(self, entry: Dict[str, Any], user_id: int) -> List[Dict[str, Any]]:
        """Process a single webhook entry"""
        results = []
        page_id = entry.get('id')
        
        # Process messaging events (DMs)
        if 'messaging' in entry:
            for message_event in entry['messaging']:
                result = await self._process_message_event(message_event, page_id, user_id)
                if result:
                    results.append(result)
        
        # Process feed changes (comments, posts)
        if 'changes' in entry:
            for change in entry['changes']:
                result = await self._process_change_event(change, page_id, user_id)
                if result:
                    results.append(result)
        
        return results
    
    async def _process_message_event(self, message_event: Dict[str, Any], page_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Process a messaging event (DM)"""
        sender = message_event.get('sender', {})
        recipient = message_event.get('recipient', {})
        message = message_event.get('message', {})
        
        # Skip if this is an echo (message sent by page)
        if message.get('is_echo'):
            return None
        
        # Skip if no text content
        text = message.get('text')
        if not text:
            return None
        
        platform = 'facebook'  # Will be 'instagram' for IG messages
        
        interaction_data = {
            'platform': platform,
            'platform_id': message.get('mid'),  # Message ID
            'platform_created_at': datetime.fromtimestamp(
                message_event.get('timestamp', 0) / 1000, 
                tz=timezone.utc
            ).isoformat(),
            'interaction_type': 'direct_message',
            'author_id': sender.get('id'),
            'author_username': sender.get('id'),  # FB doesn't provide username in messages
            'author_display_name': None,  # Would need separate API call
            'content': text,
            'parent_id': None,
            'platform_metadata': {
                'page_id': page_id,
                'sender_id': sender.get('id'),
                'recipient_id': recipient.get('id'),
                'message_id': message.get('mid'),
                'timestamp': message_event.get('timestamp'),
                'platform': platform
            }
        }
        
        # Store interaction and trigger processing
        if self.webhook_service:
            await self.webhook_service.store_interaction(user_id, interaction_data)
        
        return {
            'type': 'direct_message',
            'platform': platform,
            'processed': True,
            'interaction_id': message.get('mid')
        }
    
    async def _process_change_event(self, change: Dict[str, Any], page_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Process a feed change event (comment, mention, etc.)"""
        field = change.get('field')
        value = change.get('value', {})
        
        if field == 'feed':
            # Handle comments on posts
            if value.get('verb') == 'add' and value.get('item') == 'comment':
                return await self._process_comment(value, page_id, user_id)
            
            # Handle mentions in posts
            elif value.get('verb') == 'add' and value.get('item') == 'post':
                return await self._process_mention(value, page_id, user_id)
        
        elif field == 'mention':
            # Handle mentions/tags
            return await self._process_mention(value, page_id, user_id)
        
        return None
    
    async def _process_comment(self, value: Dict[str, Any], page_id: str, user_id: int) -> Dict[str, Any]:
        """Process a comment event"""
        comment_id = value.get('comment_id')
        post_id = value.get('post_id') 
        sender_id = value.get('sender_id')
        sender_name = value.get('sender_name')
        message = value.get('message', '')
        created_time = value.get('created_time')
        
        platform = 'facebook'  # Determine from page_id or other context
        
        interaction_data = {
            'platform': platform,
            'platform_id': comment_id,
            'platform_created_at': created_time,
            'interaction_type': 'comment',
            'author_id': sender_id,
            'author_username': sender_id,  # FB uses ID as username fallback
            'author_display_name': sender_name,
            'content': message,
            'parent_id': post_id,
            'platform_metadata': {
                'page_id': page_id,
                'post_id': post_id,
                'comment_id': comment_id,
                'sender_id': sender_id,
                'sender_name': sender_name,
                'platform': platform
            }
        }
        
        # Store interaction and trigger processing
        if self.webhook_service:
            await self.webhook_service.store_interaction(user_id, interaction_data)
        
        return {
            'type': 'comment',
            'platform': platform,
            'processed': True,
            'interaction_id': comment_id
        }
    
    async def _process_mention(self, value: Dict[str, Any], page_id: str, user_id: int) -> Dict[str, Any]:
        """Process a mention/tag event"""
        post_id = value.get('post_id')
        sender_id = value.get('sender_id')
        sender_name = value.get('sender_name')
        message = value.get('message', '')
        created_time = value.get('created_time')
        
        platform = 'facebook'  # Or 'instagram' based on context
        
        interaction_data = {
            'platform': platform,
            'platform_id': post_id,
            'platform_created_at': created_time,
            'interaction_type': 'mention',
            'author_id': sender_id,
            'author_username': sender_id,
            'author_display_name': sender_name,
            'content': message,
            'parent_id': None,
            'platform_metadata': {
                'page_id': page_id,
                'post_id': post_id,
                'sender_id': sender_id,
                'sender_name': sender_name,
                'mention_type': 'tag',
                'platform': platform
            }
        }
        
        # Store interaction and trigger processing
        if self.webhook_service:
            await self.webhook_service.store_interaction(user_id, interaction_data)
        
        return {
            'type': 'mention',
            'platform': platform,
            'processed': True,
            'interaction_id': post_id
        }

class InstagramWebhookHandler(FacebookWebhookHandler):
    """Instagram-specific webhook handler (extends Facebook handler)"""
    
    async def _process_message_event(self, message_event: Dict[str, Any], page_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Process Instagram message event"""
        result = await super()._process_message_event(message_event, page_id, user_id)
        if result:
            result['platform'] = 'instagram'
        return result
    
    async def _process_comment(self, value: Dict[str, Any], page_id: str, user_id: int) -> Dict[str, Any]:
        """Process Instagram comment event"""
        result = await super()._process_comment(value, page_id, user_id)
        result['platform'] = 'instagram'
        return result
    
    async def _process_mention(self, value: Dict[str, Any], page_id: str, user_id: int) -> Dict[str, Any]:
        """Process Instagram mention event"""
        result = await super()._process_mention(value, page_id, user_id)
        result['platform'] = 'instagram'
        return result