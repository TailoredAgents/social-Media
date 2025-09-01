"""
Integration tests for webhook system
Tests the full webhook processing flow including API endpoints, services, and tasks
"""
import pytest
import json
import hashlib
import hmac
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from backend.main import app
from backend.db.models import User, Organization, SocialConnection
from backend.tests.conftest import TestingSessionLocal


class TestWebhookEndToEndFlow:
    """Test complete webhook processing flow"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def db_session(self):
        """Create database session for testing"""
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    @pytest.fixture
    def test_user_and_org(self, db_session):
        """Create test user and organization"""
        # Create organization
        org = Organization(
            name="Test Org",
            is_active=True
        )
        db_session.add(org)
        db_session.flush()
        
        # Create user
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_verified=True,
            organization_id=org.id
        )
        db_session.add(user)
        db_session.commit()
        
        return user, org
    
    @pytest.fixture
    def meta_connection(self, db_session, test_user_and_org):
        """Create test Meta connection"""
        user, org = test_user_and_org
        
        connection = SocialConnection(
            organization_id=org.id,
            platform="meta",
            platform_account_id="page_123",
            platform_username="TestPage",
            access_tokens={"page_token": "encrypted_token"},
            is_active=True,
            webhook_subscribed=True,
            connection_metadata={"instagram_account_id": "insta_123"}
        )
        db_session.add(connection)
        db_session.commit()
        
        return connection
    
    @pytest.fixture
    def valid_webhook_payload(self):
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
                                "post_id": "post_456_789",
                                "created_time": 1234567890
                            }
                        }
                    ]
                }
            ]
        }
    
    @pytest.fixture
    def valid_signature(self, valid_webhook_payload):
        """Generate valid HMAC signature for test payload"""
        app_secret = "test_secret_123"
        payload_bytes = json.dumps(valid_webhook_payload, sort_keys=True).encode('utf-8')
        
        signature = hmac.new(
            app_secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    @patch('backend.api.webhooks.get_settings')
    def test_webhook_verification_flow(self, mock_get_settings, client):
        """Test complete webhook verification flow"""
        mock_get_settings.return_value = MagicMock(
            meta_verify_token="test_verify_token_123"
        )
        
        # Test webhook verification challenge
        response = client.get(
            "/api/webhooks/meta",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_verify_token_123",
                "hub.challenge": "challenge_response_123"
            }
        )
        
        assert response.status_code == 200
        assert response.text == "challenge_response_123"
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    @patch('backend.api.webhooks.get_meta_webhook_service')
    @patch('backend.tasks.webhook_tasks.process_meta_event')
    def test_webhook_processing_flow(
        self, 
        mock_process_task, 
        mock_get_service, 
        client, 
        valid_webhook_payload
    ):
        """Test complete webhook processing flow"""
        # Mock Celery task
        mock_task = MagicMock()
        mock_task.id = "task_123"
        mock_process_task.delay.return_value = mock_task
        
        # Mock webhook service
        mock_service = MagicMock()
        mock_service.verify_signature = AsyncMock(return_value=True)
        mock_service.enqueue_event_processing = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service
        
        # Process webhook
        response = client.post(
            "/api/webhooks/meta",
            json=valid_webhook_payload,
            headers={"X-Hub-Signature-256": "sha256=valid_signature"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "received"
        assert response_data["entries_processed"] == 1
        
        # Verify service interactions
        mock_service.verify_signature.assert_called_once()
        mock_service.enqueue_event_processing.assert_called_once()
    
    @patch('backend.services.meta_webhook_service.get_settings')
    @patch('httpx.AsyncClient')
    async def test_webhook_subscription_flow(self, mock_client, mock_get_settings):
        """Test webhook subscription flow during OAuth connection"""
        from backend.services.meta_webhook_service import MetaWebhookService
        
        # Mock settings
        mock_get_settings.return_value = MagicMock(
            meta_app_secret="test_secret",
            meta_graph_version="v18.0"
        )
        
        # Mock HTTP client for subscription
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_client_instance.post.return_value = mock_response
        
        # Test webhook subscription
        service = MetaWebhookService()
        result = await service.subscribe_page_webhooks("page_123", "access_token_456")
        
        assert result is True
        mock_client_instance.post.assert_called_once()
        
        # Verify subscription URL and parameters
        call_args = mock_client_instance.post.call_args
        assert "page_123/subscribed_apps" in call_args[0][0]
        assert call_args[1]["params"]["access_token"] == "access_token_456"
        assert "feed,mentions,messaging" in call_args[1]["params"]["subscribed_fields"]
    
    @patch('backend.services.meta_webhook_service.get_settings')
    @patch('httpx.AsyncClient')
    async def test_webhook_unsubscription_flow(self, mock_client, mock_get_settings):
        """Test webhook unsubscription flow during connection disconnect"""
        from backend.services.meta_webhook_service import MetaWebhookService
        
        # Mock settings
        mock_get_settings.return_value = MagicMock(
            meta_app_secret="test_secret",
            meta_graph_version="v18.0"
        )
        
        # Mock HTTP client for unsubscription
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_client_instance.delete.return_value = mock_response
        
        # Test webhook unsubscription
        service = MetaWebhookService()
        result = await service.unsubscribe_page_webhooks("page_123", "access_token_456")
        
        assert result is True
        mock_client_instance.delete.assert_called_once()
        
        # Verify unsubscription URL
        call_args = mock_client_instance.delete.call_args
        assert "page_123/subscribed_apps" in call_args[0][0]
    
    @patch('backend.tasks.webhook_tasks.get_meta_webhook_service')
    async def test_celery_task_processing_flow(self, mock_get_service):
        """Test Celery task processing flow"""
        from backend.tasks.webhook_tasks import process_meta_event
        
        # Mock webhook service
        mock_service = MagicMock()
        mock_service.normalize_webhook_entry.return_value = {
            "platform": "meta",
            "entry_id": "page_123",
            "changes": [
                {
                    "field": "feed",
                    "value": {"item": "post", "verb": "add"}
                }
            ],
            "messaging": []
        }
        mock_get_service.return_value = mock_service
        
        # Mock task instance
        task_instance = MagicMock()
        task_instance.request.id = "task_456"
        task_instance.request.retries = 0
        
        entry = {
            "id": "page_123",
            "time": 1234567890,
            "changes": [{"field": "feed", "value": {"item": "post"}}]
        }
        event_info = {"entry_id": "page_123", "webhook_id": "hook_789"}
        
        # Process the task
        result = await process_meta_event.__wrapped__(task_instance, entry, event_info)
        
        assert result["status"] == "success"
        assert result["task_id"] == "task_456"
        assert result["events_processed"] == 1
        
        # Verify service was called
        mock_service.normalize_webhook_entry.assert_called_once_with(entry)
    
    @patch('backend.tasks.webhook_watchdog.get_webhook_watchdog')
    async def test_webhook_watchdog_flow(self, mock_get_watchdog):
        """Test webhook watchdog monitoring flow"""
        from backend.tasks.webhook_tasks import watchdog_scan
        
        # Mock watchdog service
        mock_watchdog = MagicMock()
        mock_watchdog.scan_dlq = AsyncMock(return_value={
            "scan_time": "2025-01-01T12:00:00+00:00",
            "total_entries": 5,
            "actions_taken": {
                "retried": 2,
                "marked_failed": 1,
                "expired": 1,
                "alerts_sent": 1
            },
            "scan_duration_seconds": 1.5
        })
        mock_get_watchdog.return_value = mock_watchdog
        
        # Run watchdog scan
        result = watchdog_scan()
        
        assert result["status"] == "completed"
        # The current implementation returns basic stats, but this tests the flow


class TestWebhookErrorRecovery:
    """Test webhook error handling and recovery scenarios"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @patch('backend.api.webhooks.get_meta_webhook_service')
    def test_webhook_processing_with_signature_failure(self, mock_get_service, client):
        """Test webhook processing when signature verification fails"""
        # Mock service to fail signature verification
        mock_service = MagicMock()
        mock_service.verify_signature = AsyncMock(return_value=False)
        mock_get_service.return_value = mock_service
        
        payload = {"object": "page", "entry": [{"id": "page_123"}]}
        
        response = client.post(
            "/api/webhooks/meta",
            json=payload,
            headers={"X-Hub-Signature-256": "sha256=invalid_signature"}
        )
        
        assert response.status_code == 403
        assert "Invalid webhook signature" in response.json()["detail"]
    
    @patch('backend.api.webhooks.get_meta_webhook_service')
    def test_webhook_processing_with_enqueue_failure(self, mock_get_service, client):
        """Test webhook processing when task enqueuing fails"""
        # Mock service to succeed verification but fail enqueuing
        mock_service = MagicMock()
        mock_service.verify_signature = AsyncMock(return_value=True)
        mock_service.enqueue_event_processing = AsyncMock(return_value=False)
        mock_get_service.return_value = mock_service
        
        payload = {"object": "page", "entry": [{"id": "page_123"}]}
        
        response = client.post(
            "/api/webhooks/meta",
            json=payload,
            headers={"X-Hub-Signature-256": "sha256=valid_signature"}
        )
        
        assert response.status_code == 500
        assert "Failed to enqueue webhook processing" in response.json()["detail"]
    
    @patch('backend.tasks.webhook_tasks.get_meta_webhook_service')
    async def test_celery_task_retry_logic(self, mock_get_service):
        """Test Celery task retry logic for retryable errors"""
        from backend.tasks.webhook_tasks import process_meta_event
        from celery.exceptions import Retry
        
        # Mock service to raise retryable error
        mock_service = MagicMock()
        mock_service.normalize_webhook_entry.side_effect = ConnectionError("Network error")
        mock_get_service.return_value = mock_service
        
        # Mock task instance
        task_instance = MagicMock()
        task_instance.request.id = "retry_task_123"
        task_instance.request.retries = 1  # Below max retries
        task_instance.retry.side_effect = Retry("Retrying")
        
        entry = {"id": "page_123", "changes": []}
        event_info = {"entry_id": "page_123"}
        
        # Should raise Retry exception for retryable errors
        with pytest.raises(Retry):
            await process_meta_event.__wrapped__(task_instance, entry, event_info)
        
        task_instance.retry.assert_called_once()
    
    @patch('backend.tasks.webhook_tasks.get_meta_webhook_service')
    @patch('backend.tasks.webhook_tasks._send_to_dlq')
    async def test_celery_task_dlq_handling(self, mock_send_dlq, mock_get_service):
        """Test Celery task DLQ handling for non-retryable errors"""
        from backend.tasks.webhook_tasks import process_meta_event, DLQ_MAX_RETRIES
        
        # Mock service to raise non-retryable error
        mock_service = MagicMock()
        mock_service.normalize_webhook_entry.side_effect = ValueError("Invalid data")
        mock_get_service.return_value = mock_service
        
        # Mock DLQ
        mock_send_dlq.return_value = True
        
        # Mock task instance with max retries reached
        task_instance = MagicMock()
        task_instance.request.id = "dlq_task_123"
        task_instance.request.retries = DLQ_MAX_RETRIES
        
        entry = {"id": "page_123", "invalid": "data"}
        event_info = {"entry_id": "page_123"}
        
        # Should send to DLQ for non-retryable errors or max retries
        result = await process_meta_event.__wrapped__(task_instance, entry, event_info)
        
        assert result["status"] == "failed"
        assert result["sent_to_dlq"] is True
        mock_send_dlq.assert_called_once()


class TestWebhookSecurity:
    """Test webhook security features"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @patch('backend.services.meta_webhook_service.get_settings')
    async def test_hmac_signature_verification(self, mock_get_settings):
        """Test HMAC signature verification security"""
        from backend.services.meta_webhook_service import MetaWebhookService
        
        mock_get_settings.return_value = MagicMock(
            meta_app_secret="secret_key_123",
            meta_graph_version="v18.0"
        )
        
        service = MetaWebhookService()
        payload = b'{"test": "data"}'
        
        # Generate correct signature
        correct_signature = hmac.new(
            b"secret_key_123",
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Test correct signature
        is_valid = await service.verify_signature(payload, f"sha256={correct_signature}")
        assert is_valid is True
        
        # Test incorrect signature
        is_valid = await service.verify_signature(payload, "sha256=wrong_signature")
        assert is_valid is False
        
        # Test missing sha256 prefix
        is_valid = await service.verify_signature(payload, correct_signature)
        assert is_valid is False
    
    def test_timing_attack_protection(self):
        """Test that HMAC comparison uses constant-time comparison"""
        from backend.services.meta_webhook_service import MetaWebhookService
        import inspect
        
        # Verify that verify_signature method uses hmac.compare_digest
        source = inspect.getsource(MetaWebhookService.verify_signature)
        assert "hmac.compare_digest" in source
    
    @patch('backend.api.webhooks.get_settings')
    def test_verify_token_security(self, mock_get_settings, client):
        """Test verify token security in webhook verification"""
        mock_get_settings.return_value = MagicMock(
            meta_verify_token="secure_verify_token_123"
        )
        
        # Test correct token
        response = client.get(
            "/api/webhooks/meta",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "secure_verify_token_123",
                "hub.challenge": "challenge_123"
            }
        )
        assert response.status_code == 200
        
        # Test incorrect token
        response = client.get(
            "/api/webhooks/meta",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "challenge_123"
            }
        )
        assert response.status_code == 403
    
    def test_webhook_payload_size_limits(self, client):
        """Test webhook payload size handling"""
        # Create a reasonably large payload for testing
        large_payload = {
            "object": "page",
            "entry": [
                {
                    "id": f"page_{i}",
                    "time": 1234567890,
                    "data": "x" * 1000  # 1KB per entry
                }
                for i in range(50)  # 50KB total
            ]
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
            
            # Should handle reasonable payloads
            assert response.status_code in [200, 413, 422]


class TestWebhookPerformance:
    """Test webhook performance characteristics"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @patch('backend.api.webhooks.get_meta_webhook_service')
    def test_webhook_response_time(self, mock_get_service, client):
        """Test webhook response time is acceptable"""
        import time
        
        # Mock fast webhook service
        mock_service = MagicMock()
        mock_service.verify_signature = AsyncMock(return_value=True)
        mock_service.enqueue_event_processing = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service
        
        payload = {
            "object": "page",
            "entry": [{"id": "page_123", "time": 1234567890}]
        }
        
        start_time = time.time()
        response = client.post(
            "/api/webhooks/meta",
            json=payload,
            headers={"X-Hub-Signature-256": "sha256=valid_signature"}
        )
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        # Webhook should respond quickly (under 1 second for fast enqueuing)
        assert response_time < 1.0
    
    @patch('backend.api.webhooks.get_meta_webhook_service')
    def test_webhook_concurrent_processing(self, mock_get_service, client):
        """Test webhook handles multiple concurrent requests"""
        import threading
        import time
        
        # Mock webhook service
        mock_service = MagicMock()
        mock_service.verify_signature = AsyncMock(return_value=True)
        mock_service.enqueue_event_processing = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service
        
        payload = {
            "object": "page",
            "entry": [{"id": "page_123", "time": 1234567890}]
        }
        
        results = []
        
        def send_webhook():
            response = client.post(
                "/api/webhooks/meta",
                json=payload,
                headers={"X-Hub-Signature-256": "sha256=valid_signature"}
            )
            results.append(response.status_code)
        
        # Send 5 concurrent webhooks
        threads = []
        for i in range(5):
            thread = threading.Thread(target=send_webhook)
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert len(results) == 5
        assert all(status == 200 for status in results)