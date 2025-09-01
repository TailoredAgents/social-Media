"""
Unit tests for Meta webhook service
"""
import pytest
import json
import hashlib
import hmac
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone

from backend.services.meta_webhook_service import MetaWebhookService, get_meta_webhook_service


class TestMetaWebhookService:
    """Test Meta webhook service functionality"""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing"""
        settings = MagicMock()
        settings.meta_app_secret = "test_secret_key_123"
        settings.meta_graph_version = "v18.0"
        return settings
    
    @pytest.fixture
    def webhook_service(self, mock_settings):
        """Create webhook service with mock settings"""
        return MetaWebhookService(settings=mock_settings)
    
    def test_init_with_settings(self, mock_settings):
        """Test initialization with provided settings"""
        service = MetaWebhookService(settings=mock_settings)
        assert service.app_secret == "test_secret_key_123"
        assert service.graph_version == "v18.0"
        assert service.base_url == "https://graph.facebook.com/v18.0"
    
    @patch('backend.services.meta_webhook_service.get_settings')
    def test_init_without_settings(self, mock_get_settings):
        """Test initialization without provided settings"""
        mock_settings = MagicMock()
        mock_settings.meta_app_secret = "default_secret"
        mock_settings.meta_graph_version = "v19.0"
        mock_get_settings.return_value = mock_settings
        
        service = MetaWebhookService()
        assert service.app_secret == "default_secret"
        assert service.graph_version == "v19.0"

    async def test_verify_signature_valid(self, webhook_service):
        """Test HMAC signature verification with valid signature"""
        payload = b'{"test": "data"}'
        
        # Calculate expected signature
        expected_hmac = hmac.new(
            webhook_service.app_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        signature = f"sha256={expected_hmac}"
        
        is_valid = await webhook_service.verify_signature(payload, signature)
        assert is_valid is True
    
    async def test_verify_signature_invalid(self, webhook_service):
        """Test HMAC signature verification with invalid signature"""
        payload = b'{"test": "data"}'
        signature = "sha256=invalid_signature_hash"
        
        is_valid = await webhook_service.verify_signature(payload, signature)
        assert is_valid is False
    
    async def test_verify_signature_wrong_prefix(self, webhook_service):
        """Test signature verification with wrong prefix"""
        payload = b'{"test": "data"}'
        signature = "sha1=some_hash"  # Wrong prefix
        
        is_valid = await webhook_service.verify_signature(payload, signature)
        assert is_valid is False
    
    async def test_verify_signature_no_app_secret(self):
        """Test signature verification without app secret"""
        settings = MagicMock()
        settings.meta_app_secret = ""
        service = MetaWebhookService(settings=settings)
        
        payload = b'{"test": "data"}'
        signature = "sha256=some_hash"
        
        is_valid = await service.verify_signature(payload, signature)
        assert is_valid is False
    
    async def test_verify_signature_exception_handling(self, webhook_service):
        """Test signature verification exception handling"""
        payload = b'{"test": "data"}'
        signature = None  # This will cause an exception
        
        is_valid = await webhook_service.verify_signature(payload, signature)
        assert is_valid is False

    @patch('backend.tasks.webhook_tasks.process_meta_event')
    async def test_enqueue_event_processing_success(self, mock_process_meta_event, webhook_service):
        """Test successful event processing enqueuing"""
        # Mock Celery task
        mock_task = MagicMock()
        mock_task.id = "task_123"
        mock_process_meta_event.delay.return_value = mock_task
        
        payload = {
            "object": "page",
            "entry": [
                {"id": "page_123", "time": 1234567890},
                {"id": "page_456", "time": 1234567891}
            ]
        }
        event_info = {"webhook_id": "test_123"}
        
        result = await webhook_service.enqueue_event_processing(payload, event_info)
        
        assert result is True
        assert mock_process_meta_event.delay.call_count == 2
        
        # Verify task calls
        calls = mock_process_meta_event.delay.call_args_list
        assert calls[0][0][0]["id"] == "page_123"  # First entry
        assert calls[1][0][0]["id"] == "page_456"  # Second entry
    
    @patch('backend.tasks.webhook_tasks.process_meta_event')
    async def test_enqueue_event_processing_failure(self, mock_process_meta_event, webhook_service):
        """Test event processing enqueuing failure"""
        mock_process_meta_event.delay.side_effect = Exception("Celery error")
        
        payload = {"object": "page", "entry": [{"id": "page_123"}]}
        event_info = {"webhook_id": "test_123"}
        
        result = await webhook_service.enqueue_event_processing(payload, event_info)
        assert result is False

    @patch('httpx.AsyncClient')
    async def test_subscribe_page_webhooks_success(self, mock_client, webhook_service):
        """Test successful page webhook subscription"""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_client_instance.post.return_value = mock_response
        
        result = await webhook_service.subscribe_page_webhooks("page_123", "token_456")
        
        assert result is True
        mock_client_instance.post.assert_called_once()
        
        # Verify URL and params
        call_args = mock_client_instance.post.call_args
        assert "page_123/subscribed_apps" in call_args[0][0]
        assert "access_token" in call_args[1]["params"]
    
    @patch('httpx.AsyncClient')
    async def test_subscribe_page_webhooks_failure(self, mock_client, webhook_service):
        """Test failed page webhook subscription"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": False}
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_client_instance.post.return_value = mock_response
        
        result = await webhook_service.subscribe_page_webhooks("page_123", "token_456")
        assert result is False
    
    @patch('httpx.AsyncClient')
    async def test_subscribe_page_webhooks_http_error(self, mock_client, webhook_service):
        """Test page webhook subscription HTTP error"""
        from httpx import HTTPStatusError, Response, Request
        
        # Create mock request and response for HTTPStatusError
        mock_request = Request("POST", "http://test.com")
        mock_response = Response(400, request=mock_request)
        mock_response._text = "Bad Request"
        
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_client_instance.post.side_effect = HTTPStatusError(
            "400 Bad Request", request=mock_request, response=mock_response
        )
        
        result = await webhook_service.subscribe_page_webhooks("page_123", "token_456")
        assert result is False

    @patch('httpx.AsyncClient')
    async def test_unsubscribe_page_webhooks_success(self, mock_client, webhook_service):
        """Test successful page webhook unsubscription"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_client_instance.delete.return_value = mock_response
        
        result = await webhook_service.unsubscribe_page_webhooks("page_123", "token_456")
        
        assert result is True
        mock_client_instance.delete.assert_called_once()
    
    @patch('httpx.AsyncClient')
    async def test_unsubscribe_page_webhooks_already_unsubscribed(self, mock_client, webhook_service):
        """Test page webhook unsubscription when already unsubscribed (400 is OK)"""
        mock_response = MagicMock()
        mock_response.status_code = 400  # Already unsubscribed
        
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_client_instance.delete.return_value = mock_response
        
        result = await webhook_service.unsubscribe_page_webhooks("page_123", "token_456")
        assert result is True
    
    @patch('httpx.AsyncClient')
    async def test_unsubscribe_page_webhooks_failure(self, mock_client, webhook_service):
        """Test failed page webhook unsubscription"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_client_instance.delete.return_value = mock_response
        
        result = await webhook_service.unsubscribe_page_webhooks("page_123", "token_456")
        assert result is False

    @patch('httpx.AsyncClient')
    async def test_subscribe_instagram_webhooks_success(self, mock_client, webhook_service):
        """Test successful Instagram webhook subscription"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_client_instance.post.return_value = mock_response
        
        result = await webhook_service.subscribe_instagram_webhooks("insta_123", "token_456")
        
        assert result is True
        mock_client_instance.post.assert_called_once()
        
        # Verify URL contains Instagram ID
        call_args = mock_client_instance.post.call_args
        assert "insta_123/subscribed_apps" in call_args[0][0]

    @patch('httpx.AsyncClient')
    async def test_unsubscribe_instagram_webhooks_success(self, mock_client, webhook_service):
        """Test successful Instagram webhook unsubscription"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_client_instance.delete.return_value = mock_response
        
        result = await webhook_service.unsubscribe_instagram_webhooks("insta_123", "token_456")
        assert result is True

    def test_normalize_webhook_entry_basic(self, webhook_service):
        """Test basic webhook entry normalization"""
        entry = {
            "id": "page_123",
            "time": 1234567890,
            "changes": [
                {
                    "field": "feed",
                    "value": {"item": "post", "verb": "add", "post_id": "post_123"}
                }
            ]
        }
        
        normalized = webhook_service.normalize_webhook_entry(entry)
        
        assert normalized["platform"] == "meta"
        assert normalized["entry_id"] == "page_123"
        assert normalized["entry_time"] == 1234567890
        assert len(normalized["changes"]) == 1
        assert normalized["changes"][0]["field"] == "feed"
        assert normalized["raw_entry"] == entry
    
    def test_normalize_webhook_entry_with_messaging(self, webhook_service):
        """Test webhook entry normalization with messaging"""
        entry = {
            "id": "page_123",
            "time": 1234567890,
            "messaging": [
                {
                    "sender": {"id": "user_456"},
                    "recipient": {"id": "page_123"},
                    "timestamp": 1234567890,
                    "message": {"text": "Hello"}
                }
            ]
        }
        
        normalized = webhook_service.normalize_webhook_entry(entry)
        
        assert len(normalized["messaging"]) == 1
        assert normalized["messaging"][0]["sender"] == "user_456"
        assert normalized["messaging"][0]["recipient"] == "page_123"
        assert normalized["messaging"][0]["message"]["text"] == "Hello"
    
    def test_normalize_webhook_entry_error_handling(self, webhook_service):
        """Test webhook entry normalization error handling"""
        entry = None  # This will cause an error
        
        normalized = webhook_service.normalize_webhook_entry(entry)
        
        assert normalized["platform"] == "meta"
        assert "error" in normalized
        assert normalized["raw_entry"] is None


class TestWebhookServiceSingleton:
    """Test webhook service singleton functionality"""
    
    @patch('backend.services.meta_webhook_service.get_settings')
    def test_get_meta_webhook_service_singleton(self, mock_get_settings):
        """Test that get_meta_webhook_service returns singleton"""
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings
        
        # Reset singleton
        import backend.services.meta_webhook_service
        backend.services.meta_webhook_service._meta_webhook_service = None
        
        service1 = get_meta_webhook_service()
        service2 = get_meta_webhook_service()
        
        assert service1 is service2
        mock_get_settings.assert_called_once()
    
    def test_get_meta_webhook_service_with_settings(self):
        """Test get_meta_webhook_service with provided settings"""
        settings = MagicMock()
        settings.meta_app_secret = "test_secret"
        
        # Reset singleton
        import backend.services.meta_webhook_service
        backend.services.meta_webhook_service._meta_webhook_service = None
        
        service = get_meta_webhook_service(settings=settings)
        assert service.app_secret == "test_secret"