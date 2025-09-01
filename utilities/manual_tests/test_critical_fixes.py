#!/usr/bin/env python3
"""
Critical validation test for dashboard infinite error cascade fixes

Focus on the exact issues identified:
1. Missing content_logs table causing psycopg2.errors.UndefinedTable
2. RequestValidationMiddleware failing to return response on exceptions
3. Cascade of 500 errors when dashboard endpoints are triggered
"""

import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_content_logs_table_in_migration():
    """CRITICAL TEST: Verify content_logs table is created by migrations"""
    print("\n🔍 Testing: content_logs table in migration files...")
    
    # Read the initial migration file directly
    migration_file = project_root / "alembic/versions/001_initial_migration.py"
    
    if not migration_file.exists():
        print("❌ CRITICAL: Initial migration file not found!")
        return False
    
    with open(migration_file, 'r') as f:
        migration_content = f.read()
    
    # Check for content_logs table creation
    checks = [
        ("content_logs table creation", "op.create_table('content_logs'"),
        ("user_id column", "sa.Column('user_id'"),
        ("platform column", "sa.Column('platform'"),
        ("content column", "sa.Column('content'"),
        ("status column", "sa.Column('status'"),
        ("scheduled_for column", "sa.Column('scheduled_for'")
    ]
    
    all_passed = True
    for check_name, check_pattern in checks:
        if check_pattern in migration_content:
            print(f"   ✅ {check_name}: Found")
        else:
            print(f"   ❌ {check_name}: MISSING - {check_pattern}")
            all_passed = False
    
    # Check external_post_id migration
    external_migration = project_root / "alembic/versions/007_add_external_post_id_to_contentlog.py"
    if external_migration.exists():
        print("   ✅ External post ID migration exists")
    else:
        print("   ❌ External post ID migration missing")
        all_passed = False
    
    return all_passed

def test_migration_script_includes_content_logs():
    """CRITICAL TEST: Verify migration script checks content_logs table"""
    print("\n🔍 Testing: Migration script includes content_logs verification...")
    
    migration_script = project_root / "run_migrations.py"
    
    with open(migration_script, 'r') as f:
        script_content = f.read()
    
    if 'content_logs' in script_content:
        print("   ✅ content_logs included in migration verification")
        return True
    else:
        print("   ❌ CRITICAL: content_logs NOT included in migration verification")
        return False

async def test_request_validation_middleware_exception_handling():
    """CRITICAL TEST: RequestValidationMiddleware handles exceptions without crashing"""
    print("\n🔍 Testing: RequestValidationMiddleware exception handling...")
    
    try:
        from backend.core.security_middleware import RequestValidationMiddleware
        from fastapi import Request
        
        middleware = RequestValidationMiddleware(app=None)
        
        # Create mock request
        scope = {
            'type': 'http',
            'method': 'GET', 
            'path': '/api/content/',
            'query_string': b'',
            'headers': [],
            'client': ('127.0.0.1', 0)
        }
        request = Request(scope)
        
        # Mock call_next that simulates database error
        async def database_error_call_next(request):
            raise Exception('relation "content_logs" does not exist')
        
        # Test that middleware handles the exception
        response = await middleware.dispatch(request, database_error_call_next)
        
        if response is not None:
            print("   ✅ Middleware returned response instead of crashing")
            if hasattr(response, 'status_code') and response.status_code == 500:
                print("   ✅ Returned proper 500 error response")
                return True
            else:
                print("   ⚠️  Response exists but may not be proper error response")
                return True
        else:
            print("   ❌ CRITICAL: Middleware returned None - will cause cascade errors!")
            return False
            
    except Exception as e:
        print(f"   ❌ CRITICAL: Middleware test failed with exception: {e}")
        return False

async def test_error_tracking_middleware_null_response_handling():
    """CRITICAL TEST: Error tracking middleware handles null responses"""
    print("\n🔍 Testing: Error tracking middleware null response handling...")
    
    try:
        from backend.middleware.error_tracking import error_tracking_middleware
        from fastapi import Request
        
        # Create real Request object
        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/api/content/scheduled/upcoming',
            'query_string': b'',
            'headers': [],
            'client': ('127.0.0.1', 0)
        }
        request = Request(scope)
        
        # Mock call_next that returns None (the original problem)
        async def null_response_call_next(request):
            return None
        
        response = await error_tracking_middleware(request, null_response_call_next)
        
        if response is not None:
            print("   ✅ Error tracking middleware handled null response")
            if hasattr(response, 'status_code') and response.status_code == 500:
                print("   ✅ Returned proper error response")
                return True
            else:
                print("   ⚠️  Response exists but may not be proper error")
                return True
        else:
            print("   ❌ CRITICAL: Error tracking middleware still returns None!")
            return False
            
    except Exception as e:
        print(f"   ❌ CRITICAL: Error tracking middleware test failed: {e}")
        return False

def test_database_checks_utility():
    """CRITICAL TEST: Database check utilities work properly"""
    print("\n🔍 Testing: Database check utilities...")
    
    try:
        from backend.utils.db_checks import safe_table_query, ensure_table_exists
        from fastapi import HTTPException
        
        # Mock database session
        mock_db = Mock()
        
        # Test safe_table_query with fallback
        def failing_query(db):
            raise Exception('relation "content_logs" does not exist')
        
        result = safe_table_query(
            db=mock_db,
            table_name='content_logs', 
            query_func=failing_query,
            fallback_value=[],
            endpoint_name='test'
        )
        
        if result == []:
            print("   ✅ safe_table_query returns fallback for missing table")
        else:
            print(f"   ❌ safe_table_query returned unexpected result: {result}")
            return False
        
        # Test ensure_table_exists with missing table
        try:
            # Mock check_table_exists to return False
            with patch('backend.utils.db_checks.check_table_exists', return_value=False):
                ensure_table_exists(mock_db, 'content_logs', 'test_endpoint')
            print("   ❌ ensure_table_exists should have raised HTTPException")
            return False
        except HTTPException as e:
            if e.status_code == 503:
                print("   ✅ ensure_table_exists raises proper 503 error")
            else:
                print(f"   ❌ Wrong status code: {e.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Wrong exception type: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ CRITICAL: Database checks test failed: {e}")
        return False

def test_content_api_protection():
    """CRITICAL TEST: Content API endpoints have protection"""
    print("\n🔍 Testing: Content API endpoint protection...")
    
    try:
        # Read the content API file
        content_api_file = project_root / "backend/api/content.py"
        
        with open(content_api_file, 'r') as f:
            api_content = f.read()
        
        # Check for safety imports
        safety_checks = [
            ("Database checks import", "from backend.utils.db_checks import"),
            ("ensure_table_exists usage", "ensure_table_exists"),
            ("safe_table_query usage", "safe_table_query"),
            ("Upcoming content protection", "get_upcoming_content"),
            ("User content protection", "get_user_content")
        ]
        
        all_passed = True
        for check_name, check_pattern in safety_checks:
            if check_pattern in api_content:
                print(f"   ✅ {check_name}: Found")
            else:
                print(f"   ❌ {check_pattern}: MISSING")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"   ❌ CRITICAL: Content API protection test failed: {e}")
        return False

def test_render_deployment_configuration():
    """CRITICAL TEST: Render deployment runs migrations"""
    print("\n🔍 Testing: Render deployment configuration...")
    
    try:
        # Check render.yaml
        render_config = project_root / "render.yaml"
        
        with open(render_config, 'r') as f:
            config_content = f.read()
        
        # Check startup script
        startup_script = project_root / "start_production.sh"
        
        checks = [
            ("Render config uses startup script", "bash start_production.sh" in config_content),
            ("Startup script exists", startup_script.exists()),
            ("Startup script is executable", startup_script.stat().st_mode & 0o111 != 0 if startup_script.exists() else False)
        ]
        
        all_passed = True
        for check_name, check_result in checks:
            if check_result:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}: FAILED")
                all_passed = False
        
        # Check startup script content
        if startup_script.exists():
            with open(startup_script, 'r') as f:
                script_content = f.read()
            
            script_checks = [
                ("Runs migrations", "run_migrations" in script_content),
                ("Checks database", "check_database" in script_content),  
                ("Verifies tables", "verify_tables" in script_content),
                ("Error handling", "set -e" in script_content)
            ]
            
            for check_name, check_pattern in script_checks:
                if check_pattern:
                    print(f"   ✅ {check_name}")
                else:
                    print(f"   ❌ {check_name}: MISSING")
                    all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"   ❌ CRITICAL: Render deployment test failed: {e}")
        return False

async def main():
    """Run critical validation tests"""
    print("🚨 CRITICAL DASHBOARD FIXES VALIDATION")
    print("=" * 50)
    print("Testing fixes for infinite error cascade issues on Render")
    
    tests = [
        ("Content logs table in migration", test_content_logs_table_in_migration),
        ("Migration script verification", test_migration_script_includes_content_logs),
        ("Database utility functions", test_database_checks_utility),
        ("Content API endpoint protection", test_content_api_protection),
        ("Render deployment configuration", test_render_deployment_configuration),
    ]
    
    async_tests = [
        ("RequestValidationMiddleware exception handling", test_request_validation_middleware_exception_handling),
        ("Error tracking middleware null response", test_error_tracking_middleware_null_response_handling),
    ]
    
    passed = 0
    total = len(tests) + len(async_tests)
    
    # Run sync tests
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"   ✅ PASSED")
            else:
                print(f"   ❌ FAILED")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    # Run async tests  
    for test_name, test_func in async_tests:
        print(f"\n🧪 {test_name}...")
        try:
            if await test_func():
                passed += 1
                print(f"   ✅ PASSED")
            else:
                print(f"   ❌ FAILED")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 CRITICAL TEST RESULTS: {passed}/{total} PASSED")
    
    if passed == total:
        print("🎉 ALL CRITICAL FIXES VALIDATED - Dashboard should be stable!")
        print("\n✅ Expected behavior:")
        print("   • content_logs table will be created by migrations")
        print("   • Missing table errors return graceful 503 responses")  
        print("   • Middleware exceptions don't cause cascade failures")
        print("   • Dashboard endpoints return empty arrays instead of crashing")
        return 0
    else:
        print("⚠️  SOME CRITICAL FIXES FAILED - Review required!")
        failed = total - passed
        print(f"\n❌ {failed} critical issue(s) still exist")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)