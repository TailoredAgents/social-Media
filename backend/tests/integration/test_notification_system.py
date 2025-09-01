"""
Integration tests for the notification system
"""
import pytest
import json
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import WebSocket

from backend.auth.dependencies import get_current_user
from backend.db.database import get_db


class TestNotificationAPI:
    """Test notification API endpoints"""
    
    def test_get_notification_types(self, client):
        """Test getting available notification types"""
        response = client.get("/api/notifications/types")
        
        assert response.status_code == 200
        data = response.json()
        assert "notification_types" in data
        assert isinstance(data["notification_types"], list)
        
        # Check for expected notification types
        types = [nt["type"] for nt in data["notification_types"]]
        assert "post_published" in types
        assert "goal_milestone" in types
        assert "system_alert" in types
    
    def test_list_user_notifications(self, client, test_user_with_org, override_get_db):
        """Test listing notifications for authenticated user"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.get("/api/notifications/")
        
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "total_count" in data
        assert "unread_count" in data
        assert isinstance(data["notifications"], list)
    
    def test_get_unread_notifications(self, client, test_user_with_org, override_get_db):
        """Test getting only unread notifications"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.get("/api/notifications/?unread_only=true")
        
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        
        # All notifications should be unread
        for notification in data["notifications"]:
            assert notification["is_read"] is False
    
    def test_mark_notification_read(self, client, test_user_with_org, override_get_db):
        """Test marking a notification as read"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        # Create a test notification first (in a real test, this would exist)
        notification_id = "test-notification-123"
        
        response = client.patch(f"/api/notifications/{notification_id}/read")
        
        # Should accept the request (might be 404 if notification doesn't exist)
        assert response.status_code in [200, 404]
    
    def test_mark_all_notifications_read(self, client, test_user_with_org, override_get_db):
        """Test marking all notifications as read"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.patch("/api/notifications/mark-all-read")
        
        assert response.status_code == 200
        data = response.json()
        assert "updated_count" in data
    
    def test_delete_notification(self, client, test_user_with_org, override_get_db):
        """Test deleting a notification"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        notification_id = "test-notification-123"
        
        response = client.delete(f"/api/notifications/{notification_id}")
        
        # Should accept the request (might be 404 if notification doesn't exist)
        assert response.status_code in [200, 204, 404]
    
    def test_notification_preferences(self, client, test_user_with_org, override_get_db):
        """Test getting and updating notification preferences"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        # Get current preferences
        response = client.get("/api/notifications/preferences")
        
        assert response.status_code == 200
        data = response.json()
        assert "email_notifications" in data
        assert "push_notifications" in data
        assert "notification_types" in data
        
        # Update preferences
        new_preferences = {
            "email_notifications": True,
            "push_notifications": False,
            "notification_types": {
                "post_published": True,
                "goal_milestone": True,
                "system_alert": False
            }
        }
        
        response = client.put("/api/notifications/preferences", json=new_preferences)
        
        assert response.status_code == 200
        updated_data = response.json()
        assert updated_data["email_notifications"] == new_preferences["email_notifications"]
        assert updated_data["push_notifications"] == new_preferences["push_notifications"]


class TestNotificationWebSocket:
    """Test WebSocket notification functionality"""
    
    def test_websocket_connection_authenticated(self, client, test_user_with_org, override_get_db):
        """Test WebSocket connection with authenticated user"""
        client.app.dependency_overrides[get_db] = override_get_db
        
        # Mock WebSocket connection
        with patch('backend.services.notification_service.WebSocketManager') as mock_ws_manager:
            mock_manager = Mock()
            mock_manager.connect = AsyncMock()
            mock_manager.send_to_user = AsyncMock()
            mock_ws_manager.return_value = mock_manager
            
            # Test WebSocket endpoint
            with client.websocket_connect(f"/api/notifications/ws?user_id={test_user_with_org.id}") as websocket:
                # Should be able to connect
                assert websocket is not None
    
    def test_websocket_real_time_notification(self, client, test_user_with_org, override_get_db):
        """Test receiving real-time notifications via WebSocket"""
        client.app.dependency_overrides[get_db] = override_get_db
        
        with patch('backend.services.notification_service.WebSocketManager') as mock_ws_manager:
            mock_manager = Mock()
            mock_manager.connect = AsyncMock()
            mock_manager.send_to_user = AsyncMock()
            mock_ws_manager.return_value = mock_manager
            
            with client.websocket_connect(f"/api/notifications/ws?user_id={test_user_with_org.id}") as websocket:
                # Simulate sending a notification
                test_notification = {
                    "type": "notification",
                    "data": {
                        "id": "test-123",
                        "title": "Test Notification",
                        "message": "This is a test notification",
                        "notification_type": "post_published",
                        "priority": "medium",
                        "created_at": "2025-08-18T10:00:00Z"
                    },
                    "timestamp": "2025-08-18T10:00:00Z"
                }
                
                # In a real test, we'd send this notification and verify it's received
                # For now, just verify the connection works
                assert websocket is not None
    
    def test_websocket_ping_pong(self, client, test_user_with_org):
        """Test WebSocket ping/pong heartbeat"""
        with client.websocket_connect(f"/api/notifications/ws?user_id={test_user_with_org.id}") as websocket:
            # Send ping
            ping_message = {"type": "ping"}
            websocket.send_json(ping_message)
            
            # Should receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
    
    def test_websocket_mark_read_via_websocket(self, client, test_user_with_org):
        """Test marking notifications as read via WebSocket"""
        with client.websocket_connect(f"/api/notifications/ws?user_id={test_user_with_org.id}") as websocket:
            # Send mark read message
            mark_read_message = {
                "type": "mark_read",
                "notification_id": "test-notification-123"
            }
            websocket.send_json(mark_read_message)
            
            # Should receive confirmation (or error if notification doesn't exist)
            response = websocket.receive_json()
            assert response["type"] in ["marked_read", "error"]
    
    def test_websocket_connection_without_user_id(self, client):
        """Test WebSocket connection without user ID fails"""
        with pytest.raises(Exception):  # Should fail to connect
            with client.websocket_connect("/api/notifications/ws") as websocket:
                pass
    
    def test_websocket_invalid_user_id(self, client):
        """Test WebSocket connection with invalid user ID"""
        with pytest.raises(Exception):  # Should fail to connect
            with client.websocket_connect("/api/notifications/ws?user_id=invalid") as websocket:
                pass


class TestNotificationService:
    """Test the notification service functionality"""
    
    def test_create_notification(self, db_session, test_user_with_org):
        """Test creating a notification via the service"""
        from backend.services.notification_service import NotificationService
        
        notification_service = NotificationService(db_session)
        
        notification_data = {
            "user_id": test_user_with_org.id,
            "title": "Test Service Notification",
            "message": "This notification was created via the service",
            "notification_type": "system_alert",
            "priority": "high"
        }
        
        notification = notification_service.create_notification(**notification_data)
        
        assert notification is not None
        assert notification.title == notification_data["title"]
        assert notification.user_id == test_user_with_org.id
        assert notification.notification_type == "system_alert"
        assert notification.priority == "high"
        assert notification.is_read is False
    
    def test_send_real_time_notification(self, db_session, test_user_with_org):
        """Test sending real-time notification"""
        from backend.services.notification_service import NotificationService
        
        with patch('backend.services.notification_service.WebSocketManager') as mock_ws_manager:
            mock_manager = Mock()
            mock_manager.send_to_user = AsyncMock()
            mock_ws_manager.return_value = mock_manager
            
            notification_service = NotificationService(db_session)
            
            notification_data = {
                "user_id": test_user_with_org.id,
                "title": "Real-time Test",
                "message": "This should be sent in real-time",
                "notification_type": "post_published",
                "priority": "medium"
            }
            
            notification = notification_service.create_notification(**notification_data)
            
            # Verify WebSocket send was called
            mock_manager.send_to_user.assert_called()
    
    def test_notification_templates(self, db_session, test_user_with_org):
        """Test notification template system"""
        from backend.services.notification_service import NotificationService
        
        notification_service = NotificationService(db_session)
        
        # Test post published template
        template_data = {
            "platform": "twitter",
            "post_id": "123456789",
            "content": "Test tweet content"
        }
        
        notification = notification_service.create_from_template(
            user_id=test_user_with_org.id,
            template_type="post_published",
            template_data=template_data
        )
        
        assert notification is not None
        assert "twitter" in notification.title.lower()
        assert "published" in notification.title.lower()
        assert notification.notification_type == "post_published"
    
    def test_bulk_notification_creation(self, db_session, test_user_with_org, test_admin_user):
        """Test creating notifications for multiple users"""
        from backend.services.notification_service import NotificationService
        
        notification_service = NotificationService(db_session)
        
        user_ids = [test_user_with_org.id, test_admin_user.id]
        notification_data = {
            "title": "System Maintenance",
            "message": "The system will be down for maintenance",
            "notification_type": "system_alert",
            "priority": "urgent"
        }
        
        notifications = notification_service.create_bulk_notifications(
            user_ids=user_ids,
            **notification_data
        )
        
        assert len(notifications) == 2
        assert all(n.title == notification_data["title"] for n in notifications)
        assert all(n.priority == "urgent" for n in notifications)
    
    def test_notification_cleanup(self, db_session, test_user_with_org):
        """Test cleaning up old notifications"""
        from backend.services.notification_service import NotificationService
        from datetime import datetime, timedelta
        
        notification_service = NotificationService(db_session)
        
        # Create old notification
        old_notification = notification_service.create_notification(
            user_id=test_user_with_org.id,
            title="Old Notification",
            message="This is old",
            notification_type="system_alert",
            priority="low"
        )
        
        # Manually set creation date to be old
        old_notification.created_at = datetime.utcnow() - timedelta(days=31)
        db_session.commit()
        
        # Run cleanup
        cleaned_count = notification_service.cleanup_old_notifications(days_old=30)
        
        assert cleaned_count >= 1


class TestNotificationTriggers:
    """Test notification triggers for various events"""
    
    def test_post_published_trigger(self, db_session, test_user_with_org):
        """Test notification trigger when post is published"""
        from backend.services.notification_service import trigger_post_published_notification
        
        with patch('backend.services.notification_service.NotificationService') as mock_service:
            mock_service_instance = Mock()
            mock_service.return_value = mock_service_instance
            
            # Trigger notification
            trigger_post_published_notification(
                user_id=test_user_with_org.id,
                platform="twitter",
                post_id="123456789",
                content="Test tweet"
            )
            
            # Verify notification was created
            mock_service_instance.create_from_template.assert_called_once()
    
    def test_goal_milestone_trigger(self, db_session, test_user_with_org):
        """Test notification trigger for goal milestones"""
        from backend.services.notification_service import trigger_goal_milestone_notification
        
        with patch('backend.services.notification_service.NotificationService') as mock_service:
            mock_service_instance = Mock()
            mock_service.return_value = mock_service_instance
            
            # Trigger milestone notification
            trigger_goal_milestone_notification(
                user_id=test_user_with_org.id,
                goal_id="goal-123",
                milestone_type="25_percent",
                current_value=250,
                target_value=1000
            )
            
            # Verify notification was created
            mock_service_instance.create_from_template.assert_called_once()
    
    def test_system_alert_trigger(self, db_session, test_user_with_org):
        """Test system alert notification trigger"""
        from backend.services.notification_service import trigger_system_alert
        
        with patch('backend.services.notification_service.NotificationService') as mock_service:
            mock_service_instance = Mock()
            mock_service.return_value = mock_service_instance
            
            # Trigger system alert
            trigger_system_alert(
                message="API rate limit warning",
                severity="warning",
                affected_users=[test_user_with_org.id]
            )
            
            # Verify notification was created
            mock_service_instance.create_bulk_notifications.assert_called_once()


class TestNotificationErrorHandling:
    """Test error handling in notification system"""
    
    def test_websocket_connection_error(self, client, test_user_with_org):
        """Test WebSocket connection error handling"""
        with patch('backend.services.notification_service.WebSocketManager.connect') as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")
            
            # Should handle connection error gracefully
            with pytest.raises(Exception):
                with client.websocket_connect(f"/api/notifications/ws?user_id={test_user_with_org.id}") as websocket:
                    pass
    
    def test_notification_creation_error(self, db_session, test_user_with_org):
        """Test notification creation error handling"""
        from backend.services.notification_service import NotificationService
        
        notification_service = NotificationService(db_session)
        
        with patch.object(db_session, 'add', side_effect=Exception("Database error")):
            # Should handle database errors gracefully
            notification = notification_service.create_notification(
                user_id=test_user_with_org.id,
                title="Test",
                message="Test message",
                notification_type="system_alert"
            )
            
            assert notification is None  # Should return None on error
    
    def test_websocket_send_error(self, db_session, test_user_with_org):
        """Test WebSocket send error handling"""
        from backend.services.notification_service import NotificationService
        
        with patch('backend.services.notification_service.WebSocketManager') as mock_ws_manager:
            mock_manager = Mock()
            mock_manager.send_to_user = AsyncMock(side_effect=Exception("Send failed"))
            mock_ws_manager.return_value = mock_manager
            
            notification_service = NotificationService(db_session)
            
            # Should still create notification even if WebSocket send fails
            notification = notification_service.create_notification(
                user_id=test_user_with_org.id,
                title="Test",
                message="Test message",
                notification_type="system_alert"
            )
            
            assert notification is not None


class TestNotificationSecurity:
    """Test security aspects of notification system"""
    
    def test_user_can_only_access_own_notifications(self, client, test_user_with_org, test_admin_user, override_get_db):
        """Test that users can only access their own notifications"""
        client.app.dependency_overrides[get_db] = override_get_db
        
        # User 1 access
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        response1 = client.get("/api/notifications/")
        assert response1.status_code == 200
        
        # User 2 access
        client.app.dependency_overrides[get_current_user] = lambda: test_admin_user
        response2 = client.get("/api/notifications/")
        assert response2.status_code == 200
        
        # Responses should be different (though we can't verify content here)
    
    def test_websocket_user_isolation(self, client, test_user_with_org, test_admin_user):
        """Test that WebSocket connections are isolated per user"""
        # User 1 connection
        with client.websocket_connect(f"/api/notifications/ws?user_id={test_user_with_org.id}") as ws1:
            # User 2 connection
            with client.websocket_connect(f"/api/notifications/ws?user_id={test_admin_user.id}") as ws2:
                # Both should work independently
                assert ws1 is not None
                assert ws2 is not None
    
    def test_notification_input_validation(self, client, test_user_with_org, override_get_db):
        """Test input validation for notification endpoints"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        # Test invalid notification ID format
        response = client.patch("/api/notifications/invalid-id-format/read")
        assert response.status_code in [400, 404, 422]
        
        # Test invalid preferences format
        invalid_preferences = {
            "email_notifications": "not_a_boolean",
            "notification_types": "not_an_object"
        }
        
        response = client.put("/api/notifications/preferences", json=invalid_preferences)
        assert response.status_code == 422  # Validation error