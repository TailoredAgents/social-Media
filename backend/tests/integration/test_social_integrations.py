#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Social Media Integration Test Suite
Tests real API connections and posting capabilities for all social media platforms
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.integrations.twitter_client import twitter_client, TwitterPost
from backend.integrations.linkedin_client import linkedin_client, LinkedInPost
from backend.integrations.instagram_client import instagram_client, InstagramMedia
from backend.integrations.facebook_client import facebook_client, FacebookPost

class SocialMediaIntegrationTester:
    """
    Comprehensive test suite for social media integrations
    Tests real API connections, posting, and analytics retrieval
    """
    
    def __init__(self):
        """Initialize the integration tester"""
        self.test_results = {
            "twitter": {"status": "pending", "tests": [], "errors": []},
            : {"status": "pending", "tests": [], "errors": []},
            "instagram": {"status": "pending", "tests": [], "errors": []},
            "facebook": {"status": "pending", "tests": [], "errors": []}
        }
        
        # Load test credentials from environment
        self.credentials = {
            "twitter": {
                "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
                "refresh_token": os.getenv("TWITTER_REFRESH_TOKEN")
            },
            : {
                "access_token": os.getenv("LINKEDIN_ACCESS_TOKEN"),
                "user_id": os.getenv("LINKEDIN_USER_ID")
            },
            "instagram": {
                "access_token": os.getenv("FACEBOOK_ACCESS_TOKEN"),  # Uses Facebook token
                "ig_user_id": os.getenv("INSTAGRAM_BUSINESS_ID"),
                "page_id": os.getenv("FACEBOOK_PAGE_ID")
            },
            "facebook": {
                "access_token": os.getenv("FACEBOOK_ACCESS_TOKEN"),
                "page_id": os.getenv("FACEBOOK_PAGE_ID"),
                "page_access_token": os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
            }
        }
        
        print("🚀 Social Media Integration Test Suite Starting...")
        print("=" * 60)
    
    async def run_all_tests(self):
        """Run comprehensive tests for all platforms"""
        platforms = ["twitter", , "instagram", "facebook"]
        
        for platform in platforms:
            print(f"\n🔍 Testing {platform.upper()} Integration...")
            print("-" * 40)
            
            try:
                if platform == "twitter":
                    await self.test_twitter_integration()
                elif platform == :
                    await self.test_linkedin_integration()
                elif platform == "instagram":
                    await self.test_instagram_integration()
                elif platform == "facebook":
                    await self.test_facebook_integration()
                
                self.test_results[platform]["status"] = "completed"
                print(f"✅ {platform.upper()} integration tests completed")
                
            except Exception as e:
                self.test_results[platform]["status"] = "failed"
                self.test_results[platform]["errors"].append(str(e))
                print(f"❌ {platform.upper()} integration tests failed: {e}")
        
        # Print final results
        self.print_final_results()
    
    async def test_twitter_integration(self):
        """Test Twitter API integration"""
        platform = "twitter"
        creds = self.credentials[platform]
        
        if not creds["access_token"]:
            raise Exception("Twitter access token not found in environment")
        
        # Test 1: Get user profile
        print("📝 Test 1: Getting Twitter user profile...")
        try:
            profile = await twitter_client.get_user_profile(creds["access_token"])
            self.test_results[platform]["tests"].append({
                "name": "get_user_profile",
                "status": "passed",
                "data": {"username": profile.get("username"), "followers": profile.get("public_metrics", {}).get("followers_count", 0)}
            })
            print(f"   ✅ Profile retrieved: @{profile.get('username')} ({profile.get('public_metrics', {}).get('followers_count', 0)} followers)")
        except Exception as e:
            self.test_results[platform]["tests"].append({
                "name": "get_user_profile",
                "status": "failed",
                "error": str(e)
            })
            print(f"   ❌ Profile test failed: {e}")
        
        # Test 2: Post a test tweet
        print("📝 Test 2: Posting test tweet...")
        test_tweet = f"🤖 AI Social Media Agent Live Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} #AITest #SocialMediaAutomation"
        
        try:
            posted_tweet = await twitter_client.post_tweet(
                access_token=creds["access_token"],
                text=test_tweet
            )
            self.test_results[platform]["tests"].append({
                "name": "post_tweet",
                "status": "passed",
                "data": {"tweet_id": posted_tweet.id, "text": posted_tweet.text}
            })
            print(f"   ✅ Tweet posted successfully: {posted_tweet.id}")
            
            # Test 3: Get tweet analytics
            print("📝 Test 3: Getting tweet analytics...")
            await asyncio.sleep(5)  # Wait for metrics to be available
            
            try:
                analytics = await twitter_client.get_tweet_analytics(
                    access_token=creds["access_token"],
                    tweet_id=posted_tweet.id
                )
                self.test_results[platform]["tests"].append({
                    "name": "get_tweet_analytics",
                    "status": "passed",
                    "data": {
                        "impressions": analytics.impressions,
                        "likes": analytics.likes,
                        "retweets": analytics.retweets,
                        "engagement_rate": analytics.engagement_rate
                    }
                })
                print(f"   ✅ Analytics retrieved: {analytics.impressions} impressions, {analytics.likes} likes")
            except Exception as e:
                self.test_results[platform]["tests"].append({
                    "name": "get_tweet_analytics",
                    "status": "failed",
                    "error": str(e)
                })
                print(f"   ❌ Analytics test failed: {e}")
            
            # Test 4: Delete test tweet
            print("📝 Test 4: Deleting test tweet...")
            try:
                deleted = await twitter_client.delete_tweet(
                    access_token=creds["access_token"],
                    tweet_id=posted_tweet.id
                )
                self.test_results[platform]["tests"].append({
                    "name": "delete_tweet",
                    "status": "passed" if deleted else "failed",
                    "data": {"deleted": deleted}
                })
                print(f"   ✅ Tweet deleted successfully" if deleted else f"   ❌ Tweet deletion failed")
            except Exception as e:
                self.test_results[platform]["tests"].append({
                    "name": "delete_tweet",
                    "status": "failed",
                    "error": str(e)
                })
                print(f"   ❌ Delete test failed: {e}")
                
        except Exception as e:
            self.test_results[platform]["tests"].append({
                "name": "post_tweet",
                "status": "failed",
                "error": str(e)
            })
            print(f"   ❌ Tweet posting failed: {e}")
    
    async def test_linkedin_integration(self):
        """Test LinkedIn API integration"""
        platform = 
        creds = self.credentials[platform]
        
        if not creds["access_token"]:
            raise Exception("LinkedIn access token not found in environment")
        
        # Test 1: Get user profile
        print("📝 Test 1: Getting LinkedIn user profile...")
        try:
            profile = await get_user_profile(creds["access_token"])
            self.test_results[platform]["tests"].append({
                "name": "get_user_profile",
                "status": "passed",
                "data": {
                    "name": f"{profile.get('first_name', '')} {profile.get('last_name', '')}",
                    "connections": profile.get("connections", 0),
                    "headline": profile.get("headline", "")
                }
            })
            print(f"   ✅ Profile retrieved: {profile.get('first_name', '')} {profile.get('last_name', '')} ({profile.get('connections', 0)} connections)")
        except Exception as e:
            self.test_results[platform]["tests"].append({
                "name": "get_user_profile",
                "status": "failed",
                "error": str(e)
            })
            print(f"   ❌ Profile test failed: {e}")
        
        # Test 2: Create a test post
        print("📝 Test 2: Creating LinkedIn test post...")
        test_post = f"""🚀 AI Social Media Agent Integration Test
        
Testing our automated LinkedIn posting capabilities with professional content optimization.

Key Features:
• AI-powered content generation
• Multi-platform social media management
• Real-time analytics and insights
• Professional audience targeting

#AIAutomation #SocialMediaManagement #LinkedIn #TechInnovation

Test timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        try:
            posted_post = await create_post(
                access_token=creds["access_token"],
                text=test_post,
                visibility="PUBLIC"
            )
            self.test_results[platform]["tests"].append({
                "name": "create_post",
                "status": "passed",
                "data": {"post_id": posted_post.id, "text_length": len(posted_post.text)}
            })
            print(f"   ✅ LinkedIn post created successfully: {posted_post.id}")
            
            # Test 3: Get post analytics
            print("📝 Test 3: Getting LinkedIn post analytics...")
            await asyncio.sleep(10)  # Wait for metrics to be available
            
            try:
                analytics = await get_post_analytics(
                    access_token=creds["access_token"],
                    post_id=posted_post.id
                )
                self.test_results[platform]["tests"].append({
                    "name": "get_post_analytics",
                    "status": "passed",
                    "data": {
                        "impressions": analytics.impressions,
                        "clicks": analytics.clicks,
                        "reactions": analytics.reactions,
                        "engagement_rate": analytics.engagement_rate
                    }
                })
                print(f"   ✅ Analytics retrieved: {analytics.impressions} impressions, {analytics.reactions} reactions")
            except Exception as e:
                self.test_results[platform]["tests"].append({
                    "name": "get_post_analytics",
                    "status": "failed",
                    "error": str(e)
                })
                print(f"   ⚠️  Analytics test failed (expected for new posts): {e}")
            
        except Exception as e:
            self.test_results[platform]["tests"].append({
                "name": "create_post",
                "status": "failed",
                "error": str(e)
            })
            print(f"   ❌ LinkedIn post creation failed: {e}")
    
    async def test_instagram_integration(self):
        """Test Instagram API integration"""
        platform = "instagram"
        creds = self.credentials[platform]
        
        if not all([creds["access_token"], creds["ig_user_id"]]):
            raise Exception("Instagram credentials not found in environment")
        
        # Test 1: Get Instagram profile
        print("📝 Test 1: Getting Instagram profile...")
        try:
            profile = await instagram_client.get_profile(
                access_token=creds["access_token"],
                ig_user_id=creds["ig_user_id"]
            )
            self.test_results[platform]["tests"].append({
                "name": "get_profile",
                "status": "passed",
                "data": {
                    "username": profile.username,
                    "followers": profile.followers_count,
                    "media_count": profile.media_count
                }
            })
            print(f"   ✅ Profile retrieved: @{profile.username} ({profile.followers_count} followers, {profile.media_count} posts)")
        except Exception as e:
            self.test_results[platform]["tests"].append({
                "name": "get_profile",
                "status": "failed",
                "error": str(e)
            })
            print(f"   ❌ Profile test failed: {e}")
        
        # Test 2: Get recent media
        print("📝 Test 2: Getting recent Instagram media...")
        try:
            media_list = await instagram_client.get_user_media(
                access_token=creds["access_token"],
                ig_user_id=creds["ig_user_id"],
                limit=5
            )
            self.test_results[platform]["tests"].append({
                "name": "get_user_media",
                "status": "passed",
                "data": {"media_count": len(media_list)}
            })
            print(f"   ✅ Retrieved {len(media_list)} recent media items")
            
            # Test 3: Get media insights for latest post
            if media_list:
                print("📝 Test 3: Getting media insights...")
                try:
                    latest_media = media_list[0]
                    insights = await instagram_client.get_media_insights(
                        access_token=creds["access_token"],
                        media_id=latest_media.id
                    )
                    self.test_results[platform]["tests"].append({
                        "name": "get_media_insights",
                        "status": "passed",
                        "data": {
                            "impressions": insights.impressions,
                            "reach": insights.reach,
                            "engagement": insights.engagement
                        }
                    })
                    print(f"   ✅ Insights retrieved: {insights.impressions} impressions, {insights.reach} reach")
                except Exception as e:
                    self.test_results[platform]["tests"].append({
                        "name": "get_media_insights",
                        "status": "failed",
                        "error": str(e)
                    })
                    print(f"   ⚠️  Insights test failed: {e}")
        
        except Exception as e:
            self.test_results[platform]["tests"].append({
                "name": "get_user_media",
                "status": "failed",
                "error": str(e)
            })
            print(f"   ❌ Media retrieval failed: {e}")
        
        # Test 4: Check publishing limits
        print("📝 Test 4: Checking Instagram publishing limits...")
        try:
            limits = await instagram_client.check_publishing_limit(
                access_token=creds["access_token"],
                ig_user_id=creds["ig_user_id"]
            )
            self.test_results[platform]["tests"].append({
                "name": "check_publishing_limit",
                "status": "passed",
                "data": limits
            })
            print(f"   ✅ Publishing limits: {limits['quota_usage']}/{limits['quota_total']} used")
        except Exception as e:
            self.test_results[platform]["tests"].append({
                "name": "check_publishing_limit",
                "status": "failed",
                "error": str(e)
            })
            print(f"   ❌ Publishing limits check failed: {e}")
    
    async def test_facebook_integration(self):
        """Test Facebook API integration"""
        platform = "facebook"
        creds = self.credentials[platform]
        
        if not all([creds["access_token"], creds["page_id"]]):
            raise Exception("Facebook credentials not found in environment")
        
        # Test 1: Get user's Facebook pages
        print("📝 Test 1: Getting Facebook pages...")
        try:
            pages = await facebook_client.get_user_pages(creds["access_token"])
            managed_pages = [p for p in pages if p.id == creds["page_id"]]
            
            self.test_results[platform]["tests"].append({
                "name": "get_user_pages",
                "status": "passed",
                "data": {
                    "total_pages": len(pages),
                    "target_page_found": len(managed_pages) > 0
                }
            })
            print(f"   ✅ Found {len(pages)} managed pages, target page found: {len(managed_pages) > 0}")
            
            if managed_pages:
                target_page = managed_pages[0]
                page_token = target_page.access_token or creds.get("page_access_token")
                
                # Test 2: Get page info
                print("📝 Test 2: Getting Facebook page info...")
                try:
                    page_info = await facebook_client.get_page_info(
                        page_access_token=page_token,
                        page_id=creds["page_id"]
                    )
                    self.test_results[platform]["tests"].append({
                        "name": "get_page_info",
                        "status": "passed",
                        "data": {
                            "name": page_info.name,
                            "followers": page_info.followers_count,
                            "fan_count": page_info.fan_count
                        }
                    })
                    print(f"   ✅ Page info: {page_info.name} ({page_info.followers_count} followers)")
                except Exception as e:
                    self.test_results[platform]["tests"].append({
                        "name": "get_page_info",
                        "status": "failed",
                        "error": str(e)
                    })
                    print(f"   ❌ Page info test failed: {e}")
                
                # Test 3: Create a test post
                print("📝 Test 3: Creating Facebook test post...")
                test_post = f"""🚀 AI Social Media Agent Facebook Integration Test

Our automated social media management platform is successfully integrating with Facebook's Graph API!

✨ Key Capabilities:
• Automated content posting across platforms
• Real-time analytics and insights
• Smart content optimization
• Professional scheduling features

#FacebookAPI #AIAutomation #SocialMediaManagement #TechTest

Test executed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
                
                try:
                    posted_post = await facebook_client.create_text_post(
                        page_access_token=page_token,
                        page_id=creds["page_id"],
                        message=test_post
                    )
                    self.test_results[platform]["tests"].append({
                        "name": "create_text_post",
                        "status": "passed",
                        "data": {"post_id": posted_post.id, "message_length": len(posted_post.message)}
                    })
                    print(f"   ✅ Facebook post created successfully: {posted_post.id}")
                    
                    # Test 4: Get post insights
                    print("📝 Test 4: Getting Facebook post insights...")
                    await asyncio.sleep(10)  # Wait for metrics to be available
                    
                    try:
                        insights = await facebook_client.get_post_insights(
                            access_token=page_token,
                            post_id=posted_post.id
                        )
                        self.test_results[platform]["tests"].append({
                            "name": "get_post_insights",
                            "status": "passed",
                            "data": {
                                "impressions": insights.impressions,
                                "reach": insights.reach,
                                "engagement": insights.engagement
                            }
                        })
                        print(f"   ✅ Insights retrieved: {insights.impressions} impressions, {insights.reach} reach")
                    except Exception as e:
                        self.test_results[platform]["tests"].append({
                            "name": "get_post_insights",
                            "status": "failed",
                            "error": str(e)
                        })
                        print(f"   ⚠️  Insights test failed (expected for new posts): {e}")
                
                except Exception as e:
                    self.test_results[platform]["tests"].append({
                        "name": "create_text_post",
                        "status": "failed",
                        "error": str(e)
                    })
                    print(f"   ❌ Facebook post creation failed: {e}")
        
        except Exception as e:
            self.test_results[platform]["tests"].append({
                "name": "get_user_pages",
                "status": "failed",
                "error": str(e)
            })
            print(f"   ❌ Pages retrieval failed: {e}")
    
    def print_final_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 60)
        print("🏁 SOCIAL MEDIA INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for platform, results in self.test_results.items():
            platform_tests = len(results["tests"])
            platform_passed = len([t for t in results["tests"] if t["status"] == "passed"])
            platform_failed = len([t for t in results["tests"] if t["status"] == "failed"])
            
            total_tests += platform_tests
            passed_tests += platform_passed
            failed_tests += platform_failed
            
            status_icon = "✅" if results["status"] == "completed" else "❌" if results["status"] == "failed" else "⏳"
            
            print(f"\n{status_icon} {platform.upper()}")
            print(f"   Status: {results['status']}")
            print(f"   Tests: {platform_passed}/{platform_tests} passed")
            
            if results["errors"]:
                print(f"   Errors: {len(results['errors'])}")
                for error in results["errors"]:
                    print(f"     - {error}")
            
            # Show individual test results
            for test in results["tests"]:
                test_icon = "✅" if test["status"] == "passed" else "❌"
                print(f"     {test_icon} {test['name']}")
                if test["status"] == "failed" and "error" in test:
                    print(f"        Error: {test['error']}")
        
        # Summary
        print(f"\n📊 OVERALL SUMMARY")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ({(passed_tests/total_tests*100):.1f}%)" if total_tests > 0 else "   Passed: 0 (0%)")
        print(f"   Failed: {failed_tests} ({(failed_tests/total_tests*100):.1f}%)" if total_tests > 0 else "   Failed: 0 (0%)")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        if success_rate >= 80:
            print(f"   🎉 EXCELLENT: {success_rate:.1f}% success rate!")
        elif success_rate >= 60:
            print(f"   👍 GOOD: {success_rate:.1f}% success rate")
        else:
            print(f"   ⚠️  NEEDS IMPROVEMENT: {success_rate:.1f}% success rate")
        
        # Save results to file
        results_file = f"integration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        print("=" * 60)

async def main():
    """Run the social media integration tests"""
    print("🔧 Setting up Social Media Integration Tests...")
    
    # Check for required environment variables
    required_vars = [
        "TWITTER_ACCESS_TOKEN",
        "LINKEDIN_ACCESS_TOKEN", 
        "FACEBOOK_ACCESS_TOKEN",
        "FACEBOOK_PAGE_ID",
        "INSTAGRAM_BUSINESS_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("Some tests may be skipped or fail due to missing credentials.")
        print("Set these variables in your environment or .env file for complete testing.")
        print()
    
    tester = SocialMediaIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user")
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)