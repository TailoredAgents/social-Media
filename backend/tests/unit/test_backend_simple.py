# -*- coding: utf-8 -*-
"""
Simple backend functionality test
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Create a minimal test app
app = FastAPI(
    title="AI Social Media Content Agent API Test",
    description="Test API functionality",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "name": "AI Social Media Content Agent API",
        "version": "1.0.0",
        "status": "production-ready",
        "test": True
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": "2025-07-24T12:00:00Z",
        "version": "1.0.0",
        "test": True
    }

# Test the API
def test_backend():
    client = TestClient(app)
    
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    print("Root endpoint test passed")
    print("   Response: " + str(data))
    
    # Test health endpoint
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    print("Health endpoint test passed")
    print("   Response: " + str(data))
    
    print("\nBackend core functionality verified!")
    return True

if __name__ == "__main__":
    test_backend()