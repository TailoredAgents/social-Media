"""
Unit tests for webhook API endpoints
"""
import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from backend.main import app
from backend.api.webhooks import router


class TestWebhookVerificationEndpoint:
    """Test Meta webhook verification endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings"""
        settings = MagicMock()
        settings.meta_verify_token = "test_verify_token_123"
        settings.feature_partner_oauth = True
        return settings
    
    @patch('backend.api.webhooks.get_settings')
    def test_verify_meta_webhook_success(self, mock_get_settings, client):
        """Test successful Meta webhook verification"""
        mock_get_settings.return_value = MagicMock(meta_verify_token="test_verify_token_123")
        
        response = client.get(
            "/api/webhooks/meta",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_verify_token_123",
                "hub.challenge": "challenge_123"
            }
        )
        
        assert response.status_code == 200
        assert response.text == "challenge_123"
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    @patch('backend.api.webhooks.get_settings')
    def test_verify_meta_webhook_invalid_token(self, mock_get_settings, client):
        """Test Meta webhook verification with invalid token"""
        mock_get_settings.return_value = MagicMock(meta_verify_token="test_verify_token_123")
        
        response = client.get(
            "/api/webhooks/meta",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "challenge_123"
            }
        )
        
        assert response.status_code == 403
        assert "Verification failed" in response.json()["detail"]
    
    @patch('backend.api.webhooks.get_settings')
    def test_verify_meta_webhook_wrong_mode(self, mock_get_settings, client):
        """Test Meta webhook verification with wrong mode"""
        mock_get_settings.return_value = MagicMock(meta_verify_token="test_verify_token_123")
        
        response = client.get(
            "/api/webhooks/meta",
            params={
                "hub.mode": "unsubscribe",  # Wrong mode
                "hub.verify_token": "test_verify_token_123",
                "hub.challenge": "challenge_123"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid mode" in response.json()["detail"]
    
    @patch('backend.api.webhooks.get_settings')
    def test_verify_meta_webhook_missing_params(self, mock_get_settings, client):
        """Test Meta webhook verification with missing parameters"""
        mock_get_settings.return_value = MagicMock(meta_verify_token="test_verify_token_123")
        
        response = client.get(
            "/api/webhooks/meta",
            params={
                "hub.mode": "subscribe"
                # Missing verify_token and challenge
            }
        )
        
        assert response.status_code == 400
        assert "Missing required parameters" in response.json()["detail"]
    
    @patch('backend.api.webhooks.get_settings')
    def test_verify_meta_webhook_no_verify_token_configured(self, mock_get_settings, client):
        """Test Meta webhook verification without configured verify token"""
        mock_get_settings.return_value = MagicMock(meta_verify_token="")
        
        response = client.get(
            "/api/webhooks/meta",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "any_token",
                "hub.challenge": "challenge_123"
            }
        )
        
        assert response.status_code == 500
        assert "META_VERIFY_TOKEN not configured" in response.json()["detail"]


class TestWebhookProcessingEndpoint:
    """Test Meta webhook processing endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def valid_payload(self):
        """Create valid Meta webhook payload"""
        return {
            "object": "page",
            "entry": [
                {
                    "id": "page_123",
                    "time": 1234567890,
                    "changes": [
                        {
                            "field": "feed",
                            "value": {
                                "item": "post",
                                "verb": "add",
                                "post_id": "post_456"
                            }
                        }
                    ]
                }
            ]
        }
    
    @patch('backend.api.webhooks.get_meta_webhook_service')
    def test_process_meta_webhook_success(self, mock_get_service, client, valid_payload):
        """Test successful Meta webhook processing"""
        # Mock webhook service
        mock_service = MagicMock()
        mock_service.verify_signature = AsyncMock(return_value=True)
        mock_service.enqueue_event_processing = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/webhooks/meta",
            json=valid_payload,
            headers={"X-Hub-Signature-256": "sha256=valid_signature"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "received"
        assert response_data["entries_processed"] == 1
        assert "received_at" in response_data
        
        # Verify service calls
        mock_service.verify_signature.assert_called_once()
        mock_service.enqueue_event_processing.assert_called_once()
    
    @patch('backend.api.webhooks.get_meta_webhook_service')
    def test_process_meta_webhook_invalid_signature(self, mock_get_service, client, valid_payload):
        """Test Meta webhook processing with invalid signature"""
        # Mock webhook service
        mock_service = MagicMock()
        mock_service.verify_signature = AsyncMock(return_value=False)
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/webhooks/meta",
            json=valid_payload,
            headers={"X-Hub-Signature-256": "sha256=invalid_signature"}
        )
        
        assert response.status_code == 403
        assert "Invalid webhook signature" in response.json()["detail"]
    
    @patch('backend.api.webhooks.get_meta_webhook_service')
    def test_process_meta_webhook_missing_signature(self, mock_get_service, client, valid_payload):
        """Test Meta webhook processing with missing signature"""
        response = client.post(
            "/api/webhooks/meta",
            json=valid_payload
            # Missing X-Hub-Signature-256 header
        )
        
        assert response.status_code == 400
        assert "Missing X-Hub-Signature-256 header" in response.json()["detail"]
    
    @patch('backend.api.webhooks.get_meta_webhook_service')
    def test_process_meta_webhook_invalid_payload(self, mock_get_service, client):
        """Test Meta webhook processing with invalid payload"""
        invalid_payload = {"invalid": "structure"}
        
        # Mock webhook service
        mock_service = MagicMock()
        mock_service.verify_signature = AsyncMock(return_value=True)
        mock_service.enqueue_event_processing = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/webhooks/meta",
            json=invalid_payload,
            headers={"X-Hub-Signature-256": "sha256=valid_signature"}
        )
        
        assert response.status_code == 400
        assert "Invalid webhook payload" in response.json()["detail"]
    
    @patch('backend.api.webhooks.get_meta_webhook_service')
    def test_process_meta_webhook_enqueue_failure(self, mock_get_service, client, valid_payload):
        """Test Meta webhook processing with enqueue failure"""
        # Mock webhook service
        mock_service = MagicMock()
        mock_service.verify_signature = AsyncMock(return_value=True)
        mock_service.enqueue_event_processing = AsyncMock(return_value=False)
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/webhooks/meta",
            json=valid_payload,
            headers={"X-Hub-Signature-256": "sha256=valid_signature"}
        )
        
        assert response.status_code == 500
        assert "Failed to enqueue webhook processing" in response.json()["detail"]
    
    @patch('backend.api.webhooks.get_meta_webhook_service')
    def test_process_meta_webhook_service_exception(self, mock_get_service, client, valid_payload):
        """Test Meta webhook processing with service exception"""
        # Mock webhook service to raise exception
        mock_service = MagicMock()
        mock_service.verify_signature = AsyncMock(side_effect=Exception("Service error"))
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/webhooks/meta",
            json=valid_payload,
            headers={"X-Hub-Signature-256": "sha256=valid_signature"}
        )
        
        assert response.status_code == 500
        assert "Webhook processing failed" in response.json()["detail"]
    
    def test_process_meta_webhook_service_not_available(self, client, valid_payload):
        """Test Meta webhook processing when service not available"""
        with patch('backend.api.webhooks.get_meta_webhook_service', return_value=None):
            response = client.post(
                "/api/webhooks/meta",
                json=valid_payload,
                headers={"X-Hub-Signature-256": "sha256=valid_signature"}
            )
            
            assert response.status_code == 503
            assert "Meta webhook service not available" in response.json()["detail"]
    
    @patch('backend.api.webhooks.get_meta_webhook_service')
    def test_process_meta_webhook_empty_entries(self, mock_get_service, client):
        """Test Meta webhook processing with empty entries"""
        empty_payload = {
            "object": "page",
            "entry": []  # Empty entries
        }
        
        # Mock webhook service
        mock_service = MagicMock()
        mock_service.verify_signature = AsyncMock(return_value=True)
        mock_service.enqueue_event_processing = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/webhooks/meta",
            json=empty_payload,
            headers={"X-Hub-Signature-256": "sha256=valid_signature"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["entries_processed"] == 0
    
    @patch('backend.api.webhooks.get_meta_webhook_service')
    def test_process_meta_webhook_multiple_entries(self, mock_get_service, client):
        """Test Meta webhook processing with multiple entries"""
        multi_entry_payload = {
            "object": "page",
            "entry": [
                {"id": "page_123", "time": 1234567890},
                {"id": "page_456", "time": 1234567891},
                {"id": "page_789", "time": 1234567892}
            ]
        }
        
        # Mock webhook service
        mock_service = MagicMock()
        mock_service.verify_signature = AsyncMock(return_value=True)
        mock_service.enqueue_event_processing = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/webhooks/meta",
            json=multi_entry_payload,
            headers={"X-Hub-Signature-256": "sha256=valid_signature"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["entries_processed"] == 3


class TestWebhookRouterConfiguration:
    """Test webhook router configuration and integration"""
    
    def test_router_prefix(self):
        """Test webhook router has correct prefix"""
        from backend.api.webhooks import router
        # Router prefix is set in the main app when including the router
        # This test verifies the router object exists and is configured
        assert router is not None
    
    def test_router_tags(self):
        """Test webhook router has correct tags"""
        from backend.api.webhooks import router
        # Tags are typically set when including the router in the main app
        # This test verifies the router has the expected routes
        route_paths = [route.path for route in router.routes]
        assert "/meta" in route_paths
    
    @patch('backend.api.webhooks.get_meta_webhook_service')
    def test_webhook_endpoint_dependency_injection(self, mock_get_service):
        """Test webhook endpoint dependency injection"""
        client = TestClient(app)
        
        # Test that the dependency injection works
        response = client.get("/api/webhooks/meta?hub.mode=test")
        
        # Should get a 400 for invalid mode, but this confirms the endpoint exists
        # and dependency injection is working
        assert response.status_code in [400, 403, 500]  # Any of these is fine for this test
    
    def test_webhook_endpoint_async_support(self):
        """Test that webhook endpoints support async operations"""
        from backend.api.webhooks import process_meta_webhook
        import inspect
        
        # Verify the endpoint function is async
        assert inspect.iscoroutinefunction(process_meta_webhook)


class TestWebhookErrorHandling:
    """Test webhook error handling edge cases"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_webhook_malformed_json(self, client):
        """Test webhook with malformed JSON"""
        response = client.post(
            "/api/webhooks/meta",
            content="invalid json{",
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=signature"
            }
        )
        
        # FastAPI should handle this gracefully
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_webhook_wrong_content_type(self, client):
        """Test webhook with wrong content type"""
        response = client.post(
            "/api/webhooks/meta",
            content="text content",
            headers={
                "Content-Type": "text/plain",
                "X-Hub-Signature-256": "sha256=signature"
            }
        )
        
        # Should fail due to wrong content type
        assert response.status_code in [400, 422]
    
    def test_webhook_large_payload(self, client):
        """Test webhook with very large payload"""
        # Create a large payload (but not too large to avoid memory issues in tests)
        large_entry = {
            "id": "page_123",
            "time": 1234567890,
            "data": "x" * 10000  # 10KB of data
        }
        
        large_payload = {
            "object": "page",
            "entry": [large_entry] * 10  # 100KB total
        }
        
        with patch('backend.api.webhooks.get_meta_webhook_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.verify_signature = AsyncMock(return_value=True)
            mock_service.enqueue_event_processing = AsyncMock(return_value=True)
            mock_get_service.return_value = mock_service
            
            response = client.post(
                "/api/webhooks/meta",
                json=large_payload,
                headers={"X-Hub-Signature-256": "sha256=valid_signature"}
            )
            
            # Should handle large payloads gracefully
            assert response.status_code in [200, 413]  # OK or Payload Too Large


class TestWebhookMetrics:
    """Test webhook metrics and logging"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @patch('backend.api.webhooks.logger')
    @patch('backend.api.webhooks.get_meta_webhook_service')
    def test_webhook_processing_logging(self, mock_get_service, mock_logger, client):
        """Test that webhook processing generates appropriate logs"""
        payload = {
            "object": "page",
            "entry": [{"id": "page_123", "time": 1234567890}]
        }
        
        # Mock webhook service
        mock_service = MagicMock()
        mock_service.verify_signature = AsyncMock(return_value=True)
        mock_service.enqueue_event_processing = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/webhooks/meta",
            json=payload,
            headers={"X-Hub-Signature-256": "sha256=valid_signature"}
        )
        
        assert response.status_code == 200
        
        # Verify logging calls
        mock_logger.info.assert_called()
        
        # Check that log messages contain relevant information
        log_calls = mock_logger.info.call_args_list
        log_messages = [call[0][0] for call in log_calls]
        
        # Should log webhook received and processing success
        assert any("Received Meta webhook" in msg for msg in log_messages)
        assert any("Successfully processed Meta webhook" in msg for msg in log_messages)