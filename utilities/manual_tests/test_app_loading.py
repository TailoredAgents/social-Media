#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to diagnose app loading issues
"""
import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

print("Testing app loading...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

# Set basic environment
os.environ['ENVIRONMENT'] = 'test'

try:
    # Import FastAPI first
    from fastapi import FastAPI
    print("FastAPI imported successfully")
    
    # Try to load the system_logs router directly  
    from backend.api.system_logs import router as system_router
    print(f"System logs router loaded: {system_router}")
    print(f"System router prefix: {system_router.prefix}")
    print(f"System router tags: {system_router.tags}")
    
    # Create a test app and add the router
    test_app = FastAPI(title="Test App")
    test_app.include_router(system_router)
    
    print("Test app created successfully")
    print(f"Total routes in test app: {len(test_app.routes)}")
    
    # List all routes
    for route in test_app.routes:
        if hasattr(route, 'path'):
            print(f"Route: {route.path}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()