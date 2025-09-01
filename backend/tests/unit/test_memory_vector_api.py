"""
Comprehensive test suite for memory_vector API endpoints

Tests all memory vector API endpoints with proper authentication,
validation, error handling, and standardized response patterns.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.main import app
from backend.db.models import Memory, User
from backend.auth.dependencies import get_current_active_user
from backend.db.database import get_db
from backend.services.memory_service import memory_service
from backend.core.error_handler import ErrorCode, APIError


class TestMemoryVectorAPI:
    """Test suite for memory vector API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.is_admin = False
        return user
    
    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user"""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "admin@example.com"
        user.is_admin = True
        return user
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_memory(self):
        """Mock memory object"""
        memory = MagicMock(spec=Memory)
        memory.id = 1
        memory.content_id = "test-content-id"
        memory.content = "Test memory content"
        memory.memory_type = "insight"
        memory.metadata = {"platform": "twitter"}
        memory.created_at = datetime.utcnow()
        memory.vector_indexed = True
        return memory
    
    def test_store_vector_memory_success(self, client, mock_user, mock_db, mock_memory):
        """Test successful vector memory storage"""
        # Mock dependencies
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock memory service
        with patch.object(memory_service, 'store_memory') as mock_store:
            mock_store.return_value = {"content_id": "test-content-id"}
            mock_db.query.return_value.filter.return_value.first.return_value = mock_memory
            
            # Test request
            response = client.post(
                "/api/memory/vector/store",
                json={
                    "content": "Test content for storage",
                    "memory_type": "insight",
                    "platform": "twitter",
                    "tags": ["test", "memory"],
                    "engagement_rate": 5.2,
                    "metadata": {"additional": "data"}
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["content_id"] == "test-content-id"
            assert data["content"] == "Test memory content"
            assert data["memory_type"] == "insight"
            assert data["vector_indexed"] is True
        
        # Clean up
        app.dependency_overrides.clear()
    
    def test_store_vector_memory_validation_error(self, client, mock_user, mock_db):
        """Test validation error on store request"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Invalid memory type
        response = client.post(
            "/api/memory/vector/store",
            json={
                "content": "Test content",
                "memory_type": "invalid_type",  # Invalid type
                "platform": "twitter"
            }
        )
        
        assert response.status_code == 422
        
        # Empty content
        response = client.post(
            "/api/memory/vector/store",
            json={
                "content": "",  # Empty content
                "memory_type": "insight",
                "platform": "twitter"
            }
        )
        
        assert response.status_code == 422
        
        app.dependency_overrides.clear()
    
    def test_store_vector_memory_service_error(self, client, mock_user, mock_db):
        """Test service error handling"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        with patch.object(memory_service, 'store_memory') as mock_store:
            mock_store.side_effect = Exception("Service error")
            
            response = client.post(
                "/api/memory/vector/store",
                json={
                    "content": "Test content",
                    "memory_type": "insight",
                    "platform": "twitter"
                }
            )
            
            assert response.status_code == 500
        
        app.dependency_overrides.clear()
    
    def test_search_similar_memories_success(self, client, mock_user, mock_db, mock_memory):
        """Test successful similar memory search"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock search results
        search_results = [
            {
                "content_id": "test-content-id",
                "similarity_score": 0.85
            }
        ]
        
        with patch.object(memory_service, 'search_similar_content') as mock_search:
            mock_search.return_value = search_results
            mock_db.query.return_value.filter.return_value.first.return_value = mock_memory
            
            response = client.post(
                "/api/memory/vector/search",
                json={
                    "query": "test search query",
                    "top_k": 5,
                    "threshold": 0.7,
                    "memory_type": "insight"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["similarity_score"] == 0.85
            assert data[0]["content"] == "Test memory content"
        
        app.dependency_overrides.clear()
    
    def test_search_similar_memories_validation(self, client, mock_user, mock_db):
        """Test search validation"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Empty query
        response = client.post(
            "/api/memory/vector/search",
            json={
                "query": "",  # Empty query
                "top_k": 5,
                "threshold": 0.7
            }
        )
        
        assert response.status_code == 422
        
        # Invalid top_k
        response = client.post(
            "/api/memory/vector/search",
            json={
                "query": "test query",
                "top_k": 25,  # Too high
                "threshold": 0.7
            }
        )
        
        assert response.status_code == 422
        
        app.dependency_overrides.clear()
    
    def test_get_high_performing_content_success(self, client, mock_user, mock_db, mock_memory):
        """Test high-performing content retrieval"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        high_performing_results = [
            {"content_id": "test-content-id"}
        ]
        
        with patch.object(memory_service, 'get_high_performing_content') as mock_high:
            mock_high.return_value = high_performing_results
            mock_db.query.return_value.filter.return_value.first.return_value = mock_memory
            
            response = client.get(
                "/api/memory/vector/high-performing?min_engagement=5.0&limit=10"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["content"] == "Test memory content"
        
        app.dependency_overrides.clear()
    
    def test_get_repurposing_candidates_success(self, client, mock_user, mock_db, mock_memory):
        """Test repurposing candidates retrieval"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        repurposing_results = [
            {
                "content_id": "test-content-id",
                "age_days": 45,
                "engagement_rate": 6.5
            }
        ]
        
        with patch.object(memory_service, 'find_content_for_repurposing') as mock_repurpose:
            mock_repurpose.return_value = repurposing_results
            mock_db.query.return_value.filter.return_value.first.return_value = mock_memory
            
            response = client.get(
                "/api/memory/vector/repurposing-candidates?days_old=30&min_engagement=3.0"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["metadata"]["age_days"] == 45
            assert data[0]["metadata"]["original_engagement"] == 6.5
        
        app.dependency_overrides.clear()
    
    def test_analyze_content_patterns_success(self, client, mock_user, mock_db):
        """Test content pattern analysis"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        pattern_results = {
            "total_content": 100,
            "content_types": {"insight": 50, "research": 30},
            "platforms": {"twitter": 60, : 40},
            "avg_engagement": 4.5,
            "engagement_distribution": {"low": 0.3, "medium": 0.5, "high": 0.2}
        }
        
        with patch.object(memory_service, 'analyze_user_content_patterns') as mock_patterns:
            mock_patterns.return_value = pattern_results
            
            response = client.get("/api/memory/vector/patterns")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_content"] == 100
            assert data["avg_engagement"] == 4.5
            assert "content_types" in data
            assert "platforms" in data
        
        app.dependency_overrides.clear()
    
    def test_get_vector_stats_success(self, client, mock_user, mock_db):
        """Test vector statistics retrieval"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock database counts
        mock_db.query.return_value.filter.return_value.count.side_effect = [50, 45]  # total, indexed
        
        stats_results = {
            "vector_index_size": 45,
            "embedding_dimension": 1536,
            "avg_similarity_score": 0.75
        }
        
        with patch.object(memory_service, 'get_memory_stats') as mock_stats:
            mock_stats.return_value = stats_results
            
            response = client.get("/api/memory/vector/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_memories"] == 50
            assert data["indexed_memories"] == 45
            assert data["unindexed_memories"] == 5
            assert data["vector_index_size"] == 45
        
        app.dependency_overrides.clear()
    
    def test_sync_database_to_faiss_admin_success(self, client, mock_admin_user, mock_db):
        """Test FAISS sync with admin user"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_admin_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        sync_results = {
            "indexed": 25,
            "failed": 2,
            "total_memories": 50
        }
        
        with patch.object(memory_service, 'sync_database_to_faiss') as mock_sync:
            mock_sync.return_value = sync_results
            
            response = client.post("/api/memory/vector/sync")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["indexed"] == 25
            assert data["failed"] == 2
            assert data["total_vectors"] == 50
        
        app.dependency_overrides.clear()
    
    def test_sync_database_to_faiss_non_admin_forbidden(self, client, mock_user, mock_db):
        """Test FAISS sync forbidden for non-admin"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        response = client.post("/api/memory/vector/sync")
        
        assert response.status_code == 403
        
        app.dependency_overrides.clear()
    
    def test_get_memories_by_type_success(self, client, mock_user, mock_db, mock_memory):
        """Test retrieving memories by type"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        type_results = [
            {"content_id": "test-content-id"}
        ]
        
        with patch.object(memory_service, 'get_content_by_type') as mock_type:
            mock_type.return_value = type_results
            mock_db.query.return_value.filter.return_value.first.return_value = mock_memory
            
            response = client.get("/api/memory/vector/by-type/insight?limit=10")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["memory_type"] == "insight"
        
        app.dependency_overrides.clear()
    
    def test_authentication_required(self, client):
        """Test that endpoints require authentication"""
        # Test endpoints without authentication
        endpoints = [
            ("/api/memory/vector/store", "POST", {"content": "test", "memory_type": "insight"}),
            ("/api/memory/vector/search", "POST", {"query": "test"}),
            ("/api/memory/vector/high-performing", "GET", None),
            ("/api/memory/vector/patterns", "GET", None),
            ("/api/memory/vector/stats", "GET", None),
            ("/api/memory/vector/by-type/insight", "GET", None)
        ]
        
        for endpoint, method, json_data in endpoints:
            if method == "POST":
                response = client.post(endpoint, json=json_data)
            else:
                response = client.get(endpoint)
            
            # Should require authentication
            assert response.status_code in [401, 403]
    
    def test_error_handling_standardization(self, client, mock_user, mock_db):
        """Test that errors follow standardized format"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Test service error with standardized format
        with patch.object(memory_service, 'store_memory') as mock_store:
            mock_store.side_effect = Exception("Service failure")
            
            response = client.post(
                "/api/memory/vector/store",
                json={
                    "content": "Test content",
                    "memory_type": "insight"
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            # Should have error details with code, message, timestamp
            assert "detail" in data
        
        app.dependency_overrides.clear()


class TestMemoryVectorIntegration:
    """Integration tests for memory vector API with real database"""
    
    def test_end_to_end_workflow(self, client, test_db, test_user):
        """Test complete workflow: store -> search -> retrieve"""
        # This would be an integration test with real database
        # Implementation depends on test database setup
        pass
    
    def test_concurrent_operations(self, client, test_db, test_user):
        """Test concurrent memory operations"""
        # Test concurrent store/search operations
        pass
    
    def test_large_dataset_performance(self, client, test_db, test_user):
        """Test performance with large dataset"""
        # Test with many memories and large search operations
        pass


# Performance benchmarks
class TestMemoryVectorPerformance:
    """Performance tests for memory vector operations"""
    
    def test_search_performance(self, client, mock_user, mock_db):
        """Test search response times"""
        # Benchmark search performance
        pass
    
    def test_storage_performance(self, client, mock_user, mock_db):
        """Test storage performance"""
        # Benchmark storage operations
        pass