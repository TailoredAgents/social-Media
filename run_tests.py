#!/usr/bin/env python3
"""
Test runner script for the AI Social Media Content Agent
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and print the result"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=Path(__file__).parent
        )
        
        print(f"Command: {command}")
        print(f"Exit code: {result.returncode}")
        
        if result.stdout:
            print("\nSTDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Main test runner"""
    print("🚀 AI Social Media Content Agent - Test Suite")
    print("=" * 60)
    
    # Set environment variables for testing
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["SECRET_KEY"] = "test_secret_key_for_testing_only"
    os.environ["OPENAI_API_KEY"] = "test_openai_key"
    
    # Check if pytest is available
    print("\n📋 Checking test dependencies...")
    
    try:
        import pytest
        print("✅ pytest is available")
    except ImportError:
        print("❌ pytest not found. Installing test dependencies...")
        success = run_command(
            "pip install pytest pytest-cov pytest-asyncio pytest-mock pytest-env pytest-timeout",
            "Installing test dependencies"
        )
        if not success:
            print("❌ Failed to install test dependencies")
            return 1
    
    # Test categories to run
    test_categories = [
        {
            "name": "Multi-Tenancy Models",
            "command": "python -m pytest backend/tests/unit/test_multi_tenant_models.py -v",
            "required": True
        },
        {
            "name": "Permission System",
            "command": "python -m pytest backend/tests/unit/test_permissions.py -v",
            "required": True
        },
        {
            "name": "Tenant Isolation Middleware",
            "command": "python -m pytest backend/tests/unit/test_tenant_isolation.py -v",
            "required": True
        },
        {
            "name": "Organization APIs",
            "command": "python -m pytest backend/tests/integration/test_organization_apis.py -v",
            "required": True
        },
        {
            "name": "Social Platform APIs",
            "command": "python -m pytest backend/tests/integration/test_social_platform_apis.py -v",
            "required": False
        },
        {
            "name": "Notification System",
            "command": "python -m pytest backend/tests/integration/test_notification_system.py -v",
            "required": False
        },
        {
            "name": "All Unit Tests",
            "command": "python -m pytest backend/tests/unit/ -v",
            "required": False
        },
        {
            "name": "All Integration Tests",
            "command": "python -m pytest backend/tests/integration/ -v",
            "required": False
        }
    ]
    
    # Run tests
    results = {}
    
    for category in test_categories:
        success = run_command(category["command"], category["name"])
        results[category["name"]] = success
        
        if category["required"] and not success:
            print(f"❌ Required test category '{category['name']}' failed!")
            break
    
    # Generate test coverage report
    print("\n📊 Generating test coverage report...")
    run_command(
        "python -m pytest backend/tests/unit/ backend/tests/integration/ --cov=backend --cov-report=html --cov-report=term",
        "Test Coverage Report"
    )
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for success in results.values() if success)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed_tests}/{total_tests} test categories passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test categories failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())