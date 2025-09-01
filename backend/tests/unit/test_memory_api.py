"""
Test memory API endpoints
"""
import asyncio
import httpx
import json
import time
from datetime import datetime

# Fake API key for testing
import os
os.environ['OPENAI_API_KEY'] = 'test-key'

async def test_memory_api():
    """Test memory API endpoints"""
    print("🧪 Testing Memory API Integration\n")
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health check
        print("1️⃣ Testing API health...")
        try:
            response = await client.get(f"{base_url}/api/health")
            if response.status_code == 200:
                print("✅ API is running")
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            print("💡 Make sure to start the server with: uvicorn backend.main:app --reload")
            return False
        
        # Test 2: Test memory endpoints (without auth for now)
        print("\n2️⃣ Testing memory endpoints...")
        
        # Test memory stats endpoint
        try:
            response = await client.get(f"{base_url}/api/memory/stats")
            print(f"   Memory stats: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   - Response: {data}")
        except Exception as e:
            print(f"   Memory stats failed: {e}")
        
        # Test vector search stats (this will likely require auth)
        try:
            response = await client.get(f"{base_url}/api/memory/vector/stats")
            print(f"   Vector stats: {response.status_code}")
            if response.status_code == 401:
                print("   - Expected: Authentication required")
            elif response.status_code == 200:
                data = response.json()
                print(f"   - Response: {data}")
        except Exception as e:
            print(f"   Vector stats failed: {e}")
    
    print("\n✅ Memory API integration test completed!")
    return True

if __name__ == "__main__":
    asyncio.run(test_memory_api())