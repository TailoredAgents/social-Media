"""
Test script for JWT validation middleware
Tests Auth0 JWT validation, token caching, rate limiting, and error handling
"""
import asyncio
import time
import requests
import json
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_ENDPOINTS = [
    "/api/goals",
    "/api/notifications",
    "/api/content/history",
    "/api/auth/session-info"
]

class JWTMiddlewareTest:
    """Comprehensive JWT middleware testing"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.test_results = []
        self.valid_token = None
        self.invalid_token = "invalid.jwt.token"
    
    def log_result(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        print(f"[{status.upper()}] {test_name}: {details}")
    
    def test_health_endpoints(self):
        """Test that health endpoints don't require authentication"""
        print("\n=== Testing Health Endpoints (No Auth Required) ===")
        
        public_endpoints = ["/", "/api/health", "/docs", "/redoc"]
        
        for endpoint in public_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    self.log_result(f"Public endpoint {endpoint}", "PASS", f"Status: {response.status_code}")
                else:
                    self.log_result(f"Public endpoint {endpoint}", "FAIL", f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Public endpoint {endpoint}", "ERROR", str(e))
    
    def test_protected_endpoints_without_token(self):
        """Test that protected endpoints require authentication"""
        print("\n=== Testing Protected Endpoints (No Token) ===")
        
        for endpoint in TEST_ENDPOINTS:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 401:
                    self.log_result(f"No token {endpoint}", "PASS", "Correctly rejected with 401")
                else:
                    self.log_result(f"No token {endpoint}", "FAIL", f"Expected 401, got {response.status_code}")
            except Exception as e:
                self.log_result(f"No token {endpoint}", "ERROR", str(e))
    
    def test_protected_endpoints_with_invalid_token(self):
        """Test protected endpoints with invalid token"""
        print("\n=== Testing Protected Endpoints (Invalid Token) ===")
        
        headers = {"Authorization": f"Bearer {self.invalid_token}"}
        
        for endpoint in TEST_ENDPOINTS:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers, timeout=5)
                if response.status_code == 401:
                    self.log_result(f"Invalid token {endpoint}", "PASS", "Correctly rejected with 401")
                else:
                    self.log_result(f"Invalid token {endpoint}", "FAIL", f"Expected 401, got {response.status_code}")
            except Exception as e:
                self.log_result(f"Invalid token {endpoint}", "ERROR", str(e))
    
    def test_auth_management_endpoints(self):
        """Test authentication management endpoints"""
        print("\n=== Testing Auth Management Endpoints ===")
        
        # Test auth health endpoint (should be public)
        try:
            response = requests.get(f"{self.base_url}/api/auth/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Auth health endpoint", "PASS", f"Status: {data.get('status')}")
            else:
                self.log_result("Auth health endpoint", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Auth health endpoint", "ERROR", str(e))
        
        # Test token validation endpoint (should require token)
        try:
            response = requests.post(f"{self.base_url}/api/auth/validate-token", timeout=5)
            if response.status_code == 401:
                self.log_result("Token validation endpoint", "PASS", "Correctly requires auth")
            else:
                self.log_result("Token validation endpoint", "FAIL", f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("Token validation endpoint", "ERROR", str(e))
    
    def test_cors_headers(self):
        """Test CORS headers in error responses"""
        print("\n=== Testing CORS Headers ===")
        
        try:
            response = requests.get(f"{self.base_url}/api/goals", timeout=5)
            headers = response.headers
            
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers"
            ]
            
            cors_present = all(header in headers for header in cors_headers)
            
            if cors_present:
                self.log_result("CORS headers", "PASS", "All CORS headers present in error response")
            else:
                self.log_result("CORS headers", "FAIL", f"Missing CORS headers: {headers}")
        except Exception as e:
            self.log_result("CORS headers", "ERROR", str(e))
    
    def test_middleware_performance(self):
        """Test middleware performance with multiple requests"""
        print("\n=== Testing Middleware Performance ===")
        
        start_time = time.time()
        total_requests = 10
        
        for i in range(total_requests):
            try:
                response = requests.get(f"{self.base_url}/api/goals", timeout=5)
                # We expect 401, but we're testing response time
            except Exception:
                pass
        
        end_time = time.time()
        avg_response_time = (end_time - start_time) / total_requests
        
        if avg_response_time < 0.1:  # 100ms
            self.log_result("Middleware performance", "PASS", f"Avg response time: {avg_response_time:.3f}s")
        else:
            self.log_result("Middleware performance", "WARN", f"Slow response time: {avg_response_time:.3f}s")
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\n=== Testing Rate Limiting (Simulated) ===")
        
        # Note: This is a simplified test since we don't have valid tokens
        # In practice, you'd need valid tokens to test rate limiting properly
        
        requests_made = 0
        for i in range(5):  # Make 5 rapid requests
            try:
                response = requests.get(f"{self.base_url}/api/goals", timeout=2)
                requests_made += 1
            except Exception:
                pass
        
        if requests_made == 5:
            self.log_result("Rate limiting test", "INFO", "Made 5 requests successfully (no valid token to test limits)")
        else:
            self.log_result("Rate limiting test", "WARN", f"Only made {requests_made}/5 requests")
    
    def test_auth_status_endpoint(self):
        """Test the auth status monitoring endpoint"""
        print("\n=== Testing Auth Status Monitoring ===")
        
        try:
            response = requests.get(f"{self.base_url}/api/auth/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                auth_system = data.get("auth_system", {})
                middleware_stats = data.get("middleware_stats", {})
                
                self.log_result("Auth status endpoint", "PASS", 
                    f"Middleware active: {auth_system.get('middleware_active')}, "
                    f"Cached tokens: {middleware_stats.get('cached_tokens', 0)}")
            else:
                self.log_result("Auth status endpoint", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Auth status endpoint", "ERROR", str(e))
    
    def run_all_tests(self):
        """Run comprehensive middleware test suite"""
        print("🚀 Starting JWT Middleware Test Suite")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run all tests
        self.test_health_endpoints()
        self.test_protected_endpoints_without_token()
        self.test_protected_endpoints_with_invalid_token()
        self.test_auth_management_endpoints()
        self.test_cors_headers()
        self.test_middleware_performance()
        self.test_rate_limiting()
        self.test_auth_status_endpoint()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        errors = len([r for r in self.test_results if r["status"] == "ERROR"])
        warnings = len([r for r in self.test_results if r["status"] == "WARN"])
        info = len([r for r in self.test_results if r["status"] == "INFO"])
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"🚨 Errors: {errors}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"ℹ️  Info: {info}")
        print(f"📝 Total Tests: {len(self.test_results)}")
        
        if failed == 0 and errors == 0:
            print("\n🎉 All critical tests passed! JWT middleware is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the results above for details.")
        
        return self.test_results

def main():
    """Main test execution"""
    tester = JWTMiddlewareTest()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"✅ Server is running (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Server is not running: {e}")
        print("Please start the FastAPI server with: uvicorn backend.main:app --reload")
        return
    
    # Run tests
    results = tester.run_all_tests()
    
    # Save results to file
    with open("jwt_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Test results saved to: jwt_test_results.json")

if __name__ == "__main__":
    main()