#!/usr/bin/env python3
"""
API endpoint testing script
Tests all core API endpoints for basic functionality
"""
import requests
import json
import sys
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

class APITester:
    """Test API endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_user_id = None
    
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_health_check(self) -> bool:
        """Test basic health check"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                self.log("✅ Health check passed")
                return True
            else:
                self.log(f"❌ Health check failed: {response.status_code}", "ERROR")
                return False
        except requests.RequestException as e:
            self.log(f"❌ Health check error: {e}", "ERROR")
            return False
    
    def test_auth_endpoints(self) -> bool:
        """Test authentication endpoints"""
        self.log("Testing authentication endpoints...")
        
        # Test registration
        register_data = {
            "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
            "username": f"test_user_{datetime.now().strftime('%H%M%S')}",
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=register_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.test_user_id = data.get("user_id")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log("✅ User registration successful")
                
                # Test token verification
                verify_response = self.session.get(f"{self.base_url}/api/auth/verify")
                if verify_response.status_code == 200:
                    self.log("✅ Token verification successful")
                    return True
                else:
                    self.log("❌ Token verification failed", "ERROR")
                    return False
            else:
                self.log(f"❌ Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except requests.RequestException as e:
            self.log(f"❌ Auth test error: {e}", "ERROR")
            return False
    
    def test_goals_endpoints(self) -> bool:
        """Test goals endpoints"""
        self.log("Testing goals endpoints...")
        
        if not self.auth_token:
            self.log("❌ No auth token for goals test", "ERROR")
            return False
        
        try:
            # Create a goal
            goal_data = {
                "title": "Test Goal",
                "description": "This is a test goal",
                "goal_type": "follower_growth",
                "target_value": 1000.0,
                "target_date": (date.today() + timedelta(days=30)).isoformat(),
                "platform": "twitter"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/goals/",
                json=goal_data
            )
            
            if response.status_code == 200:
                goal = response.json()
                goal_id = goal.get("id")
                self.log("✅ Goal creation successful")
                
                # Test getting goals
                get_response = self.session.get(f"{self.base_url}/api/goals/")
                if get_response.status_code == 200:
                    goals = get_response.json()
                    if isinstance(goals, list) and len(goals) > 0:
                        self.log("✅ Goal retrieval successful")
                        
                        # Test updating goal progress
                        progress_data = {"current_value": 50.0, "notes": "Test progress update"}
                        progress_response = self.session.put(
                            f"{self.base_url}/api/goals/{goal_id}/progress",
                            json=progress_data
                        )
                        
                        if progress_response.status_code == 200:
                            self.log("✅ Goal progress update successful")
                            return True
                        else:
                            self.log("❌ Goal progress update failed", "ERROR")
                            return False
                    else:
                        self.log("❌ No goals retrieved", "ERROR")
                        return False
                else:
                    self.log("❌ Goal retrieval failed", "ERROR")
                    return False
            else:
                self.log(f"❌ Goal creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except requests.RequestException as e:
            self.log(f"❌ Goals test error: {e}", "ERROR")
            return False
    
    def test_content_endpoints(self) -> bool:
        """Test content endpoints"""
        self.log("Testing content endpoints...")
        
        if not self.auth_token:
            self.log("❌ No auth token for content test", "ERROR")
            return False
        
        try:
            # Create content
            content_data = {
                "platform": "twitter",
                "content": "This is a test post from the API testing script! 🚀",
                "content_type": "text"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/content/",
                json=content_data
            )
            
            if response.status_code == 200:
                content = response.json()
                content_id = content.get("id")
                self.log("✅ Content creation successful")
                
                # Test getting content
                get_response = self.session.get(f"{self.base_url}/api/content/")
                if get_response.status_code == 200:
                    content_list = get_response.json()
                    if isinstance(content_list, list) and len(content_list) > 0:
                        self.log("✅ Content retrieval successful")
                        
                        # Test publishing content
                        publish_data = {"platform_post_id": "test_123"}
                        publish_response = self.session.post(
                            f"{self.base_url}/api/content/{content_id}/publish",
                            json=publish_data
                        )
                        
                        if publish_response.status_code == 200:
                            self.log("✅ Content publishing successful")
                            return True
                        else:
                            self.log("❌ Content publishing failed", "ERROR")
                            return False
                    else:
                        self.log("❌ No content retrieved", "ERROR")
                        return False
                else:
                    self.log("❌ Content retrieval failed", "ERROR")
                    return False
            else:
                self.log(f"❌ Content creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except requests.RequestException as e:
            self.log(f"❌ Content test error: {e}", "ERROR")
            return False
    
    def test_memory_endpoints(self) -> bool:
        """Test memory endpoints"""
        self.log("Testing memory endpoints...")
        
        if not self.auth_token:
            self.log("❌ No auth token for memory test", "ERROR")
            return False
        
        try:
            # Store content in memory
            memory_data = {
                "content": "This is important information to remember for future content creation.",
                "content_type": "insight",
                "source": "manual",
                "platform": "twitter",
                "tags": ["testing", "api", "memory"],
                "sentiment": "positive",
                "topic_category": "development"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/memory/store",
                json=memory_data
            )
            
            if response.status_code == 200:
                memory_item = response.json()
                memory_id = memory_item.get("id")
                self.log("✅ Memory storage successful")
                
                # Test searching memory
                search_data = {
                    "query": "important information",
                    "limit": 5
                }
                
                search_response = self.session.post(
                    f"{self.base_url}/api/memory/search",
                    json=search_data
                )
                
                if search_response.status_code == 200:
                    search_results = search_response.json()
                    if isinstance(search_results, list):
                        self.log("✅ Memory search successful")
                        
                        # Test getting memory analytics
                        analytics_response = self.session.get(f"{self.base_url}/api/memory/analytics/summary")
                        if analytics_response.status_code == 200:
                            self.log("✅ Memory analytics successful")
                            return True
                        else:
                            self.log("❌ Memory analytics failed", "ERROR")
                            return False
                    else:
                        self.log("❌ Invalid search results format", "ERROR")
                        return False
                else:
                    self.log("❌ Memory search failed", "ERROR")
                    return False
            else:
                self.log(f"❌ Memory storage failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except requests.RequestException as e:
            self.log(f"❌ Memory test error: {e}", "ERROR")
            return False
    
    def test_workflow_endpoints(self) -> bool:
        """Test workflow endpoints"""
        self.log("Testing workflow endpoints...")
        
        if not self.auth_token:
            self.log("❌ No auth token for workflow test", "ERROR")
            return False
        
        try:
            # Execute a workflow
            workflow_data = {
                "workflow_type": "manual",
                "execution_params": {
                    "test_mode": True,
                    "content_count": 1
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/workflow/execute",
                json=workflow_data
            )
            
            if response.status_code == 200:
                execution = response.json()
                execution_id = execution.get("id")
                self.log("✅ Workflow execution started")
                
                # Test getting workflow executions
                get_response = self.session.get(f"{self.base_url}/api/workflow/")
                if get_response.status_code == 200:
                    executions = get_response.json()
                    if isinstance(executions, list):
                        self.log("✅ Workflow retrieval successful")
                        
                        # Test getting workflow status summary
                        status_response = self.session.get(f"{self.base_url}/api/workflow/status/summary")
                        if status_response.status_code == 200:
                            self.log("✅ Workflow status summary successful")
                            return True
                        else:
                            self.log("❌ Workflow status summary failed", "ERROR")
                            return False
                    else:
                        self.log("❌ Invalid executions format", "ERROR")
                        return False
                else:
                    self.log("❌ Workflow retrieval failed", "ERROR")
                    return False
            else:
                self.log(f"❌ Workflow execution failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except requests.RequestException as e:
            self.log(f"❌ Workflow test error: {e}", "ERROR")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all API tests"""
        self.log("🚀 Starting API endpoint tests")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Authentication", self.test_auth_endpoints),
            ("Goals", self.test_goals_endpoints),
            ("Content", self.test_content_endpoints),
            ("Memory", self.test_memory_endpoints),
            ("Workflow", self.test_workflow_endpoints),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n📋 Running {test_name} tests...")
            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name} tests passed")
                else:
                    self.log(f"❌ {test_name} tests failed", "ERROR")
            except Exception as e:
                self.log(f"❌ {test_name} tests error: {e}", "ERROR")
        
        self.log(f"\n📊 Test Results: {passed}/{total} passed")
        
        if passed == total:
            self.log("🎉 All tests passed!")
            return True
        else:
            self.log("⚠️  Some tests failed. Check the logs above.", "ERROR")
            return False

def main():
    """Main function"""
    base_url = "http://localhost:8000"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"Testing API endpoints at: {base_url}")
    print("Make sure the server is running with: python -m uvicorn backend.main:app --reload")
    print("=" * 60)
    
    tester = APITester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()