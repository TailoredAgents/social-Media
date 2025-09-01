#!/usr/bin/env python3
"""
Simple deployment test script
"""
import sys
import os
from pathlib import Path

def test_app_import():
    """Test if the app can be imported"""
    print("Testing app import...")
    
    try:
        # Add backend to path
        backend_path = Path(__file__).parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        from app import app
        print("SUCCESS: App imported successfully")
        print("App title: " + str(app.title))
        print("Total routes: " + str(len(app.routes)))
        return True
    except Exception as e:
        print("FAILED: App import error: " + str(e))
        import traceback
        traceback.print_exc()
        return False

def test_production_config():
    """Test production configuration"""
    print("Testing production config...")
    
    try:
        from backend.core.production_config import production_config
        status = production_config.get_feature_status()
        print("SUCCESS: Production config loaded")
        print("Available features: " + str(len(status.get('available_features', []))))
        print("Missing deps: " + str(status.get('missing_dependencies', [])))
        return True
    except Exception as e:
        print("FAILED: Production config error: " + str(e))
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("DEPLOYMENT TEST")
    print("=" * 50)
    
    tests = [
        ("App Import", test_app_import),
        ("Production Config", test_production_config)
    ]
    
    passed = 0
    for name, test_func in tests:
        print("\n" + name + ":")
        if test_func():
            passed += 1
        
    print("\n" + "=" * 50)
    print("RESULT: " + str(passed) + "/" + str(len(tests)) + " tests passed")
    
    if passed == len(tests):
        print("DEPLOYMENT TEST: PASSED")
        sys.exit(0)
    else:
        print("DEPLOYMENT TEST: FAILED")
        sys.exit(1)