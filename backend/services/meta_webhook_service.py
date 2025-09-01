"""
Meta (Facebook/Instagram) Webhook Service
Handles webhook signature verification, subscription management, and event processing
"""
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import httpx

from backend.core.config import get_settings
from backend.core.encryption import decrypt_token

logger = logging.getLogger(__name__)


class MetaWebhookService:
    """Service for handling Meta (Facebook/Instagram) webhooks"""
    
    def __init__(self, settings=None):
        """
        Initialize Meta webhook service
        
        Args:
            settings: Application settings (will get from config if not provided)
        """
        self.settings = settings or get_settings()
        self.app_secret = getattr(self.settings, 'meta_app_secret', '')
        self.graph_version = getattr(self.settings, 'meta_graph_version', 'v18.0')
        self.base_url = f"https://graph.facebook.com/{self.graph_version}"
        
    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Meta webhook HMAC signature
        
        Args:
            payload: Raw request body bytes
            signature: X-Hub-Signature-256 header value
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if not self.app_secret:
                logger.error("META_APP_SECRET not configured")
                return False
                
            # Expected format: "sha256=<hex_digest>"
            if not signature.startswith("sha256="):
                logger.warning("Meta webhook signature missing sha256 prefix")
                return False
            
            expected_digest = signature[7:]  # Remove "sha256=" prefix
            
            # Calculate HMAC using app secret
            calculated_hmac = hmac.new(
                self.app_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Use constant-time comparison to prevent timing attacks
            is_valid = hmac.compare_digest(calculated_hmac, expected_digest)
            
            if not is_valid:
                logger.warning("Meta webhook HMAC signature verification failed")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying Meta webhook signature: {e}")
            return False
    
    async def enqueue_event_processing(self, payload: Dict[str, Any], event_info: Dict[str, Any]) -> bool:
        """
        Enqueue webhook event processing to Celery
        
        Args:
            payload: Full webhook payload
            event_info: Basic event information for logging
            
        Returns:
            True if successfully enqueued, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from backend.tasks.webhook_tasks import process_meta_event
            
            # Set received timestamp
            event_info["received_at"] = datetime.now(timezone.utc).isoformat()
            
            # Process each entry in the payload
            entries = payload.get("entry", [])
            task_ids = []
            
            for entry in entries:
                # Add entry-level info for task processing
                entry_info = {
                    **event_info,
                    "entry_id": entry.get("id"),
                    "entry_time": entry.get("time"),
                }
                
                # Enqueue Celery task
                task = process_meta_event.delay(entry, entry_info)
                task_ids.append(task.id)
                
                logger.info(f"Enqueued Meta webhook entry processing: task_id={task.id}")
            
            logger.info(f"Enqueued {len(task_ids)} Meta webhook processing tasks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue Meta webhook processing: {e}")
            return False
    
    async def subscribe_page_webhooks(self, page_id: str, page_access_token: str) -> bool:
        """
        Subscribe a Facebook Page to app webhooks
        
        Args:
            page_id: Facebook Page ID
            page_access_token: Page access token
            
        Returns:
            True if subscription successful, False otherwise
        """
        try:
            url = f"{self.base_url}/{page_id}/subscribed_apps"
            
            params = {
                "subscribed_fields": "feed,mentions,messaging,message_deliveries,messaging_postbacks",
                "access_token": page_access_token
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params=params)
                response.raise_for_status()
                
                result = response.json()
                success = result.get("success", False)
                
                if success:
                    logger.info(f"Successfully subscribed Page {page_id} to webhooks")
                else:
                    logger.warning(f"Page {page_id} webhook subscription returned success=false")
                
                return success
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error subscribing Page {page_id} webhooks: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Error subscribing Page {page_id} webhooks: {e}")
            return False
    
    async def unsubscribe_page_webhooks(self, page_id: str, page_access_token: str) -> bool:
        """
        Unsubscribe a Facebook Page from app webhooks
        
        Args:
            page_id: Facebook Page ID
            page_access_token: Page access token
            
        Returns:
            True if unsubscription successful, False otherwise
        """
        try:
            url = f"{self.base_url}/{page_id}/subscribed_apps"
            
            params = {
                "access_token": page_access_token
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(url, params=params)
                
                # Both 200 and 400 are acceptable (400 might mean already unsubscribed)
                if response.status_code in [200, 400]:
                    logger.info(f"Successfully unsubscribed Page {page_id} from webhooks")
                    return True
                else:
                    logger.warning(f"Page {page_id} webhook unsubscription failed: {response.status_code} - {response.text}")
                    return False
                
        except Exception as e:
            logger.error(f"Error unsubscribing Page {page_id} webhooks: {e}")
            return False
    
    async def subscribe_instagram_webhooks(self, instagram_id: str, page_access_token: str) -> bool:
        """
        Subscribe an Instagram Business account to app webhooks
        
        Note: Instagram webhook subscriptions are often managed through the Page,
        but this method provides direct subscription if needed.
        
        Args:
            instagram_id: Instagram Business account ID
            page_access_token: Page access token (Instagram accounts are managed via Page tokens)
            
        Returns:
            True if subscription successful, False otherwise
        """
        try:
            url = f"{self.base_url}/{instagram_id}/subscribed_apps"
            
            params = {
                "subscribed_fields": "feed,comments,mentions,story_insights",
                "access_token": page_access_token
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params=params)
                
                # Instagram webhook subscriptions may not be available for all account types
                if response.status_code in [200, 400]:
                    logger.info(f"Successfully subscribed Instagram {instagram_id} to webhooks")
                    return True
                else:
                    logger.warning(f"Instagram {instagram_id} webhook subscription failed: {response.status_code}")
                    return False
                
        except Exception as e:
            logger.error(f"Error subscribing Instagram {instagram_id} webhooks: {e}")
            return False
    
    async def unsubscribe_instagram_webhooks(self, instagram_id: str, page_access_token: str) -> bool:
        """
        Unsubscribe an Instagram Business account from app webhooks
        
        Args:
            instagram_id: Instagram Business account ID
            page_access_token: Page access token
            
        Returns:
            True if unsubscription successful, False otherwise
        """
        try:
            url = f"{self.base_url}/{instagram_id}/subscribed_apps"
            
            params = {
                "access_token": page_access_token
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(url, params=params)
                
                # Both 200 and 400 are acceptable
                if response.status_code in [200, 400]:
                    logger.info(f"Successfully unsubscribed Instagram {instagram_id} from webhooks")
                    return True
                else:
                    logger.warning(f"Instagram {instagram_id} webhook unsubscription failed: {response.status_code}")
                    return False
                
        except Exception as e:
            logger.error(f"Error unsubscribing Instagram {instagram_id} webhooks: {e}")
            return False
    
    def normalize_webhook_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a Meta webhook entry to standard format
        
        Args:
            entry: Raw webhook entry from Meta
            
        Returns:
            Normalized entry data
        """
        try:
            normalized = {
                "platform": "meta",
                "entry_id": entry.get("id"),
                "entry_time": entry.get("time"),
                "object_type": "page",  # Default to page, may be overridden
                "changes": [],
                "messaging": [],
                "raw_entry": entry  # Keep original for debugging
            }
            
            # Process changes (Page events)
            for change in entry.get("changes", []):
                normalized_change = {
                    "field": change.get("field"),
                    "change_time": change.get("time"),
                    "value": change.get("value", {})
                }
                normalized["changes"].append(normalized_change)
            
            # Process messaging (Page/Instagram messaging)
            for message in entry.get("messaging", []):
                normalized_message = {
                    "sender": message.get("sender", {}).get("id"),
                    "recipient": message.get("recipient", {}).get("id"),
                    "timestamp": message.get("timestamp"),
                    "message": message.get("message"),
                    "postback": message.get("postback"),
                    "delivery": message.get("delivery"),
                    "read": message.get("read")
                }
                normalized["messaging"].append(normalized_message)
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing Meta webhook entry: {e}")
            return {
                "platform": "meta",
                "error": str(e),
                "raw_entry": entry
            }


# Singleton instance
_meta_webhook_service = None


def get_meta_webhook_service(settings=None) -> MetaWebhookService:
    """
    Get Meta webhook service instance
    
    Args:
        settings: Application settings (optional)
        
    Returns:
        MetaWebhookService instance
    """
    global _meta_webhook_service
    
    if _meta_webhook_service is None:
        _meta_webhook_service = MetaWebhookService(settings)
    
    return _meta_webhook_service