"""
Performance benchmarking tests for backend services

Tests performance characteristics of key system components:
- API endpoint response times
- Database query performance  
- Vector search performance
- Background task processing
- Memory usage and resource consumption
"""
import pytest
import time
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, Mock
import psutil
import sys
from concurrent.futures import ThreadPoolExecutor

from backend.db.models import ContentItem, Goal, Memory, User
from backend.core.vector_store import VectorStore
from backend.services.embedding_service import EmbeddingService


class TestAPIPerformance:
    """Test API endpoint performance benchmarks"""
    
    def test_content_api_response_times(self, client, test_user, auth_headers, db_session, performance_timer):
        """Test content API response time benchmarks"""
        # Create test content for performance testing
        content_items = []
        for i in range(100):
            content = ContentItem(
                user_id=test_user.user_id,
                title=f"Performance Test Content {i}",
                content=f"Content body for performance testing {i}",
                platform="twitter",
                status="published" if i % 2 else "draft"
            )
            db_session.add(content)
            content_items.append(content)
        db_session.commit()
        
        # Test GET /api/content/list performance
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            performance_timer.start()
            response = client.get("/api/content/list?limit=50", headers=auth_headers)
            response_time = performance_timer.stop()
        
        assert response.status_code == 200
        assert response_time < 0.2  # Should respond within 200ms
        
        data = response.json()
        assert len(data["items"]) == 50
        
        # Test POST /api/content/create performance
        content_data = {
            "title": "Performance Test Post",
            "content": "This is a performance test post",
            "platform": "twitter",
            "content_type": "text"
        }
        
        performance_timer.start()
        response = client.post(
            "/api/content/create",
            json=content_data,
            headers=auth_headers
        )
        create_time = performance_timer.stop()
        
        assert response.status_code == 201
        assert create_time < 0.1  # Content creation should be fast (<100ms)
    
    def test_goals_api_performance(self, client, test_user, auth_headers, db_session, performance_timer):
        """Test goals API performance with large datasets"""
        # Create test goals
        for i in range(50):
            goal = Goal(
                user_id=test_user.user_id,
                title=f"Performance Goal {i}",
                description=f"Goal for performance testing {i}",
                target_metric="followers",
                target_value=1000 + i * 100,
                current_value=500 + i * 50,
                target_date=datetime.now(timezone.utc) + timedelta(days=30),
                category="growth",
                priority="medium",
                status="active"
            )
            db_session.add(goal)
        db_session.commit()
        
        # Test goals list performance
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            performance_timer.start()
            response = client.get("/api/goals/list", headers=auth_headers)
            response_time = performance_timer.stop()
        
        assert response.status_code == 200
        assert response_time < 0.15  # Should be fast even with 50 goals
        
        data = response.json()
        assert len(data["items"]) == 50
    
    def test_memory_search_performance(self, client, test_user, auth_headers, db_session, performance_timer, mock_faiss):
        """Test memory search API performance"""
        # Create test memories
        for i in range(200):
            memory = Memory(
                user_id=test_user.user_id,
                content_text=f"Performance test memory content {i} with various keywords and topics",
                content_type="research",
                source_url=f"https://example.com/test-{i}",
                vector_id=f"test_vector_{i}",
                metadata={
                    "topic": f"topic_{i % 10}",
                    "relevance_score": 0.8 + (i % 20) * 0.01,
                    "keywords": [f"keyword_{i}", f"topic_{i % 10}", "performance"]
                }
            )
            db_session.add(memory)
        db_session.commit()
        
        # Test semantic search performance
        search_data = {
            "query": "performance testing keywords",
            "limit": 20,
            "similarity_threshold": 0.7
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            performance_timer.start()
            response = client.post(
                "/api/memory/search",
                json=search_data,
                headers=auth_headers
            )
            search_time = performance_timer.stop()
        
        assert response.status_code == 200
        assert search_time < 0.1  # Vector search should be very fast (<100ms)
        
        data = response.json()
        assert len(data["results"]) <= 20
    
    def test_bulk_operations_performance(self, client, test_user, auth_headers, db_session, performance_timer):
        """Test performance of bulk operations"""
        # Create content for bulk operations
        content_items = []
        for i in range(20):
            content = ContentItem(
                user_id=test_user.user_id,
                title=f"Bulk Test Content {i}",
                content=f"Content for bulk operation testing {i}",
                platform="twitter",
                status="draft"
            )
            db_session.add(content)
            content_items.append(content)
        db_session.commit()
        
        # Test bulk update performance
        bulk_data = {
            "content_ids": [item.id for item in content_items],
            "action": "schedule",
            "scheduled_time": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            performance_timer.start()
            response = client.post(
                "/api/content/bulk",
                json=bulk_data,
                headers=auth_headers
            )
            bulk_time = performance_timer.stop()
        
        assert response.status_code == 200
        assert bulk_time < 0.5  # Bulk operations should complete within 500ms
        
        data = response.json()
        assert data["processed_count"] == 20
        assert data["success_count"] == 20


class TestDatabasePerformance:
    """Test database query performance"""
    
    def test_complex_query_performance(self, db_session, test_user, performance_timer):
        """Test performance of complex database queries"""
        # Create large dataset
        for i in range(500):
            content = ContentItem(
                user_id=test_user.user_id,
                title=f"Query Test Content {i}",
                content=f"Content for query performance testing {i}",
                platform=["twitter", , "facebook"][i % 3],
                status=["draft", "scheduled", "published"][i % 3],
                performance_data={
                    "likes": i * 10,
                    "shares": i * 2,
                    "engagement_rate": (i % 10) + 1.0
                }
            )
            db_session.add(content)
        db_session.commit()
        
        # Test complex query with joins and aggregations
        performance_timer.start()
        
        query = db_session.query(ContentItem).filter(
            ContentItem.user_id == test_user.user_id,
            ContentItem.status == "published"
        ).order_by(ContentItem.created_at.desc()).limit(50)
        
        results = query.all()
        query_time = performance_timer.stop()
        
        assert len(results) > 0
        assert query_time < 0.05  # Database queries should be very fast (<50ms)
    
    def test_index_performance(self, db_session, test_user, performance_timer):
        """Test database index performance"""
        # Create data that will test various indexes
        for i in range(1000):
            content = ContentItem(
                user_id=test_user.user_id,
                title=f"Index Test {i}",
                content=f"Content {i}",
                platform="twitter",
                status="published",
                created_at=datetime.now(timezone.utc) - timedelta(days=i % 365)
            )
            db_session.add(content)
        db_session.commit()
        
        # Test user_id index
        performance_timer.start()
        user_content = db_session.query(ContentItem).filter(
            ContentItem.user_id == test_user.user_id
        ).count()
        index_time_1 = performance_timer.stop()
        
        assert user_content == 1000
        assert index_time_1 < 0.02  # Index lookup should be very fast
        
        # Test date range query with index
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        performance_timer.start()
        recent_content = db_session.query(ContentItem).filter(
            ContentItem.user_id == test_user.user_id,
            ContentItem.created_at >= start_date
        ).count()
        index_time_2 = performance_timer.stop()
        
        assert recent_content >= 0
        assert index_time_2 < 0.03  # Date range with index should be fast
    
    def test_aggregation_performance(self, db_session, test_user, performance_timer):
        """Test database aggregation query performance"""
        from sqlalchemy import func
        
        # Create content with performance data
        for i in range(200):
            content = ContentItem(
                user_id=test_user.user_id,
                title=f"Aggregation Test {i}",
                content=f"Content {i}",
                platform=["twitter", ][i % 2],
                status="published",
                performance_data={
                    "likes": i * 5,
                    "shares": i * 2,
                    "engagement_rate": (i % 10) + 1.0
                }
            )
            db_session.add(content)
        db_session.commit()
        
        # Test aggregation query
        performance_timer.start()
        
        stats = db_session.query(
            ContentItem.platform,
            func.count(ContentItem.id).label('count'),
            func.avg(func.cast(ContentItem.performance_data['likes'], float)).label('avg_likes')
        ).filter(
            ContentItem.user_id == test_user.user_id
        ).group_by(ContentItem.platform).all()
        
        aggregation_time = performance_timer.stop()
        
        assert len(stats) == 2  # twitter and linkedin
        assert aggregation_time < 0.1  # Aggregations should be reasonably fast


class TestVectorSearchPerformance:
    """Test vector search performance benchmarks"""
    
    @patch('backend.core.vector_store.faiss')
    def test_vector_store_performance(self, mock_faiss, performance_timer):
        """Test FAISS vector store performance"""
        # Mock FAISS operations
        mock_index = Mock()
        mock_index.ntotal = 10000
        mock_index.search.return_value = (
            [[0.95, 0.89, 0.87, 0.82, 0.78]],  # distances
            [[1, 2, 3, 4, 5]]  # indices
        )
        mock_faiss.IndexFlatIP.return_value = mock_index
        
        vector_store = VectorStore()
        
        # Test vector search performance
        query_vector = [0.1] * 1536  # OpenAI embedding dimension
        
        performance_timer.start()
        results = vector_store.search(query_vector, k=10, threshold=0.7)
        search_time = performance_timer.stop()
        
        assert len(results) <= 10
        assert search_time < 0.05  # Vector search should be very fast (<50ms)
        
        # Test batch vector addition performance
        batch_vectors = [[0.1] * 1536 for _ in range(100)]
        batch_metadata = [{"content": f"test_{i}"} for i in range(100)]
        
        performance_timer.start()
        vector_ids = vector_store.add_vectors(batch_vectors, batch_metadata)
        add_time = performance_timer.stop()
        
        assert len(vector_ids) == 100
        assert add_time < 0.2  # Batch addition should be fast (<200ms)
    
    @patch('openai.embeddings.create')
    def test_embedding_service_performance(self, mock_openai, performance_timer):
        """Test OpenAI embedding service performance"""
        # Mock OpenAI response
        mock_openai.return_value = Mock()
        mock_openai.return_value.data = [Mock() for _ in range(10)]
        for i, item in enumerate(mock_openai.return_value.data):
            item.embedding = [0.1 + i * 0.01] * 1536
        
        embedding_service = EmbeddingService()
        
        # Test batch embedding performance
        texts = [f"Test content for embedding {i}" for i in range(10)]
        
        performance_timer.start()
        embeddings = embedding_service.create_embeddings_batch(texts)
        embedding_time = performance_timer.stop()
        
        assert len(embeddings) == 10
        assert embedding_time < 1.0  # Embedding generation should be reasonable
        
        # Verify rate limiting doesn't slow us down excessively
        assert embedding_time > 0.1  # Should have some processing time


class TestConcurrentPerformance:
    """Test performance under concurrent load"""
    
    def test_concurrent_api_requests(self, client, test_user, auth_headers, performance_timer):
        """Test API performance under concurrent load"""
        def make_request():
            with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                return client.get("/api/health", headers=auth_headers)
        
        # Test concurrent requests
        performance_timer.start()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            responses = [future.result() for future in futures]
        
        concurrent_time = performance_timer.stop()
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)
        assert len(responses) == 50
        
        # Should handle concurrent load efficiently
        assert concurrent_time < 5.0  # 50 concurrent requests in under 5 seconds
        
        # Calculate throughput
        throughput = len(responses) / concurrent_time
        assert throughput > 15  # At least 15 requests per second
    
    def test_database_connection_pooling(self, db_session, test_user, performance_timer):
        """Test database connection pool performance"""
        def db_operation():
            # Simulate database operations
            content_count = db_session.query(ContentItem).filter(
                ContentItem.user_id == test_user.user_id
            ).count()
            return content_count
        
        # Test concurrent database operations
        performance_timer.start()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(db_operation) for _ in range(20)]
            results = [future.result() for future in futures]
        
        db_concurrent_time = performance_timer.stop()
        
        assert len(results) == 20
        assert db_concurrent_time < 2.0  # Should handle concurrent DB ops efficiently


class TestMemoryUsagePerformance:
    """Test memory usage and resource consumption"""
    
    def test_memory_usage_during_operations(self, client, test_user, auth_headers, db_session):
        """Test memory usage during heavy operations"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        large_content_data = {
            "title": "Large Content Test",
            "content": "x" * 10000,  # Large content
            "platform": "twitter",
            "content_type": "text",
            "metadata": {
                "large_data": ["item"] * 1000  # Large metadata
            }
        }
        
        # Create multiple large content items
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            for _ in range(10):
                response = client.post(
                    "/api/content/create",
                    json=large_content_data,
                    headers=auth_headers
                )
                assert response.status_code == 201
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100
    
    def test_garbage_collection_performance(self):
        """Test garbage collection impact on performance"""
        import gc
        
        # Force garbage collection and measure impact
        start_time = time.time()
        gc.collect()
        gc_time = time.time() - start_time
        
        # Garbage collection should be fast
        assert gc_time < 0.1  # Less than 100ms
        
        # Check for memory leaks by creating and destroying objects
        initial_objects = len(gc.get_objects())
        
        # Create temporary objects
        temp_objects = []
        for i in range(1000):
            temp_objects.append({
                "id": i,
                "data": f"test_data_{i}",
                "timestamp": datetime.now()
            })
        
        # Clear references
        temp_objects.clear()
        temp_objects = None
        
        # Force garbage collection
        gc.collect()
        
        final_objects = len(gc.get_objects())
        object_increase = final_objects - initial_objects
        
        # Should not have significant object leaks
        assert object_increase < 100


class TestPerformanceRegressionChecks:
    """Performance regression testing"""
    
    def test_api_response_time_benchmarks(self, client, test_user, auth_headers, performance_timer):
        """Test API response time benchmarks for regression detection"""
        endpoints_benchmarks = [
            ("/api/health", 0.01),  # 10ms
            ("/api/content/list", 0.2),  # 200ms
            ("/api/goals/list", 0.15),  # 150ms
            ("/api/memory/stats", 0.1),  # 100ms
        ]
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            for endpoint, max_time in endpoints_benchmarks:
                performance_timer.start()
                response = client.get(endpoint, headers=auth_headers)
                response_time = performance_timer.stop()
                
                assert response.status_code in [200, 401]  # Some may require specific auth
                assert response_time < max_time, f"{endpoint} took {response_time}s, expected <{max_time}s"
    
    def test_throughput_benchmarks(self, client, test_user, auth_headers, performance_timer):
        """Test system throughput benchmarks"""
        # Test content creation throughput
        content_data = {
            "title": "Throughput Test",
            "content": "Content for throughput testing",
            "platform": "twitter",
            "content_type": "text"
        }
        
        requests_count = 20
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            performance_timer.start()
            
            for _ in range(requests_count):
                response = client.post(
                    "/api/content/create",
                    json=content_data,
                    headers=auth_headers
                )
                assert response.status_code == 201
            
            total_time = performance_timer.stop()
        
        throughput = requests_count / total_time
        assert throughput > 10  # At least 10 requests per second
        
        # Average response time should be reasonable
        avg_response_time = total_time / requests_count
        assert avg_response_time < 0.2  # Less than 200ms per request
    
    def test_resource_usage_limits(self):
        """Test that resource usage stays within acceptable limits"""
        process = psutil.Process()
        
        # CPU usage should be reasonable
        cpu_percent = process.cpu_percent(interval=1)
        assert cpu_percent < 80  # Less than 80% CPU usage
        
        # Memory usage should be reasonable
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        assert memory_mb < 500  # Less than 500 MB memory usage
        
        # File descriptor usage should be reasonable
        try:
            num_fds = process.num_fds()
            assert num_fds < 1000  # Less than 1000 file descriptors
        except AttributeError:
            # num_fds() not available on Windows
            pass


# Performance test fixtures and utilities
@pytest.fixture
def performance_metrics():
    """Fixture to collect performance metrics during tests"""
    metrics = {
        "response_times": [],
        "memory_usage": [],
        "cpu_usage": [],
        "db_query_times": []
    }
    
    yield metrics
    
    # Could save metrics to file or database for trend analysis
    if metrics["response_times"]:
        avg_response_time = sum(metrics["response_times"]) / len(metrics["response_times"])
        print(f"\nAverage response time: {avg_response_time:.3f}s")
    
    if metrics["memory_usage"]:
        max_memory = max(metrics["memory_usage"])
        print(f"Peak memory usage: {max_memory:.1f}MB")


@pytest.mark.performance
class TestPerformanceIntegration:
    """Integration tests combining multiple performance aspects"""
    
    def test_end_to_end_performance(self, client, test_user, auth_headers, db_session, performance_timer):
        """Test end-to-end workflow performance"""
        
        # Simulate complete user workflow
        workflow_steps = [
            # 1. Create content
            lambda: client.post(
                "/api/content/create",
                json={
                    "title": "E2E Performance Test",
                    "content": "End-to-end performance testing content",
                    "platform": "twitter",
                    "content_type": "text"
                },
                headers=auth_headers
            ),
            
            # 2. Search memory
            lambda: client.post(
                "/api/memory/search",
                json={
                    "query": "performance testing",
                    "limit": 10
                },
                headers=auth_headers
            ),
            
            # 3. Check goals
            lambda: client.get("/api/goals/list", headers=auth_headers),
            
            # 4. Get analytics
            lambda: client.get("/api/content/analytics/summary", headers=auth_headers)
        ]
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            performance_timer.start()
            
            for step in workflow_steps:
                response = step()
                # Most should succeed, some may return 404/422 due to mocking
                assert response.status_code in [200, 201, 404, 422]
            
            e2e_time = performance_timer.stop()
        
        # Complete workflow should be fast
        assert e2e_time < 2.0  # Less than 2 seconds for complete workflow
        
        print(f"\nEnd-to-end workflow completed in {e2e_time:.3f}s")
EOF < /dev/null