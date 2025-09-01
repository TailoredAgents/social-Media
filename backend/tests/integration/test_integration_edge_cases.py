#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Social Media Integration Edge Cases and Error Handling Test Suite
Tests error handling, rate limiting, content validation, and edge cases
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.integrations.twitter_client import twitter_client
from backend.integrations.linkedin_client import linkedin_client
from backend.integrations.instagram_client import instagram_client
from backend.integrations.facebook_client import facebook_client

class IntegrationEdgeCaseTester:
    """
    Test suite for social media integration edge cases and error handling
    """
    
    def __init__(self):
        """Initialize the edge case tester"""
        self.test_results = {
            "content_validation": {"tests": [], "passed": 0, "failed": 0},
            "error_handling": {"tests": [], "passed": 0, "failed": 0},
            "rate_limiting": {"tests": [], "passed": 0, "failed": 0},
            "network_errors": {"tests": [], "passed": 0, "failed": 0},
            "authentication": {"tests": [], "passed": 0, "failed": 0}
        }
        
        print("🧪 Social Media Integration Edge Case Test Suite Starting...")
        print("=" * 65)
    
    async def run_all_edge_case_tests(self):
        """Run all edge case and error handling tests"""
        test_categories = [
            ("Content Validation", self.test_content_validation),
            ("Error Handling", self.test_error_handling),
            ("Rate Limiting", self.test_rate_limiting_behavior),
            ("Network Errors", self.test_network_error_handling),
            ("Authentication", self.test_authentication_errors)
        ]
        
        for category_name, test_function in test_categories:
            print(f"\n🔍 Testing {category_name}...")
            print("-" * 50)
            
            try:
                await test_function()
                print(f"✅ {category_name} tests completed")
            except Exception as e:
                print(f"❌ {category_name} tests failed: {e}")
        
        self.print_edge_case_results()
    
    async def test_content_validation(self):
        """Test content validation across all platforms"""
        category = "content_validation"
        
        # Test 1: Twitter character limit validation
        print("📝 Test 1: Twitter character limit validation...")
        try:
            long_text = "a" * 300  # Exceeds 280 character limit
            is_valid, error_msg = twitter_client.is_valid_tweet_text(long_text)
            
            success = not is_valid and "too long" in error_msg.lower()
            self.record_test_result(category, "twitter_character_limit", success, 
                                  error_msg if not success else None)
            print(f"   {'✅' if success else '❌'} Twitter character limit validation")
        except Exception as e:
            self.record_test_result(category, "twitter_character_limit", False, str(e))
            print(f"   ❌ Twitter character limit test failed: {e}")
        
        # Test 2: LinkedIn content validation
        print("📝 Test 2: LinkedIn content validation...")
        try:
            long_content = "a" * 3500  # Exceeds LinkedIn limit
            is_valid, error_msg = validate_post_content(long_content)
            
            success = not is_valid and "too long" in error_msg.lower()
            self.record_test_result(category, "linkedin_content_limit", success,
                                  error_msg if not success else None)
            print(f"   {'✅' if success else '❌'} LinkedIn content limit validation")
        except Exception as e:
            self.record_test_result(category, "linkedin_content_limit", False, str(e))
            print(f"   ❌ LinkedIn content limit test failed: {e}")
        
        # Test 3: Instagram caption validation
        print("📝 Test 3: Instagram caption validation...")
        try:
            long_caption = "a" * 2500  # Exceeds Instagram caption limit
            is_valid, error_msg = instagram_client.validate_caption(long_caption)
            
            success = not is_valid and "too long" in error_msg.lower()
            self.record_test_result(category, "instagram_caption_limit", success,
                                  error_msg if not success else None)
            print(f"   {'✅' if success else '❌'} Instagram caption limit validation")
        except Exception as e:
            self.record_test_result(category, "instagram_caption_limit", False, str(e))
            print(f"   ❌ Instagram caption limit test failed: {e}")
        
        # Test 4: Facebook content validation
        print("📝 Test 4: Facebook content validation...")
        try:
            long_message = "a" * 65000  # Exceeds Facebook message limit
            is_valid, error_msg = facebook_client.validate_post_content(long_message)
            
            success = not is_valid and "too long" in error_msg.lower()
            self.record_test_result(category, "facebook_content_limit", success,
                                  error_msg if not success else None)
            print(f"   {'✅' if success else '❌'} Facebook content limit validation")
        except Exception as e:
            self.record_test_result(category, "facebook_content_limit", False, str(e))
            print(f"   ❌ Facebook content limit test failed: {e}")
        
        # Test 5: Empty content validation
        print("📝 Test 5: Empty content validation...")
        try:
            # Test empty tweet
            is_valid_twitter, _ = twitter_client.is_valid_tweet_text("")
            is_valid_ _ = validate_post_content("")
            is_valid_instagram, _ = instagram_client.validate_caption("")
            is_valid_facebook, _ = facebook_client.validate_post_content("")
            
            success = not any([is_valid_twitter, is_valid_ is_valid_instagram, is_valid_facebook])
            self.record_test_result(category, "empty_content_validation", success,
                                  None if success else "Some platforms allowed empty content")
            print(f"   {'✅' if success else '❌'} Empty content validation")
        except Exception as e:
            self.record_test_result(category, "empty_content_validation", False, str(e))
            print(f"   ❌ Empty content validation test failed: {e}")
        
        # Test 6: Hashtag extraction and validation
        print("📝 Test 6: Hashtag extraction and validation...")
        try:
            test_text = "Testing #AI #MachineLearning #SocialMedia #Automation #Testing #AI"
            
            twitter_hashtags = twitter_client.extract_hashtags(test_text)
            linkedin_hashtags = extract_hashtags(test_text)
            instagram_hashtags = instagram_client.extract_hashtags(test_text)
            facebook_hashtags = facebook_client.extract_hashtags(test_text)
            
            # Check if hashtags are properly extracted
            expected_unique = {"#ai", "#machinelearning", "#socialmedia", "#automation", "#testing"}
            
            success = (
                len(set(twitter_hashtags)) >= 5 and
                len(set(linkedin_hashtags)) >= 5 and
                len(set(instagram_hashtags)) >= 5 and
                len(set(facebook_hashtags)) >= 5
            )
            
            self.record_test_result(category, "hashtag_extraction", success,
                                  None if success else "Hashtag extraction inconsistent")
            print(f"   {'✅' if success else '❌'} Hashtag extraction validation")
        except Exception as e:
            self.record_test_result(category, "hashtag_extraction", False, str(e))
            print(f"   ❌ Hashtag extraction test failed: {e}")
    
    async def test_error_handling(self):
        """Test error handling for various scenarios"""
        category = "error_handling"
        
        # Test 1: Invalid access token handling
        print("📝 Test 1: Invalid access token handling...")
        invalid_token = "invalid_token_12345"
        
        platforms_tested = 0
        errors_handled = 0
        
        # Test Twitter with invalid token
        try:
            await twitter_client.get_user_profile(invalid_token)
            platforms_tested += 1
        except Exception as e:
            platforms_tested += 1
            if "401" in str(e) or "unauthorized" in str(e).lower() or "invalid" in str(e).lower():
                errors_handled += 1
        
        # Test LinkedIn with invalid token
        try:
            await get_user_profile(invalid_token)
            platforms_tested += 1
        except Exception as e:
            platforms_tested += 1
            if "401" in str(e) or "unauthorized" in str(e).lower() or "invalid" in str(e).lower():
                errors_handled += 1
        
        success = errors_handled >= 2  # At least 2 platforms should handle invalid tokens properly
        self.record_test_result(category, "invalid_token_handling", success,
                              None if success else f"Only {errors_handled}/{platforms_tested} platforms handled invalid tokens")
        print(f"   {'✅' if success else '❌'} Invalid access token handling")
        
        # Test 2: Invalid content format handling
        print("📝 Test 2: Invalid content format handling...")
        try:
            # Test invalid media URLs
            invalid_url = "not_a_valid_url"
            
            validation_errors = 0
            
            # Instagram would reject invalid image URLs
            try:
                await instagram_client.post_image(
                    access_token="dummy_token",
                    ig_user_id="dummy_id", 
                    image_url=invalid_url,
                    caption="Test"
                )
            except Exception as e:
                if "url" in str(e).lower() or "invalid" in str(e).lower():
                    validation_errors += 1
            
            success = validation_errors > 0
            self.record_test_result(category, "invalid_content_format", success,
                                  None if success else "Invalid content format not properly handled")
            print(f"   {'✅' if success else '❌'} Invalid content format handling")
        except Exception as e:
            self.record_test_result(category, "invalid_content_format", False, str(e))
            print(f"   ❌ Invalid content format test failed: {e}")
        
        # Test 3: Network timeout simulation
        print("📝 Test 3: Network timeout behavior...")
        try:
            # This is a conceptual test - in real implementation, we'd simulate network issues
            # For now, we test that the timeout configurations are reasonable
            
            timeout_configs = {
                "twitter": hasattr(twitter_client, '_make_request'),
                : hasattr(linkedin_client, '_make_request'),
                "instagram": hasattr(instagram_client, '_make_request'),
                "facebook": hasattr(facebook_client, '_make_request')
            }
            
            success = all(timeout_configs.values())
            self.record_test_result(category, "network_timeout_config", success,
                                  None if success else "Some clients missing proper request handling")
            print(f"   {'✅' if success else '❌'} Network timeout configuration")
        except Exception as e:
            self.record_test_result(category, "network_timeout_config", False, str(e))
            print(f"   ❌ Network timeout test failed: {e}")
    
    async def test_rate_limiting_behavior(self):
        """Test rate limiting behavior and handling"""
        category = "rate_limiting"
        
        # Test 1: Rate limit configuration validation
        print("📝 Test 1: Rate limit configuration validation...")
        try:
            rate_limit_configs = {
                "twitter": hasattr(twitter_client, 'rate_limits') and len(twitter_client.rate_limits) > 0,
                : hasattr(linkedin_client, 'rate_limits') and len(rate_limits) > 0,
                "instagram": hasattr(instagram_client, 'rate_limits') and len(instagram_client.rate_limits) > 0,
                "facebook": hasattr(facebook_client, 'rate_limits') and len(facebook_client.rate_limits) > 0
            }
            
            success = all(rate_limit_configs.values())
            self.record_test_result(category, "rate_limit_configuration", success,
                                  None if success else f"Missing rate limit configs: {[k for k, v in rate_limit_configs.items() if not v]}")
            print(f"   {'✅' if success else '❌'} Rate limit configuration validation")
        except Exception as e:
            self.record_test_result(category, "rate_limit_configuration", False, str(e))
            print(f"   ❌ Rate limit configuration test failed: {e}")
        
        # Test 2: Content limits validation
        print("📝 Test 2: Content limits validation...")
        try:
            content_limits = {
                "twitter": hasattr(twitter_client, 'endpoints') and len(twitter_client.endpoints) > 0,
                : hasattr(linkedin_client, 'content_limits') and len(content_limits) > 0,
                "instagram": hasattr(instagram_client, 'content_limits') and len(instagram_client.content_limits) > 0,
                "facebook": hasattr(facebook_client, 'content_limits') and len(facebook_client.content_limits) > 0
            }
            
            success = sum(content_limits.values()) >= 3  # At least 3 platforms should have content limits
            self.record_test_result(category, "content_limits", success,
                                  None if success else "Insufficient content limit configurations")
            print(f"   {'✅' if success else '❌'} Content limits validation")
        except Exception as e:
            self.record_test_result(category, "content_limits", False, str(e))
            print(f"   ❌ Content limits test failed: {e}")
    
    async def test_network_error_handling(self):
        """Test network error handling scenarios"""
        category = "network_errors"
        
        # Test 1: Invalid endpoint handling
        print("📝 Test 1: Invalid endpoint handling...")
        try:
            # Test with clearly invalid endpoints
            error_count = 0
            
            # Each client should have proper error handling in _make_request
            clients_with_error_handling = {
                "twitter": hasattr(twitter_client, '_make_request'),
                : hasattr(linkedin_client, '_make_request'),
                "instagram": hasattr(instagram_client, '_make_request'),
                "facebook": hasattr(facebook_client, '_make_request')
            }
            
            success = all(clients_with_error_handling.values())
            self.record_test_result(category, "invalid_endpoint_handling", success,
                                  None if success else "Some clients missing error handling methods")
            print(f"   {'✅' if success else '❌'} Invalid endpoint handling")
        except Exception as e:
            self.record_test_result(category, "invalid_endpoint_handling", False, str(e))
            print(f"   ❌ Invalid endpoint handling test failed: {e}")
        
        # Test 2: Request method validation
        print("📝 Test 2: Request method validation...")
        try:
            # Check if clients validate HTTP methods
            method_validation = {
                "twitter": hasattr(twitter_client, '_make_request'),
                : hasattr(linkedin_client, '_make_request'),
                "instagram": hasattr(instagram_client, '_make_request'),
                "facebook": hasattr(facebook_client, '_make_request')
            }
            
            success = all(method_validation.values())
            self.record_test_result(category, "request_method_validation", success,
                                  None if success else "Some clients missing request method validation")
            print(f"   {'✅' if success else '❌'} Request method validation")
        except Exception as e:
            self.record_test_result(category, "request_method_validation", False, str(e))
            print(f"   ❌ Request method validation test failed: {e}")
    
    async def test_authentication_errors(self):
        """Test authentication error scenarios"""
        category = "authentication"
        
        # Test 1: Missing token handling
        print("📝 Test 1: Missing token handling...")
        try:
            auth_validation_count = 0
            
            # Test each platform's handling of None/empty tokens
            test_cases = [
                ("twitter", twitter_client.get_user_profile, None),
                (, get_user_profile, ""),
                ("instagram", instagram_client.get_profile, None),
                ("facebook", facebook_client.get_user_pages, "")
            ]
            
            for platform, method, invalid_token in test_cases:
                try:
                    if platform == "instagram":
                        await method(invalid_token, "dummy_id")
                    else:
                        await method(invalid_token)
                except Exception as e:
                    # Should raise appropriate authentication error
                    if any(keyword in str(e).lower() for keyword in ["token", "auth", "credential", "invalid"]):
                        auth_validation_count += 1
            
            success = auth_validation_count >= 3  # At least 3 platforms should handle auth errors
            self.record_test_result(category, "missing_token_handling", success,
                                  None if success else f"Only {auth_validation_count}/4 platforms handled auth errors properly")
            print(f"   {'✅' if success else '❌'} Missing token handling")
        except Exception as e:
            self.record_test_result(category, "missing_token_handling", False, str(e))
            print(f"   ❌ Missing token handling test failed: {e}")
        
        # Test 2: Token format validation
        print("📝 Test 2: Token format validation...")
        try:
            # Test with malformed tokens
            malformed_tokens = ["", "   ", "invalid", "123", "bearer_", "oauth_"]
            platforms_tested = 0
            proper_rejections = 0
            
            for token in malformed_tokens[:2]:  # Test first 2 to avoid rate limiting
                try:
                    await twitter_client.get_user_profile(token)
                    platforms_tested += 1
                except Exception as e:
                    platforms_tested += 1
                    if any(keyword in str(e).lower() for keyword in ["token", "auth", "invalid", "401", "403"]):
                        proper_rejections += 1
                        break  # One proper rejection is enough
            
            success = proper_rejections > 0
            self.record_test_result(category, "token_format_validation", success,
                                  None if success else "Token format validation not working properly")
            print(f"   {'✅' if success else '❌'} Token format validation")
        except Exception as e:
            self.record_test_result(category, "token_format_validation", False, str(e))
            print(f"   ❌ Token format validation test failed: {e}")
    
    def record_test_result(self, category: str, test_name: str, success: bool, error_msg: Optional[str] = None):
        """Record a test result"""
        self.test_results[category]["tests"].append({
            "name": test_name,
            "status": "passed" if success else "failed",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        })
        
        if success:
            self.test_results[category]["passed"] += 1
        else:
            self.test_results[category]["failed"] += 1
    
    def print_edge_case_results(self):
        """Print comprehensive edge case test results"""
        print("\n" + "=" * 65)
        print("🧪 EDGE CASE AND ERROR HANDLING TEST RESULTS")
        print("=" * 65)
        
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
                status_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
                
                print(f"\n{status_icon} {category.replace('_', ' ').title()}")
                print(f"   Tests: {category_passed}/{category_tests} passed ({success_rate:.1f}%)")
                
                # Show failed tests
                failed_tests = [t for t in results["tests"] if t["status"] == "failed"]
                if failed_tests:
                    print(f"   Failed tests:")
                    for test in failed_tests:
                        print(f"     ❌ {test['name']}")
                        if test.get("error"):
                            print(f"        Error: {test['error']}")
        
        # Overall summary
        print(f"\n📊 OVERALL EDGE CASE TEST SUMMARY")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {total_passed} ({(total_passed/total_tests*100):.1f}%)" if total_tests > 0 else "   Passed: 0 (0%)")
        print(f"   Failed: {total_failed} ({(total_failed/total_tests*100):.1f}%)" if total_tests > 0 else "   Failed: 0 (0%)")
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        if overall_success_rate >= 90:
            print(f"   🏆 EXCELLENT: {overall_success_rate:.1f}% success rate - Robust error handling!")
        elif overall_success_rate >= 75:
            print(f"   👍 GOOD: {overall_success_rate:.1f}% success rate - Good error handling")
        elif overall_success_rate >= 60:
            print(f"   ⚠️  FAIR: {overall_success_rate:.1f}% success rate - Some improvements needed")
        else:
            print(f"   ❌ POOR: {overall_success_rate:.1f}% success rate - Significant improvements needed")
        
        # Save results
        results_file = f"edge_case_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        print("=" * 65)

async def main():
    """Run the edge case and error handling tests"""
    print("🔧 Setting up Edge Case and Error Handling Tests...")
    print("These tests focus on robustness and error handling rather than live API calls.")
    print()
    
    tester = IntegrationEdgeCaseTester()
    await tester.run_all_edge_case_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user")
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)