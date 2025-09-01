#!/usr/bin/env python3
"""
Standalone Integration Validation Test
Tests the integration client structure and validation without external dependencies
"""
import re
import sys
import json
from datetime import datetime
from typing import Dict, List, Tuple

class IntegrationValidator:
    """Validates social media integration code structure and functionality"""
    
    def __init__(self):
        self.test_results = {
            "structure_validation": {"passed": 0, "failed": 0, "tests": []},
            "content_validation": {"passed": 0, "failed": 0, "tests": []},
            "error_handling": {"passed": 0, "failed": 0, "tests": []}
        }
        
    def run_all_tests(self):
        """Run all integration validation tests"""
        print("Social Media Integration Validation Suite")
        print("=" * 50)
        
        self.test_client_structure()
        self.test_content_validation_logic()
        self.test_error_handling_patterns()
        
        self.print_results()
    
    def test_client_structure(self):
        """Test client file structure and required components"""
        print("\n1. Client Structure Validation:")
        
        clients = {
            "Twitter": "backend/integrations/twitter_client.py",
            "LinkedIn": "backend/integrations/py", 
            "Instagram": "backend/integrations/instagram_client.py",
            "Facebook": "backend/integrations/facebook_client.py"
        }
        
        for platform, file_path in clients.items():
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for required components
                has_client_class = f"{platform}APIClient" in content
                has_make_request = "_make_request" in content
                has_endpoints = "endpoints" in content
                has_rate_limits = "rate_limits" in content
                has_async_methods = "async def" in content
                has_error_handling = "Exception" in content
                
                required_components = [
                    has_client_class, has_make_request, has_endpoints,
                    has_rate_limits, has_async_methods, has_error_handling
                ]
                
                score = sum(required_components)
                passed = score >= 5  # At least 5/6 components
                
                self.record_test("structure_validation", f"{platform}_structure", passed,
                               f"Score: {score}/6 components" if not passed else None)
                
                print(f"   {'PASS' if passed else 'FAIL'} {platform} client structure ({score}/6)")
                
            except FileNotFoundError:
                self.record_test("structure_validation", f"{platform}_structure", False,
                               "File not found")
                print(f"   FAIL {platform} client file not found")
            except Exception as e:
                self.record_test("structure_validation", f"{platform}_structure", False, str(e))
                print(f"   ERROR {platform} client test failed: {e}")
    
    def test_content_validation_logic(self):
        """Test content validation logic patterns"""
        print("\n2. Content Validation Logic:")
        
        validation_tests = [
            ("twitter_limits", "backend/integrations/twitter_client.py", "280", "tweet"),
            ("linkedin_limits", "backend/integrations/py", "3000", "post"),
            ("instagram_limits", "backend/integrations/instagram_client.py", "2200", "caption"),
            ("facebook_limits", "backend/integrations/facebook_client.py", "63206", "message")
        ]
        
        for test_name, file_path, expected_limit, content_type in validation_tests:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for content limit validation
                has_length_check = "len(" in content
                has_limit_constant = expected_limit in content
                has_validation_method = "validate" in content.lower()
                has_error_return = "return False" in content or "raise" in content
                
                validation_score = sum([has_length_check, has_limit_constant, 
                                      has_validation_method, has_error_return])
                passed = validation_score >= 3
                
                self.record_test("content_validation", test_name, passed,
                               f"Score: {validation_score}/4" if not passed else None)
                
                platform = test_name.split('_')[0].title()
                print(f"   {'PASS' if passed else 'FAIL'} {platform} content validation ({validation_score}/4)")
                
            except FileNotFoundError:
                self.record_test("content_validation", test_name, False, "File not found")
                print(f"   FAIL {test_name} file not found")
            except Exception as e:
                self.record_test("content_validation", test_name, False, str(e))
                print(f"   ERROR {test_name} failed: {e}")
    
    def test_error_handling_patterns(self):
        """Test error handling patterns in integration clients"""
        print("\n3. Error Handling Patterns:")
        
        clients = {
            "Twitter": "backend/integrations/twitter_client.py",
            "LinkedIn": "backend/integrations/py",
            "Instagram": "backend/integrations/instagram_client.py", 
            "Facebook": "backend/integrations/facebook_client.py"
        }
        
        for platform, file_path in clients.items():
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for error handling patterns
                has_try_except = "try:" in content and "except" in content
                has_status_code_check = "status_code" in content
                has_rate_limit_handling = "429" in content or "rate" in content.lower()
                has_error_logging = "logger.error" in content or "logger.warning" in content
                has_custom_exceptions = "raise Exception" in content or "Exception(" in content
                has_network_error = "httpx" in content and "RequestError" in content
                
                error_patterns = [
                    has_try_except, has_status_code_check, has_rate_limit_handling,
                    has_error_logging, has_custom_exceptions, has_network_error
                ]
                
                score = sum(error_patterns)
                passed = score >= 4  # At least 4/6 patterns
                
                self.record_test("error_handling", f"{platform}_error_handling", passed,
                               f"Score: {score}/6 patterns" if not passed else None)
                
                print(f"   {'PASS' if passed else 'FAIL'} {platform} error handling ({score}/6)")
                
            except FileNotFoundError:
                self.record_test("error_handling", f"{platform}_error_handling", False,
                               "File not found")
                print(f"   FAIL {platform} file not found")
            except Exception as e:
                self.record_test("error_handling", f"{platform}_error_handling", False, str(e))
                print(f"   ERROR {platform} error handling test failed: {e}")
    
    def record_test(self, category: str, test_name: str, passed: bool, error: str = None):
        """Record a test result"""
        self.test_results[category]["tests"].append({
            "name": test_name,
            "status": "passed" if passed else "failed",
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        
        if passed:
            self.test_results[category]["passed"] += 1
        else:
            self.test_results[category]["failed"] += 1
    
    def print_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 50)
        print("INTEGRATION VALIDATION RESULTS")
        print("=" * 50)
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        for category, results in self.test_results.items():
            category_tests = len(results["tests"])
            category_passed = results["passed"]
            category_failed = results["failed"]
            
            total_tests += category_tests
            total_passed += category_passed
            total_failed += category_failed
            
            if category_tests > 0:
                success_rate = (category_passed / category_tests) * 100
                status = "PASS" if success_rate >= 80 else "WARN" if success_rate >= 60 else "FAIL"
                
                print(f"\n{status} {category.replace('_', ' ').title()}")
                print(f"   Tests: {category_passed}/{category_tests} passed ({success_rate:.1f}%)")
                
                # Show failed tests
                failed_tests = [t for t in results["tests"] if t["status"] == "failed"]
                if failed_tests:
                    for test in failed_tests:
                        print(f"     FAIL {test['name']}")
                        if test.get("error"):
                            print(f"          {test['error']}")
        
        # Overall summary
        print(f"\nOVERALL VALIDATION SUMMARY")
        print(f"   Total Tests: {total_tests}")
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"   Passed: {total_passed} ({success_rate:.1f}%)")
            print(f"   Failed: {total_failed} ({(total_failed/total_tests*100):.1f}%)")
            
            if success_rate >= 90:
                print(f"   EXCELLENT: Integration code quality is excellent!")
            elif success_rate >= 75:
                print(f"   GOOD: Integration code quality is good")
            elif success_rate >= 60:
                print(f"   FAIR: Integration code needs some improvements")
            else:
                print(f"   POOR: Integration code needs significant improvements")
        else:
            print("   No tests completed")
        
        # Save results
        results_file = f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: {results_file}")
        print("=" * 50)

def main():
    """Run integration validation tests"""
    validator = IntegrationValidator()
    validator.run_all_tests()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Validation failed: {e}")
        sys.exit(1)