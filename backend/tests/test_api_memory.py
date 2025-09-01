"""
Test memory and vector search API endpoints
"""
import pytest
from fastapi.testclient import TestClient
import numpy as np

def test_store_memory_content(authenticated_client: TestClient, sample_memory_data):
    """Test storing content in memory system"""
    response = authenticated_client.post("/api/memory/store", json=sample_memory_data)
    
    assert response.status_code == 201
    data = response.json()
    
    expected_keys = ["id", "content", "content_type", "relevance_score", "created_at"]
    for key in expected_keys:
        assert key in data
    
    assert data["content"] == sample_memory_data["content"]
    assert data["content_type"] == sample_memory_data["content_type"]

def test_search_memory_content(authenticated_client: TestClient, test_memory_content):
    """Test searching memory content with semantic search"""
    search_request = {
        "query": "social media trends",
        "limit": 10,
        "min_relevance": 0.5
    }
    
    response = authenticated_client.post("/api/memory/search", json=search_request)
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    # Each result should have content and similarity score
    for result in data:
        assert "content" in result
        assert "similarity_score" in result
        assert "match_reason" in result

def test_get_memory_content_list(authenticated_client: TestClient, test_memory_content):
    """Test retrieving memory content list"""
    response = authenticated_client.get("/api/memory/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "content" in data
    assert "total" in data
    assert isinstance(data["content"], list)

def test_get_memory_content_by_id(authenticated_client: TestClient, test_memory_content):
    """Test retrieving specific memory content by ID"""
    response = authenticated_client.get(f"/api/memory/{test_memory_content.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == test_memory_content.id
    assert data["content"] == test_memory_content.content

def test_update_memory_content(authenticated_client: TestClient, test_memory_content):
    """Test updating memory content"""
    update_data = {
        "tags": ["updated", "memory", "test"],
        "relevance_score": 0.95,
        "performance_tier": "high"
    }
    
    response = authenticated_client.put(f"/api/memory/{test_memory_content.id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["tags"] == update_data["tags"]
    assert data["relevance_score"] == update_data["relevance_score"]

def test_delete_memory_content(authenticated_client: TestClient, test_memory_content):
    """Test deleting memory content"""
    response = authenticated_client.delete(f"/api/memory/{test_memory_content.id}")
    
    assert response.status_code == 200
    
    # Verify content is deleted
    get_response = authenticated_client.get(f"/api/memory/{test_memory_content.id}")
    assert get_response.status_code == 404

def test_memory_filtering_by_type(authenticated_client: TestClient, test_memory_content):
    """Test filtering memory content by type"""
    response = authenticated_client.get(f"/api/memory/?content_type={test_memory_content.content_type}")
    
    assert response.status_code == 200
    data = response.json()
    
    # All returned content should match the type filter
    for content in data["content"]:
        assert content["content_type"] == test_memory_content.content_type

def test_memory_filtering_by_platform(authenticated_client: TestClient, test_memory_content):
    """Test filtering memory content by platform"""
    response = authenticated_client.get(f"/api/memory/?platform={test_memory_content.platform}")
    
    assert response.status_code == 200
    data = response.json()
    
    # All returned content should match the platform filter
    for content in data["content"]:
        assert content["platform"] == test_memory_content.platform

def test_memory_search_with_filters(authenticated_client: TestClient, test_memory_content):
    """Test memory search with additional filters"""
    search_request = {
        "query": "test content",
        "content_types": ["research"],
        "platforms": ["twitter"],
        "min_relevance": 0.3,
        "limit": 5
    }
    
    response = authenticated_client.post("/api/memory/search", json=search_request)
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) <= 5  # Respects limit

def test_memory_bulk_operations(authenticated_client: TestClient, test_memory_content):
    """Test bulk memory operations"""
    bulk_data = {
        "memory_ids": [test_memory_content.id],
        "action": "update_performance_tier",
        "parameters": {"performance_tier": "high"}
    }
    
    response = authenticated_client.post("/api/memory/bulk", json=bulk_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "updated_count" in data
    assert data["updated_count"] >= 1

def test_memory_statistics(authenticated_client: TestClient, test_memory_content):
    """Test memory system statistics"""
    response = authenticated_client.get("/api/memory/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    expected_keys = ["total_memories", "by_type", "by_platform", "performance_distribution", "vector_stats"]
    for key in expected_keys:
        assert key in data

def test_similar_content_recommendations(authenticated_client: TestClient, test_memory_content):
    """Test getting similar content recommendations"""
    response = authenticated_client.get(f"/api/memory/{test_memory_content.id}/similar")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "similar_content" in data
    assert isinstance(data["similar_content"], list)
    
    # Each similar item should have similarity score
    for item in data["similar_content"]:
        assert "similarity_score" in item
        assert "content" in item

def test_memory_content_repurposing(authenticated_client: TestClient, test_memory_content):
    """Test content repurposing suggestions"""
    response = authenticated_client.get(f"/api/memory/{test_memory_content.id}/repurpose?target_platform=linkedin")
    
    assert response.status_code == 200
    data = response.json()
    
    expected_keys = ["original_content", "repurposed_content", "platform_adaptations", "suggestions"]
    for key in expected_keys:
        assert key in data

def test_vector_search_performance(authenticated_client: TestClient, test_memory_content):
    """Test vector search performance metrics"""
    search_request = {
        "query": "performance test query",
        "limit": 100
    }
    
    response = authenticated_client.post("/api/memory/search", json=search_request)
    
    assert response.status_code == 200
    
    # Should complete quickly (this is more of a smoke test)
    assert response.elapsed.total_seconds() < 2.0  # Should be much faster in reality

def test_memory_export(authenticated_client: TestClient, test_memory_content):
    """Test memory content export"""
    response = authenticated_client.get("/api/memory/export?format=json")
    
    assert response.status_code == 200
    
    # Should return JSON export
    data = response.json()
    assert "memories" in data
    assert "export_info" in data

def test_memory_embedding_regeneration(authenticated_client: TestClient, test_memory_content):
    """Test memory embedding regeneration"""
    response = authenticated_client.post(f"/api/memory/{test_memory_content.id}/regenerate-embedding")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "embedding_updated" in data
    assert data["embedding_updated"] == True

def test_memory_content_validation(authenticated_client: TestClient):
    """Test memory content validation"""
    invalid_data = {
        "content": "",  # Empty content
        "content_type": "invalid_type",
        "metadata": "not_a_dict"  # Should be dict
    }
    
    response = authenticated_client.post("/api/memory/store", json=invalid_data)
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

def test_memory_search_validation(authenticated_client: TestClient):
    """Test memory search validation"""
    invalid_search = {
        "query": "",  # Empty query
        "limit": 1000,  # Too high limit
        "min_relevance": 1.5  # Invalid relevance score
    }
    
    response = authenticated_client.post("/api/memory/search", json=invalid_search)
    
    assert response.status_code == 422

def test_memory_content_ownership(authenticated_client: TestClient, test_memory_content, db_session):
    """Test that users can only access their own memory content"""
    from backend.db.models import User, MemoryContent
    
    # Create another user's memory content
    other_user = User(
        email="other@example.com",
        username="otheruser",
        full_name="Other User",
        is_active=True
    )
    db_session.add(other_user)
    db_session.commit()
    
    other_memory = MemoryContent(
        id="other-memory-123",
        user_id=other_user.id,
        content="Other user's memory",
        content_type="research"
    )
    db_session.add(other_memory)
    db_session.commit()
    
    # Try to access other user's memory
    response = authenticated_client.get(f"/api/memory/{other_memory.id}")
    assert response.status_code == 404

def test_memory_vector_statistics(authenticated_client: TestClient, test_memory_content):
    """Test vector store statistics endpoint"""
    response = authenticated_client.get("/api/memory/vector/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    expected_keys = ["total_vectors", "index_size", "search_performance", "last_updated"]
    for key in expected_keys:
        assert key in data

@pytest.mark.asyncio
async def test_batch_memory_storage(authenticated_client: TestClient):
    """Test batch storage of multiple memory items"""
    batch_data = {
        "memories": [
            {
                "content": "First batch memory item",
                "content_type": "research",
                "tags": ["batch", "test"]
            },
            {
                "content": "Second batch memory item",
                "content_type": "insight",
                "tags": ["batch", "test"]
            }
        ]
    }
    
    response = authenticated_client.post("/api/memory/batch", json=batch_data)
    
    assert response.status_code == 201
    data = response.json()
    
    assert "created_count" in data
    assert data["created_count"] == 2
    assert "memory_ids" in data
    assert len(data["memory_ids"]) == 2

def test_memory_tag_suggestions(authenticated_client: TestClient, test_memory_content):
    """Test automatic tag suggestions for memory content"""
    response = authenticated_client.post("/api/memory/suggest-tags", json={
        "content": "This is content about artificial intelligence and machine learning trends"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert "suggested_tags" in data
    assert isinstance(data["suggested_tags"], list)
    assert len(data["suggested_tags"]) > 0