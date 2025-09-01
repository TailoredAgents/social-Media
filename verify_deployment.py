#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deployment verification script for Render
Tests critical functionality before deployment
"""
import sys
import os
import requests
import json
from pathlib import Path

def test_local_import():
    """Test if the app can be imported locally"""
    print("Testing local app import...")
    
    try:
        # Add backend to path
        backend_path = Path(__file__).parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        from app import app
        print("SUCCESS: App import successful")
        return True
    except Exception as e:
        print(f"FAILED: App import failed: {e}")
        return False

def test_health_endpoint(base_url="http://localhost:8000"):
    """Test health endpoint"""
    print(f"🔍 Testing health endpoint at {base_url}...")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health endpoint responding")
            print(f"   Status: {data.get('status')}")
            print(f"   Features: {len(data.get('features', {}).get('available_features', []))}")
            return True
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False

def test_render_health_endpoint(base_url="http://localhost:8000"):
    """Test render-specific health endpoint"""
    print(f"🔍 Testing render health endpoint at {base_url}...")
    
    try:
        response = requests.get(f"{base_url}/render-health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Render health endpoint responding")
            print(f"   Mode: {data.get('mode')}")
            print(f"   Routes: {data.get('available_routes', 'unknown')}")
            return True
        else:
            print(f"❌ Render health endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Render health endpoint failed: {e}")
        return False

def test_docs_endpoint(base_url="http://localhost:8000"):
    """Test API documentation endpoint"""
    print(f"📚 Testing docs endpoint at {base_url}...")
    
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ Docs endpoint responding")
            return True
        else:
            print(f"❌ Docs endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Docs endpoint failed: {e}")
        return False

def test_image_endpoints(base_url="http://localhost:8000"):
    """Test image generation endpoints availability"""
    print(f"🖼️ Testing image endpoints at {base_url}...")
    
    endpoints = [
        "/api/content/generate-image",
        "/api/images/stream-status"
    ]
    
    success_count = 0
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            # 403 (auth required) is expected, 404 is bad
            if response.status_code in [200, 403]:
                print(f"✅ {endpoint} available")
                success_count += 1
            elif response.status_code == 404:
                print(f"❌ {endpoint} not found (404)")
            else:
                print(f"⚠️ {endpoint} returned {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} failed: {e}")
    
    return success_count >= len(endpoints) // 2

def run_full_verification(base_url="http://localhost:8000"):
    """Run full deployment verification"""
    print("🚀 Starting deployment verification...")
    print("=" * 50)
    
    tests = [
        ("Local Import", test_local_import),
        ("Health Endpoint", lambda: test_health_endpoint(base_url)),
        ("Render Health", lambda: test_render_health_endpoint(base_url)),
        ("Docs Endpoint", lambda: test_docs_endpoint(base_url)),
        ("Image Endpoints", lambda: test_image_endpoints(base_url))
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
        print()
    
    print("=" * 50)
    print("📊 VERIFICATION RESULTS:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed >= len(results) * 0.8:  # 80% pass rate
        print("🎉 Deployment verification SUCCESSFUL!")
        return True
    else:
        print("🚨 Deployment verification FAILED!")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify deployment")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL to test (default: http://localhost:8000)")
    parser.add_argument("--render", action="store_true",
                       help="Test against Render deployment")
    
    args = parser.parse_args()
    
    if args.render:
        base_url = "https://ai-social-backend.onrender.com"
    else:
        base_url = args.url
    
    success = run_full_verification(base_url)
    sys.exit(0 if success else 1)