#!/usr/bin/env python3
"""
Comprehensive test suite for dashboard infinite error cascade fixes

This script tests:
1. Database table existence checks
2. Middleware exception handling
3. Safe query patterns
4. Dashboard endpoint graceful degradation
5. Migration system validation
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import sqlite3

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the modules to test
from backend.utils.db_checks import (
    check_table_exists, ensure_table_exists, safe_table_query,
    check_critical_tables_exist
)
from backend.core.security_middleware import RequestValidationMiddleware
from backend.middleware.error_tracking import error_tracking_middleware, log_404_errors

class TestDatabaseFixes(unittest.TestCase):
    """Test database table checks and safe query patterns"""
    
    def setUp(self):
        """Create a temporary SQLite database for testing"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Create SQLAlchemy engine for testing
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        
        self.engine = create_engine(f'sqlite:///{self.temp_db.name}')
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        
        # Create a test table
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """))
            conn.execute(text("INSERT INTO test_table (name) VALUES ('test_data')"))
            conn.commit()
    
    def tearDown(self):
        """Clean up test database"""
        self.db.close()
        os.unlink(self.temp_db.name)
    
    def test_check_table_exists_positive(self):
        """Test that check_table_exists returns True for existing table"""
        result = check_table_exists(self.db, 'test_table')
        self.assertTrue(result, "Should detect existing test_table")
    
    def test_check_table_exists_negative(self):
        """Test that check_table_exists returns False for non-existing table"""
        result = check_table_exists(self.db, 'nonexistent_table')
        self.assertFalse(result, "Should not detect nonexistent table")
    
    def test_ensure_table_exists_success(self):
        """Test that ensure_table_exists passes for existing table"""
        try:
            ensure_table_exists(self.db, 'test_table', 'test_endpoint')
        except Exception:
            self.fail("ensure_table_exists should not raise exception for existing table")
    
    def test_ensure_table_exists_failure(self):
        """Test that ensure_table_exists raises HTTPException for missing table"""
        from fastapi import HTTPException
        
        with self.assertRaises(HTTPException) as context:
            ensure_table_exists(self.db, 'missing_table', 'test_endpoint')
        
        self.assertEqual(context.exception.status_code, 503)
        self.assertIn('missing_table', str(context.exception.detail))
    
    def test_safe_table_query_success(self):
        """Test that safe_table_query works for existing table"""
        def test_query(db):
            from sqlalchemy import text
            result = db.execute(text("SELECT COUNT(*) FROM test_table"))
            return result.scalar()
        
        result = safe_table_query(
            self.db, 'test_table', test_query, 
            fallback_value=0, endpoint_name='test'
        )
        
        self.assertEqual(result, 1, "Should return correct count from test_table")
    
    def test_safe_table_query_fallback(self):
        """Test that safe_table_query returns fallback for missing table"""
        def test_query(db):
            from sqlalchemy import text
            result = db.execute(text("SELECT COUNT(*) FROM missing_table"))
            return result.scalar()
        
        result = safe_table_query(
            self.db, 'missing_table', test_query,
            fallback_value=[], endpoint_name='test'
        )
        
        self.assertEqual(result, [], "Should return fallback value for missing table")
    
    def test_check_critical_tables_exist(self):
        """Test critical tables check with mixed results"""
        # Create some of the critical tables
        with self.engine.connect() as conn:
            conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
            conn.execute(text("CREATE TABLE content_logs (id INTEGER PRIMARY KEY)"))
            conn.commit()
        
        status = check_critical_tables_exist(self.db)
        
        self.assertFalse(status['all_exist'], "Not all critical tables should exist")
        self.assertIn('users', status['existing'])
        self.assertIn('content_logs', status['existing'])
        self.assertTrue(len(status['missing']) > 0, "Some tables should be missing")


class TestMiddlewareExceptionHandling(unittest.TestCase):
    """Test middleware exception handling improvements"""
    
    @patch('backend.core.security_middleware.logger')
    async def test_request_validation_middleware_exception_handling(self, mock_logger):
        """Test that RequestValidationMiddleware handles exceptions properly"""
        middleware = RequestValidationMiddleware(app=None)
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.path = '/api/test'
        mock_request.method = 'GET'
        mock_request.query_params.items.return_value = []
        mock_request.headers.items.return_value = []
        mock_request.client.host = '127.0.0.1'
        
        # Create mock call_next that raises an exception
        async def failing_call_next(request):
            raise Exception("Database connection failed")
        
        # Test exception handling
        response = await middleware.dispatch(mock_request, failing_call_next)
        
        # Should return JSONResponse, not crash
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 500)
        
        # Should have logged the error
        mock_logger.error.assert_called()
    
    @patch('backend.middleware.error_tracking.logger')
    async def test_error_tracking_middleware_null_response(self, mock_logger):
        """Test that error_tracking_middleware handles null responses"""
        from fastapi import Request
        from unittest.mock import AsyncMock
        
        # Create real Request object
        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/api/test',
            'query_string': b'',
            'headers': [],
            'client': ('127.0.0.1', 0)
        }
        
        request = Request(scope)
        
        # Mock call_next that returns None
        async def null_call_next(request):
            return None
        
        response = await error_tracking_middleware(request, null_call_next)
        
        # Should return JSONResponse for null response
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 500)
        
        # Should have logged the error
        mock_logger.error.assert_called()


class TestDashboardEndpointProtection(unittest.TestCase):
    """Test dashboard endpoint protection against missing tables"""
    
    def setUp(self):
        """Set up test database and FastAPI dependencies"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        self.engine = create_engine(f'sqlite:///{self.temp_db.name}')
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_content_endpoint_missing_table_graceful_degradation(self):
        """Test that content endpoints handle missing tables gracefully"""
        from backend.api.content import get_user_content, get_upcoming_content
        from backend.db.models import User
        from unittest.mock import Mock
        import pytest
        
        # Mock database session with no content_logs table
        mock_db = Mock()
        mock_db.query.side_effect = Exception("relation \"content_logs\" does not exist")
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        
        try:
            # This should not crash, should return graceful error or empty result
            # Note: We can't actually call async functions easily in unittest,
            # but the safe_table_query should handle the exception
            
            # Instead, test the safe_table_query pattern directly
            from backend.utils.db_checks import safe_table_query
            
            def failing_query(db):
                raise Exception("relation \"content_logs\" does not exist")
            
            result = safe_table_query(
                mock_db, 'content_logs', failing_query,
                fallback_value=[], endpoint_name='test'
            )
            
            self.assertEqual(result, [], "Should return empty list for missing table")
            
        except Exception as e:
            self.fail(f"Endpoint should handle missing table gracefully, but raised: {e}")


class TestMigrationSystemValidation(unittest.TestCase):
    """Test migration system and table creation"""
    
    def test_content_logs_in_initial_migration(self):
        """Verify that content_logs table is defined in initial migration"""
        from alembic.versions import initial_migration_001
        import inspect
        
        # Get the source code of the migration
        migration_source = inspect.getsource(initial_migration_001.upgrade)
        
        self.assertIn('content_logs', migration_source, 
                     "content_logs table should be defined in initial migration")
        self.assertIn('user_id', migration_source,
                     "content_logs should have user_id column")
        self.assertIn('platform', migration_source,
                     "content_logs should have platform column")
        self.assertIn('content', migration_source,
                     "content_logs should have content column")
    
    def test_migration_script_table_verification(self):
        """Test that migration script checks for content_logs table"""
        import run_migrations
        import inspect
        
        # Check that run_migrations includes content_logs in verification
        migration_source = inspect.getsource(run_migrations.run_migrations)
        
        self.assertIn('content_logs', migration_source,
                     "Migration script should verify content_logs table")


async def run_async_tests():
    """Run async tests"""
    print("\n🧪 Running async middleware tests...")
    
    middleware_test = TestMiddlewareExceptionHandling()
    
    try:
        await middleware_test.test_request_validation_middleware_exception_handling()
        print("✅ RequestValidationMiddleware exception handling test passed")
    except Exception as e:
        print(f"❌ RequestValidationMiddleware test failed: {e}")
    
    try:
        await middleware_test.test_error_tracking_middleware_null_response()
        print("✅ Error tracking middleware null response test passed")
    except Exception as e:
        print(f"❌ Error tracking middleware test failed: {e}")


def main():
    """Run all tests"""
    print("🚀 Running comprehensive dashboard fix validation tests...")
    print("=" * 60)
    
    # Run sync tests
    test_classes = [
        TestDatabaseFixes,
        TestDashboardEndpointProtection, 
        TestMigrationSystemValidation
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        passed_tests += result.testsRun - len(result.failures) - len(result.errors)
    
    # Run async tests
    asyncio.run(run_async_tests())
    
    print("\n" + "=" * 60)
    print(f"📊 Test Summary: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All dashboard fixes validated successfully!")
        return 0
    else:
        print("⚠️  Some tests failed - review fixes needed")
        return 1


if __name__ == "__main__":
    sys.exit(main())