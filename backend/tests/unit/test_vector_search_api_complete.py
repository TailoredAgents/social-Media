"""
Comprehensive test suite for vector search API endpoints

Tests all vector search API endpoints including similarity search,
content creation assistance, memory storage, and performance optimization.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from backend.main import app
from backend.db.models import User
from backend.auth.dependencies import get_current_user
from backend.db.database import get_db


class TestVectorSearchAPI:
    """Test suite for vector search API endpoints"""
    
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
        return user
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_search_results(self):
        """Mock vector search results"""
        return [
            {
                "id": 1,
                "content": "AI is transforming the future of technology with innovative solutions",
                "memory_type": "research",
                "similarity_score": 0.92,
                "metadata": {
                    "platform": "research",
                    "tags": ["AI", "technology", "innovation"],
                    "created_at": "2024-01-15T10:30:00Z"
                },
                "created_at": datetime.utcnow(),
                "tags": ["AI", "technology"]
            },
            {
                "id": 2,
                "content": "Machine learning algorithms are revolutionizing data analysis",
                "memory_type": "insight",
                "similarity_score": 0.87,
                "metadata": {
                    "platform": ,
                    "engagement_rate": 6.5,
                    "tags": ["ML", "data", "analysis"]
                },
                "created_at": datetime.utcnow(),
                "tags": ["ML", "data"]
            }
        ]
    
    def test_vector_search_success(self, client, mock_user, mock_db, mock_search_results):
        """Test successful vector similarity search"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        with patch('backend.api.vector_search.memory_service') as mock_service, \
             patch('backend.api.vector_search.clean_text_input') as mock_clean, \
             patch('backend.api.vector_search.validate_text_length') as mock_validate:
            
            mock_clean.return_value = "artificial intelligence trends"
            mock_validate.return_value = None
            mock_service.search_similar_memories.return_value = mock_search_results
            
            response = client.post(
                "/api/vector/search",
                json={
                    "query": "artificial intelligence trends",
                    "memory_type": "research",
                    "limit": 10,
                    "threshold": 0.8
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["results"]) == 2
            assert data["results"][0]["similarity_score"] == 0.92
            assert data["results"][0]["memory_type"] == "research"
            assert data["query"] == "artificial intelligence trends"
            assert data["total_results"] == 2
        
        app.dependency_overrides.clear()
    
    def test_vector_search_validation_errors(self, client, mock_user, mock_db):
        """Test vector search validation errors"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Empty query
        response = client.post(
            "/api/vector/search",
            json={
                "query": "",
                "limit": 10,
                "threshold": 0.8
            }
        )
        assert response.status_code == 422
        
        # Query too long
        response = client.post(
            "/api/vector/search",
            json={
                "query": "A" * 1001,  # Exceeds 1000 character limit
                "limit": 10,
                "threshold": 0.8
            }
        )
        assert response.status_code == 422
        
        # Invalid limit
        response = client.post(
            "/api/vector/search",
            json={
                "query": "test query",
                "limit": 100,  # Exceeds max limit of 50
                "threshold": 0.8
            }
        )
        assert response.status_code == 422
        
        # Invalid threshold
        response = client.post(
            "/api/vector/search",
            json={
                "query": "test query",
                "limit": 10,
                "threshold": 1.5  # Exceeds max threshold of 1.0
            }
        )
        assert response.status_code == 422
        
        app.dependency_overrides.clear()
    
    def test_vector_search_with_filters(self, client, mock_user, mock_db, mock_search_results):
        """Test vector search with memory type filter"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Filter by research type
        filtered_results = [r for r in mock_search_results if r["memory_type"] == "research"]
        
        with patch('backend.api.vector_search.memory_service') as mock_service, \
             patch('backend.api.vector_search.clean_text_input') as mock_clean, \
             patch('backend.api.vector_search.validate_text_length') as mock_validate:
            
            mock_clean.return_value = "machine learning"
            mock_validate.return_value = None
            mock_service.search_similar_memories.return_value = filtered_results
            
            response = client.post(
                "/api/vector/search",
                json={
                    "query": "machine learning",
                    "memory_type": "research",
                    "limit": 5,
                    "threshold": 0.7
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 1
            assert data["results"][0]["memory_type"] == "research"
        
        app.dependency_overrides.clear()
    
    def test_content_creation_search_success(self, client, mock_user, mock_db):
        """Test content creation search assistance"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_content_memories = {
            "similar_content": [
                {
                    "content": "AI revolutionizes healthcare with predictive analytics",
                    "similarity_score": 0.89,
                    "engagement_rate": 7.2,
                    "platform": 
                }
            ],
            "research_insights": [
                {
                    "content": "Latest research shows AI improving diagnostic accuracy by 25%",
                    "similarity_score": 0.85,
                    "source": "medical_journal",
                    "credibility_score": 0.92
                }
            ],
            "templates": [
                {
                    "template": "🏥 {insight} {statistic} {call_to_action} #healthcare #AI",
                    "performance_score": 8.1,
                    "usage_count": 15
                }
            ],
            "high_performing_examples": [
                {
                    "content": "Healthcare AI breakthrough: 95% accuracy in early diagnosis! 🎯",
                    "engagement_rate": 9.3,
                    "platform": "twitter",
                    "metrics": {"likes": 450, "shares": 89, "comments": 23}
                }
            ],
            "total_relevant_memories": 4
        }
        
        with patch('backend.api.vector_search.memory_service') as mock_service:
            mock_service.find_memories_for_content_creation.return_value = mock_content_memories
            
            response = client.post(
                "/api/vector/content-creation-search",
                json={
                    "topic": "AI in healthcare",
                    "platform": 
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["topic"] == "AI in healthcare"
            assert data["platform"] == 
            assert len(data["similar_content"]) == 1
            assert len(data["research_insights"]) == 1
            assert len(data["templates"]) == 1
            assert data["total_relevant_memories"] == 4
        
        app.dependency_overrides.clear()
    
    def test_memory_store_success(self, client, mock_user, mock_db):
        """Test successful memory storage"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_stored_memory = {
            "id": 123,
            "content_id": "mem_456",
            "content": "Blockchain technology is reshaping financial services",
            "memory_type": "insight",
            "metadata": {
                "platform": "twitter",
                "engagement_rate": 5.8,
                "tags": ["blockchain", "fintech"]
            },
            "vector_indexed": True,
            "created_at": datetime.utcnow()
        }
        
        with patch('backend.api.vector_search.memory_service') as mock_service, \
             patch('backend.api.vector_search.clean_text_input') as mock_clean, \
             patch('backend.api.vector_search.validate_text_length') as mock_validate:
            
            mock_clean.return_value = "Blockchain technology is reshaping financial services"
            mock_validate.return_value = None
            mock_service.store_memory.return_value = mock_stored_memory
            
            response = client.post(
                "/api/vector/store",
                json={
                    "content": "Blockchain technology is reshaping financial services",
                    "memory_type": "insight",
                    "metadata": {
                        "platform": "twitter",
                        "engagement_rate": 5.8
                    },
                    "tags": ["blockchain", "fintech"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["memory"]["id"] == 123
            assert data["memory"]["content_id"] == "mem_456"
            assert data["memory"]["memory_type"] == "insight"
            assert data["memory"]["vector_indexed"] is True
        
        app.dependency_overrides.clear()
    
    def test_memory_store_validation_errors(self, client, mock_user, mock_db):
        """Test memory store validation errors"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Content too short
        response = client.post(
            "/api/vector/store",
            json={
                "content": "Short",  # Less than 10 characters
                "memory_type": "insight",
                "metadata": {},
                "tags": []
            }
        )
        assert response.status_code == 422
        
        # Content too long
        response = client.post(
            "/api/vector/store",
            json={
                "content": "A" * 10001,  # Exceeds 10000 character limit
                "memory_type": "insight",
                "metadata": {},
                "tags": []
            }
        )
        assert response.status_code == 422
        
        # Missing required fields
        response = client.post(
            "/api/vector/store",
            json={
                "content": "Valid content for testing memory storage functionality"
                # Missing memory_type
            }
        )
        assert response.status_code == 422
        
        app.dependency_overrides.clear()
    
    def test_memory_store_service_error(self, client, mock_user, mock_db):
        """Test memory store service error handling"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        with patch('backend.api.vector_search.memory_service') as mock_service, \
             patch('backend.api.vector_search.clean_text_input') as mock_clean, \
             patch('backend.api.vector_search.validate_text_length') as mock_validate:
            
            mock_clean.return_value = "Valid content"
            mock_validate.return_value = None
            mock_service.store_memory.side_effect = Exception("Vector indexing failed")
            
            response = client.post(
                "/api/vector/store",
                json={
                    "content": "Valid content for testing error handling",
                    "memory_type": "insight",
                    "metadata": {},
                    "tags": []
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Error storing memory" in data["detail"]
        
        app.dependency_overrides.clear()
    
    def test_vector_analytics_retrieval(self, client, mock_user, mock_db):
        """Test vector search analytics"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_analytics = {
            "total_memories": 1250,
            "memory_types": {
                "research": 450,
                "insight": 380,
                "content": 280,
                "template": 140
            },
            "vector_index_stats": {
                "total_vectors": 1245,
                "indexed_today": 25,
                "avg_similarity_score": 0.76,
                "search_performance": {
                    "avg_query_time": 0.045,
                    "cache_hit_rate": 0.82
                }
            },
            "popular_queries": [
                {"query": "AI trends", "count": 45, "avg_score": 0.84},
                {"query": "social media strategy", "count": 38, "avg_score": 0.79},
                {"query": "content marketing", "count": 32, "avg_score": 0.81}
            ],
            "content_categories": {
                "technology": 0.35,
                "business": 0.28,
                "marketing": 0.22,
                "other": 0.15
            }
        }
        
        with patch('backend.api.vector_search.memory_service') as mock_service:
            mock_service.analyze_content_performance.return_value = mock_analytics
            
            response = client.get("/api/vector/analytics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_memories"] == 1250
            assert "memory_types" in data
            assert "vector_index_stats" in data
            assert len(data["popular_queries"]) == 3
            assert data["vector_index_stats"]["avg_query_time"] == 0.045
        
        app.dependency_overrides.clear()
    
    def test_vector_search_performance_optimization(self, client, mock_user, mock_db):
        """Test vector search performance optimization"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Test caching behavior
        with patch('backend.api.vector_search.memory_service') as mock_service:
            mock_service.search_similar_memories.return_value = []
            
            # Make multiple identical requests
            for _ in range(3):
                response = client.post(
                    "/api/vector/search",
                    json={
                        "query": "identical query for caching test",
                        "limit": 5,
                        "threshold": 0.7
                    }
                )
                assert response.status_code == 200
            
            # Service should be called for each request (caching would be at service level)
            assert mock_service.search_similar_memories.call_count == 3
        
        app.dependency_overrides.clear()
    
    def test_vector_search_edge_cases(self, client, mock_user, mock_db):
        """Test vector search edge cases"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        with patch('backend.api.vector_search.memory_service') as mock_service, \
             patch('backend.api.vector_search.clean_text_input') as mock_clean, \
             patch('backend.api.vector_search.validate_text_length') as mock_validate:
            
            # Test with no results
            mock_clean.return_value = "obscure query"
            mock_validate.return_value = None
            mock_service.search_similar_memories.return_value = []
            
            response = client.post(
                "/api/vector/search",
                json={
                    "query": "obscure query with no matches",
                    "limit": 10,
                    "threshold": 0.9
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_results"] == 0
            assert len(data["results"]) == 0
            
            # Test with very high threshold
            response = client.post(
                "/api/vector/search",
                json={
                    "query": "test query",
                    "limit": 5,
                    "threshold": 0.99
                }
            )
            
            assert response.status_code == 200
        
        app.dependency_overrides.clear()
    
    def test_vector_search_special_characters(self, client, mock_user, mock_db):
        """Test vector search with special characters and unicode"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        special_queries = [
            "AI & ML trends 🤖",
            "Café analytics ☕",
            "データサイエンス",  # Japanese
            "Künstliche Intelligenz",  # German
            "المعلوماتية"  # Arabic
        ]
        
        with patch('backend.api.vector_search.memory_service') as mock_service, \
             patch('backend.api.vector_search.clean_text_input') as mock_clean, \
             patch('backend.api.vector_search.validate_text_length') as mock_validate:
            
            mock_validate.return_value = None
            mock_service.search_similar_memories.return_value = []
            
            for query in special_queries:
                mock_clean.return_value = query
                
                response = client.post(
                    "/api/vector/search",
                    json={
                        "query": query,
                        "limit": 5,
                        "threshold": 0.7
                    }
                )
                
                # Should handle special characters gracefully
                assert response.status_code == 200
        
        app.dependency_overrides.clear()
    
    def test_memory_bulk_operations(self, client, mock_user, mock_db):
        """Test bulk memory operations"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        bulk_memories = [
            {
                "content": "First memory content about AI trends",
                "memory_type": "research",
                "tags": ["AI", "trends"]
            },
            {
                "content": "Second memory about machine learning applications",
                "memory_type": "insight",
                "tags": ["ML", "applications"]
            },
            {
                "content": "Third memory about data science best practices",
                "memory_type": "template",
                "tags": ["data", "science"]
            }
        ]
        
        with patch('backend.api.vector_search.memory_service') as mock_service:
            mock_service.bulk_store_memories.return_value = {
                "stored": 3,
                "failed": 0,
                "memory_ids": ["mem_1", "mem_2", "mem_3"]
            }
            
            response = client.post(
                "/api/vector/bulk-store",
                json={"memories": bulk_memories}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["stored"] == 3
            assert data["failed"] == 0
            assert len(data["memory_ids"]) == 3
        
        app.dependency_overrides.clear()
    
    def test_vector_search_authentication_required(self, client):
        """Test that vector search endpoints require authentication"""
        endpoints = [
            ("/api/vector/search", "POST", {"query": "test", "limit": 5}),
            ("/api/vector/content-creation-search", "POST", {"topic": "test", "platform": "twitter"}),
            ("/api/vector/store", "POST", {"content": "test content", "memory_type": "insight"}),
            ("/api/vector/analytics", "GET", None)
        ]
        
        for endpoint, method, json_data in endpoints:
            if method == "POST":
                response = client.post(endpoint, json=json_data)
            else:
                response = client.get(endpoint)
            
            assert response.status_code in [401, 403]
    
    def test_vector_search_rate_limiting_simulation(self, client, mock_user, mock_db):
        """Test vector search rate limiting behavior"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        with patch('backend.api.vector_search.memory_service') as mock_service:
            mock_service.search_similar_memories.return_value = []
            
            # Simulate rapid requests
            responses = []
            for i in range(10):
                response = client.post(
                    "/api/vector/search",
                    json={
                        "query": f"rapid query {i}",
                        "limit": 5,
                        "threshold": 0.7
                    }
                )
                responses.append(response)
            
            # All should succeed (rate limiting would be implemented at infrastructure level)
            for response in responses:
                assert response.status_code == 200
        
        app.dependency_overrides.clear()


class TestVectorSearchPerformance:
    """Performance tests for vector search API"""
    
    def test_large_result_set_handling(self, client, mock_user, mock_db):
        """Test handling of large result sets"""
        # Test performance with large numbers of results
        pass
    
    def test_complex_query_performance(self, client, mock_user, mock_db):
        """Test performance with complex queries"""
        # Test performance with complex search queries
        pass
    
    def test_concurrent_search_performance(self, client, mock_user, mock_db):
        """Test concurrent search performance"""
        # Test performance under concurrent load
        pass


class TestVectorSearchIntegration:
    """Integration tests for vector search API"""
    
    def test_end_to_end_memory_workflow(self, client, test_db, test_user):
        """Test complete memory workflow: store -> search -> retrieve"""
        # Test: store memory -> search -> get results -> validate accuracy
        pass
    
    def test_cross_platform_memory_search(self, client, test_db, test_user):
        """Test memory search across different platforms"""
        pass
    
    def test_memory_quality_and_relevance(self, client, test_db, test_user):
        """Test memory quality and search relevance"""
        pass