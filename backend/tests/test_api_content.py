"""
Test content management API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

def test_create_content(authenticated_client: TestClient, sample_content_data):
    """Test creating new content"""
    response = authenticated_client.post("/api/content/", json=sample_content_data)
    
    assert response.status_code == 201
    data = response.json()
    
    expected_keys = ["id", "content", "platform", "content_type", "status", "created_at"]
    for key in expected_keys:
        assert key in data
    
    assert data["content"] == sample_content_data["content"]
    assert data["platform"] == sample_content_data["platform"]
    assert data["status"] == "draft"  # Default status

def test_get_content_list(authenticated_client: TestClient, test_content_item):
    """Test retrieving content list"""
    response = authenticated_client.get("/api/content/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "content" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    
    assert len(data["content"]) >= 1
    assert data["total"] >= 1

def test_get_content_by_id(authenticated_client: TestClient, test_content_item):
    """Test retrieving specific content by ID"""
    response = authenticated_client.get(f"/api/content/{test_content_item.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == test_content_item.id
    assert data["content"] == test_content_item.content
    assert data["platform"] == test_content_item.platform

def test_update_content(authenticated_client: TestClient, test_content_item):
    """Test updating existing content"""
    update_data = {
        "content": "Updated content text",
        "status": "ready"
    }
    
    response = authenticated_client.put(f"/api/content/{test_content_item.id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["content"] == update_data["content"]
    assert data["status"] == update_data["status"]

def test_delete_content(authenticated_client: TestClient, test_content_item):
    """Test deleting content"""
    response = authenticated_client.delete(f"/api/content/{test_content_item.id}")
    
    assert response.status_code == 200
    
    # Verify content is deleted
    get_response = authenticated_client.get(f"/api/content/{test_content_item.id}")
    assert get_response.status_code == 404

def test_content_filtering_by_platform(authenticated_client: TestClient, test_content_item):
    """Test filtering content by platform"""
    response = authenticated_client.get(f"/api/content/?platform={test_content_item.platform}")
    
    assert response.status_code == 200
    data = response.json()
    
    # All returned content should match the platform filter
    for content in data["content"]:
        assert content["platform"] == test_content_item.platform

def test_content_filtering_by_status(authenticated_client: TestClient, test_content_item):
    """Test filtering content by status"""
    response = authenticated_client.get(f"/api/content/?status={test_content_item.status}")
    
    assert response.status_code == 200
    data = response.json()
    
    # All returned content should match the status filter
    for content in data["content"]:
        assert content["status"] == test_content_item.status

def test_content_search(authenticated_client: TestClient, test_content_item):
    """Test content search functionality"""
    search_query = "test"
    response = authenticated_client.get(f"/api/content/?search={search_query}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Search should work (might return 0 or more results)
    assert "content" in data
    assert isinstance(data["content"], list)

def test_content_pagination(authenticated_client: TestClient, test_content_item):
    """Test content pagination"""
    response = authenticated_client.get("/api/content/?page=1&page_size=10")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["content"]) <= 10

def test_schedule_content(authenticated_client: TestClient, sample_content_data):
    """Test scheduling content for future publication"""
    scheduled_time = datetime.utcnow() + timedelta(hours=2)
    sample_content_data["scheduled_for"] = scheduled_time.isoformat()
    sample_content_data["status"] = "scheduled"
    
    response = authenticated_client.post("/api/content/", json=sample_content_data)
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["status"] == "scheduled"
    assert "scheduled_for" in data

def test_content_analytics(authenticated_client: TestClient, test_content_item):
    """Test content analytics endpoint"""
    response = authenticated_client.get(f"/api/content/{test_content_item.id}/analytics")
    
    assert response.status_code == 200
    data = response.json()
    
    expected_keys = ["engagement_rate", "performance_tier", "metrics"]
    for key in expected_keys:
        assert key in data

def test_bulk_content_operations(authenticated_client: TestClient, test_content_item):
    """Test bulk content operations"""
    bulk_data = {
        "content_ids": [test_content_item.id],
        "action": "update_status",
        "parameters": {"status": "archived"}
    }
    
    response = authenticated_client.post("/api/content/bulk", json=bulk_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "updated_count" in data
    assert data["updated_count"] >= 1

def test_content_export(authenticated_client: TestClient, test_content_item):
    """Test content export functionality"""
    response = authenticated_client.get("/api/content/export?format=csv")
    
    assert response.status_code == 200
    # Should return CSV content
    assert response.headers["content-type"] == "text/csv"

def test_content_validation_errors(authenticated_client: TestClient):
    """Test content creation with validation errors"""
    invalid_data = {
        "content": "",  # Empty content should fail
        "platform": "invalid_platform",  # Invalid platform
        "content_type": "invalid_type"  # Invalid type
    }
    
    response = authenticated_client.post("/api/content/", json=invalid_data)
    
    assert response.status_code == 422
    data = response.json()
    
    assert "detail" in data
    # Should contain validation error details

def test_unauthorized_content_access(client: TestClient):
    """Test that unauthorized users cannot access content"""
    response = client.get("/api/content/")
    
    assert response.status_code == 401

def test_content_owner_isolation(authenticated_client: TestClient, test_content_item, db_session):
    """Test that users can only access their own content"""
    # Create another user's content
    from backend.db.models import User, ContentItem
    
    other_user = User(
        email="other@example.com",
        username="otheruser",
        full_name="Other User",
        is_active=True
    )
    db_session.add(other_user)
    db_session.commit()
    
    other_content = ContentItem(
        user_id=other_user.id,
        content="Other user's content",
        platform="twitter",
        content_type="post"
    )
    db_session.add(other_content)
    db_session.commit()
    
    # Try to access other user's content
    response = authenticated_client.get(f"/api/content/{other_content.id}")
    assert response.status_code == 404  # Should not find it

def test_content_performance_tracking(authenticated_client: TestClient, test_content_item):
    """Test content performance tracking updates"""
    performance_data = {
        "likes": 150,
        "shares": 25,
        "comments": 10,
        "impressions": 2000,
        "engagement_rate": 9.25
    }
    
    response = authenticated_client.post(
        f"/api/content/{test_content_item.id}/performance",
        json=performance_data
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "performance_updated" in data
    assert data["performance_updated"] == True

@pytest.mark.asyncio
async def test_content_ai_generation(authenticated_client: TestClient):
    """Test AI-powered content generation"""
    generation_request = {
        "topic": "artificial intelligence trends",
        "platform": "twitter",
        "tone": "professional",
        "include_hashtags": True
    }
    
    response = authenticated_client.post("/api/content/generate", json=generation_request)
    
    assert response.status_code == 200
    data = response.json()
    
    expected_keys = ["generated_content", "hashtags", "engagement_prediction"]
    for key in expected_keys:
        assert key in data
    
    assert len(data["generated_content"]) > 0
    assert isinstance(data["hashtags"], list)

def test_content_duplicate_detection(authenticated_client: TestClient, test_content_item):
    """Test duplicate content detection"""
    duplicate_data = {
        "content": test_content_item.content,  # Same content
        "platform": test_content_item.platform,
        "content_type": test_content_item.content_type
    }
    
    response = authenticated_client.post("/api/content/", json=duplicate_data)
    
    # Should either warn about duplicates or create with a flag
    assert response.status_code in [201, 409]  # Created or Conflict

def test_content_scheduling_validation(authenticated_client: TestClient, sample_content_data):
    """Test content scheduling validation"""
    # Try to schedule in the past
    past_time = datetime.utcnow() - timedelta(hours=1)
    sample_content_data["scheduled_for"] = past_time.isoformat()
    
    response = authenticated_client.post("/api/content/", json=sample_content_data)
    
    # Should handle past scheduling appropriately
    assert response.status_code in [201, 422]  # Either created or validation error