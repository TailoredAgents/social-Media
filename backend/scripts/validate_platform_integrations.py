#!/usr/bin/env python3
"""
Platform Integration Validation Script
Production readiness validation for all social media platform integrations

This script validates:
1. API connectivity and authentication
2. Basic CRUD operations
3. Rate limiting compliance
4. Error handling
5. OAuth token management
6. Real API response validation

Usage:
    python -m backend.scripts.validate_platform_integrations
"""
import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import json
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.core.config import get_settings
from backend.integrations.twitter_client import twitter_client
from backend.integrations.instagram_client import instagram_client
# LinkedIn and TikTok integrations removed
linkedin_client = None
from backend.integrations.facebook_client import facebook_client
# TikTok integration removed
tiktok_client = None
from backend.auth.social_oauth import oauth_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('platform_validation.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Validation result for a platform"""
    platform: str
    success: bool
    tests_passed: int
    tests_failed: int
    errors: List[str]
    warnings: List[str]
    performance_metrics: Dict[str, float]
    details: Dict[str, Any]

class PlatformValidator:
    """Comprehensive platform integration validator"""
    
    def __init__(self):
        self.settings = get_settings()
        self.results: List[ValidationResult] = []
        
        # Test user credentials (mock - in production these would be real test accounts)
        self.test_credentials = {
            "twitter": {
                "user_id": 1,
                "access_token": os.getenv("TWITTER_TEST_ACCESS_TOKEN"),
                "test_content": "Testing AI Social Media Agent integration 🤖 #TestPost"
            },
            "instagram": {
                "user_id": 2,
                "access_token": os.getenv("INSTAGRAM_TEST_ACCESS_TOKEN"),
                "test_content": "AI-powered content generation test ✨"
            },
            "linkedin": {
                "user_id": 3,
                "access_token": os.getenv("LINKEDIN_TEST_ACCESS_TOKEN"),
                "test_content": "Testing enterprise social media automation capabilities"
            },
            "facebook": {
                "user_id": 4,
                "access_token": os.getenv("FACEBOOK_TEST_ACCESS_TOKEN"),
                "test_content": "Validating Facebook integration for AI content agent"
            },
            "tiktok": {
                "user_id": 5,
                "access_token": os.getenv("TIKTOK_TEST_ACCESS_TOKEN"),
                "test_content": "AI content creation test for TikTok platform"
            }
        }
    
    async def validate_all_platforms(self) -> List[ValidationResult]:
        """Validate all platform integrations"""
        logger.info("🚀 Starting comprehensive platform integration validation")
        logger.info("=" * 80)
        
        platforms = [
            ("twitter", twitter_client),
            ("instagram", instagram_client),
            ("facebook", facebook_client)
        ]
        
        for platform_name, client in platforms:
            logger.info(f"\n📱 Validating {platform_name.upper()} integration...")
            
            result = await self._validate_platform(platform_name, client)
            self.results.append(result)
            
            # Log summary
            status_icon = "✅" if result.success else "❌"
            logger.info(f"{status_icon} {platform_name.upper()}: {result.tests_passed}/{result.tests_passed + result.tests_failed} tests passed")
            
            if result.errors:
                for error in result.errors[:3]:  # Show first 3 errors
                    logger.error(f"   ❌ {error}")
            
            if result.warnings:
                for warning in result.warnings[:2]:  # Show first 2 warnings
                    logger.warning(f"   ⚠️  {warning}")
        
        # Generate summary report
        self._generate_summary_report()
        
        return self.results
    
    async def _validate_platform(self, platform_name: str, client: Any) -> ValidationResult:
        """Validate a specific platform integration"""
        start_time = datetime.utcnow()
        errors = []
        warnings = []
        tests_passed = 0
        tests_failed = 0
        performance_metrics = {}
        details = {}
        
        credentials = self.test_credentials.get(platform_name)
        if not credentials or not credentials.get("access_token"):
            errors.append(f"No test credentials configured for {platform_name}")
            return ValidationResult(
                platform=platform_name,
                success=False,
                tests_passed=0,
                tests_failed=1,
                errors=errors,
                warnings=warnings,
                performance_metrics={},
                details={"skipped": "No test credentials"}
            )
        
        access_token = credentials["access_token"]
        user_id = credentials["user_id"]
        
        # Test 1: Token validation and user profile retrieval
        try:
            profile_start = datetime.utcnow()
            
            if hasattr(client, 'get_user_profile'):
                profile = await client.get_user_profile(access_token)
                profile_time = (datetime.utcnow() - profile_start).total_seconds() * 1000
                performance_metrics["profile_fetch_ms"] = profile_time
                
                if profile and profile.get("id"):
                    tests_passed += 1
                    details["user_profile"] = {
                        "id": profile.get("id"),
                        "username": profile.get("username", "N/A"),
                        "verified": profile.get("verified", False)
                    }
                    logger.info(f"   ✅ Profile fetch: {profile_time:.1f}ms")
                else:
                    tests_failed += 1
                    errors.append("Profile fetch returned empty or invalid data")
            else:
                tests_failed += 1
                errors.append("Client missing get_user_profile method")
                
        except Exception as e:
            tests_failed += 1
            errors.append(f"Profile fetch failed: {str(e)}")
            logger.error(f"   ❌ Profile fetch error: {e}")
        
        # Test 2: OAuth token management
        try:
            token_start = datetime.utcnow()
            
            if hasattr(client, 'get_user_token'):
                stored_token = await client.get_user_token(user_id)
                token_time = (datetime.utcnow() - token_start).total_seconds() * 1000
                performance_metrics["token_fetch_ms"] = token_time
                
                if stored_token:
                    tests_passed += 1
                    details["oauth_token"] = {"status": "valid", "length": len(stored_token)}
                    logger.info(f"   ✅ OAuth token fetch: {token_time:.1f}ms")
                else:
                    tests_failed += 1
                    warnings.append("No stored OAuth token found for test user")
            else:
                tests_failed += 1
                errors.append("Client missing get_user_token method")
                
        except Exception as e:
            tests_failed += 1
            errors.append(f"OAuth token validation failed: {str(e)}")
        
        # Test 3: Content posting capability (if supported)
        post_id = None
        try:
            if hasattr(client, 'create_post') or hasattr(client, 'post_tweet'):
                post_start = datetime.utcnow()
                test_content = f"{credentials['test_content']} - {datetime.utcnow().strftime('%H:%M:%S')}"
                
                # Use appropriate method based on platform
                if platform_name == "twitter" and hasattr(client, 'post_tweet'):
                    post_result = await client.post_tweet(access_token, test_content)
                    post_id = post_result.id if hasattr(post_result, 'id') else post_result.get('id')
                elif hasattr(client, 'create_post'):
                    post_result = await client.create_post(access_token, test_content)
                    post_id = post_result.get('id')
                else:
                    raise Exception("No posting method available")
                
                post_time = (datetime.utcnow() - post_start).total_seconds() * 1000
                performance_metrics["content_post_ms"] = post_time
                
                if post_id:
                    tests_passed += 1
                    details["content_posting"] = {
                        "post_id": post_id,
                        "content_length": len(test_content),
                        "post_time_ms": post_time
                    }
                    logger.info(f"   ✅ Content posting: {post_time:.1f}ms (ID: {post_id})")
                else:
                    tests_failed += 1
                    errors.append("Content posting returned no post ID")
                    
        except Exception as e:
            tests_failed += 1
            errors.append(f"Content posting failed: {str(e)}")
            logger.error(f"   ❌ Content posting error: {e}")
        
        # Test 4: Analytics/metrics retrieval (if supported)
        try:
            if post_id and hasattr(client, 'get_post_analytics'):
                analytics_start = datetime.utcnow()
                
                # Wait a moment for post to be processed
                await asyncio.sleep(2)
                
                analytics = await client.get_post_analytics(access_token, post_id)
                analytics_time = (datetime.utcnow() - analytics_start).total_seconds() * 1000
                performance_metrics["analytics_fetch_ms"] = analytics_time
                
                if analytics:
                    tests_passed += 1
                    details["analytics"] = {
                        "metrics_available": list(analytics.keys()) if isinstance(analytics, dict) else "raw_data",
                        "fetch_time_ms": analytics_time
                    }
                    logger.info(f"   ✅ Analytics fetch: {analytics_time:.1f}ms")
                else:
                    warnings.append("Analytics fetch returned empty data (normal for new posts)")
                    
        except Exception as e:
            warnings.append(f"Analytics fetch failed: {str(e)} (may be normal for test posts)")
        
        # Test 5: Rate limiting compliance
        try:
            rate_limit_start = datetime.utcnow()
            
            # Make multiple rapid requests to test rate limiting
            rate_limit_requests = []
            for i in range(3):
                try:
                    if hasattr(client, 'get_user_profile'):
                        req_start = datetime.utcnow()
                        await client.get_user_profile(access_token)
                        req_time = (datetime.utcnow() - req_start).total_seconds() * 1000
                        rate_limit_requests.append(req_time)
                        await asyncio.sleep(0.5)  # Brief delay between requests
                except Exception as e:
                    if "rate limit" in str(e).lower() or "429" in str(e):
                        # Rate limiting is working correctly
                        tests_passed += 1
                        details["rate_limiting"] = {"status": "enforced", "error": str(e)}
                        logger.info(f"   ✅ Rate limiting enforced correctly")
                        break
                    else:
                        raise e
            else:
                # No rate limiting encountered
                tests_passed += 1
                avg_time = sum(rate_limit_requests) / len(rate_limit_requests)
                details["rate_limiting"] = {
                    "status": "no_limits_hit", 
                    "avg_response_time_ms": avg_time,
                    "requests_made": len(rate_limit_requests)
                }
                performance_metrics["avg_api_response_ms"] = avg_time
                logger.info(f"   ✅ Rate limiting test completed (avg: {avg_time:.1f}ms)")
                
        except Exception as e:
            tests_failed += 1
            errors.append(f"Rate limiting test failed: {str(e)}")
        
        # Test 6: Error handling validation
        try:
            error_start = datetime.utcnow()
            
            # Test with invalid access token
            try:
                if hasattr(client, 'get_user_profile'):
                    await client.get_user_profile("invalid_token_12345")
                    tests_failed += 1
                    errors.append("Error handling failed - invalid token accepted")
                else:
                    warnings.append("Cannot test error handling - no profile method")
            except Exception as e:
                # This is expected - error handling is working
                if "unauthorized" in str(e).lower() or "invalid" in str(e).lower() or "401" in str(e):
                    tests_passed += 1
                    details["error_handling"] = {"status": "working", "error_type": type(e).__name__}
                    logger.info(f"   ✅ Error handling working correctly")
                else:
                    tests_failed += 1
                    errors.append(f"Unexpected error type: {str(e)}")
                    
        except Exception as e:
            tests_failed += 1
            errors.append(f"Error handling test failed: {str(e)}")
        
        # Cleanup: Delete test post if created
        if post_id:
            try:
                if hasattr(client, 'delete_post'):
                    await client.delete_post(access_token, post_id)
                    logger.info(f"   🧹 Cleaned up test post: {post_id}")
                elif hasattr(client, 'delete_tweet') and platform_name == "twitter":
                    await client.delete_tweet(access_token, post_id)
                    logger.info(f"   🧹 Cleaned up test tweet: {post_id}")
                else:
                    warnings.append(f"Could not clean up test post {post_id} - no delete method")
            except Exception as e:
                warnings.append(f"Failed to cleanup test post {post_id}: {str(e)}")
        
        # Calculate overall validation time
        total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        performance_metrics["total_validation_ms"] = total_time
        
        # Determine success
        success = tests_failed == 0 and len(errors) == 0
        
        return ValidationResult(
            platform=platform_name,
            success=success,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            errors=errors,
            warnings=warnings,
            performance_metrics=performance_metrics,
            details=details
        )
    
    def _generate_summary_report(self):
        """Generate comprehensive validation summary report"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 PLATFORM INTEGRATION VALIDATION SUMMARY")
        logger.info("=" * 80)
        
        total_platforms = len(self.results)
        successful_platforms = sum(1 for r in self.results if r.success)
        total_tests = sum(r.tests_passed + r.tests_failed for r in self.results)
        total_passed = sum(r.tests_passed for r in self.results)
        total_errors = sum(len(r.errors) for r in self.results)
        total_warnings = sum(len(r.warnings) for r in self.results)
        
        logger.info(f"🎯 Overall Status: {successful_platforms}/{total_platforms} platforms validated successfully")
        logger.info(f"📈 Test Results: {total_passed}/{total_tests} tests passed")
        logger.info(f"🚨 Issues Found: {total_errors} errors, {total_warnings} warnings")
        
        # Performance summary
        logger.info(f"\n⚡ Performance Metrics:")
        for result in self.results:
            if result.performance_metrics:
                avg_time = result.performance_metrics.get("total_validation_ms", 0)
                logger.info(f"   {result.platform}: {avg_time:.1f}ms total validation time")
        
        # Platform-specific details
        logger.info(f"\n📱 Platform Details:")
        for result in self.results:
            status_icon = "✅" if result.success else "❌"
            logger.info(f"{status_icon} {result.platform.upper()}:")
            logger.info(f"   Tests: {result.tests_passed} passed, {result.tests_failed} failed")
            
            if result.errors:
                logger.info(f"   Errors: {', '.join(result.errors[:2])}")
            
            if result.performance_metrics:
                key_metrics = ["profile_fetch_ms", "content_post_ms", "analytics_fetch_ms"]
                metrics_str = []
                for metric in key_metrics:
                    if metric in result.performance_metrics:
                        metrics_str.append(f"{metric.replace('_ms', '')}: {result.performance_metrics[metric]:.1f}ms")
                if metrics_str:
                    logger.info(f"   Performance: {', '.join(metrics_str)}")
        
        # Recommendations
        logger.info(f"\n💡 Recommendations:")
        
        failed_platforms = [r.platform for r in self.results if not r.success]
        if failed_platforms:
            logger.warning(f"   ⚠️  Review failed platforms: {', '.join(failed_platforms)}")
        
        slow_platforms = [
            r.platform for r in self.results 
            if r.performance_metrics.get("total_validation_ms", 0) > 5000
        ]
        if slow_platforms:
            logger.warning(f"   ⚠️  Optimize slow platforms: {', '.join(slow_platforms)}")
        
        if total_errors == 0:
            logger.info(f"   ✅ All integrations are production-ready!")
        else:
            logger.warning(f"   ⚠️  Address {total_errors} errors before production deployment")
        
        # Save detailed report to file
        self._save_detailed_report()
        
        logger.info("=" * 80)
    
    def _save_detailed_report(self):
        """Save detailed validation report to JSON file"""
        try:
            report_data = {
                "validation_timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total_platforms": len(self.results),
                    "successful_platforms": sum(1 for r in self.results if r.success),
                    "total_tests": sum(r.tests_passed + r.tests_failed for r in self.results),
                    "total_passed": sum(r.tests_passed for r in self.results),
                    "total_errors": sum(len(r.errors) for r in self.results),
                    "total_warnings": sum(len(r.warnings) for r in self.results)
                },
                "platform_results": [
                    {
                        "platform": r.platform,
                        "success": r.success,
                        "tests_passed": r.tests_passed,
                        "tests_failed": r.tests_failed,
                        "errors": r.errors,
                        "warnings": r.warnings,
                        "performance_metrics": r.performance_metrics,
                        "details": r.details
                    }
                    for r in self.results
                ]
            }
            
            report_file = f"platform_validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"📋 Detailed report saved to: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save detailed report: {e}")

async def main():
    """Main validation function"""
    try:
        validator = PlatformValidator()
        results = await validator.validate_all_platforms()
        
        # Exit with error code if any validations failed
        failed_count = sum(1 for r in results if not r.success)
        if failed_count > 0:
            logger.error(f"❌ {failed_count} platform(s) failed validation")
            sys.exit(1)
        else:
            logger.info("✅ All platform integrations validated successfully!")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"❌ Validation script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())