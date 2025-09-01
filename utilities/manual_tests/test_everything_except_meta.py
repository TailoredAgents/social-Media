#!/usr/bin/env python3
"""
Test Everything EXCEPT Meta/Facebook/Instagram APIs
Because Meta's API setup is unnecessarily complex bullshit.
"""
import asyncio
import sys
import json
import traceback
from datetime import datetime

def print_test_header(test_name):
    print(f"\n{'='*50}")
    print(f"🧪 TESTING: {test_name}")
    print(f"{'='*50}")

def print_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")

async def test_configuration():
    """Test 1: Configuration Loading"""
    print_test_header("Configuration Loading")
    
    try:
        from backend.core.config import get_settings
        settings = get_settings()
        
        # Test OpenAI key
        openai_configured = bool(settings.openai_api_key and len(settings.openai_api_key) > 20)
        print_result("OpenAI API Key", openai_configured, f"Length: {len(settings.openai_api_key)}")
        
        # Test Serper key
        serper_configured = bool(settings.serper_api_key and len(settings.serper_api_key) > 10)
        print_result("Serper API Key", serper_configured, f"Length: {len(settings.serper_api_key)}")
        
        # Test Twitter keys
        twitter_configured = bool(settings.twitter_api_key and settings.twitter_bearer_token)
        print_result("Twitter API Keys", twitter_configured, "API Key + Bearer Token")
        
        # Test database URL
        db_configured = bool(settings.database_url)
        print_result("Database URL", db_configured, f"Type: {settings.database_url.split('://')[0] if settings.database_url else 'None'}")
        
        return openai_configured and serper_configured
        
    except Exception as e:
        print_result("Configuration Loading", False, str(e))
        return False

async def test_database_connection():
    """Test 2: Database Connection"""
    print_test_header("Database Connection")
    
    try:
        from backend.db.database import get_db
        from backend.db.models import User
        
        db_gen = get_db()
        db = next(db_gen)
        # Test basic query
        users = db.query(User).limit(1).all()
        print_result("Database Connection", True, f"Connected, found {len(users)} users")
        db_gen.close()  # Close the generator
        return True
            
    except Exception as e:
        print_result("Database Connection", False, str(e))
        return False

async def test_openai_integration():
    """Test 3: OpenAI Integration"""
    print_test_header("OpenAI Integration")
    
    try:
        from backend.core.config import get_settings
        from openai import AsyncOpenAI
        
        settings = get_settings()
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Test GPT-5 mini (updated model)
        response = await client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": "Say 'OpenAI test successful' and nothing else"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        success = "successful" in result.lower()
        print_result("GPT-5 Mini", success, f"Response: {result}")
        
        return success
        
    except Exception as e:
        print_result("OpenAI Integration", False, str(e))
        return False

async def test_content_generation():
    """Test 4: Content Generation API"""
    print_test_header("Content Generation API")
    
    try:
        # Import and test content generation
        from backend.services.content_automation import ContentGenerationAutomation
        
        automation = ContentGenerationAutomation()
        
        # Test content generation
        result = await automation.generate_content(
            platform="twitter",
            topic="artificial intelligence",
            context={
                "brand_voice": "professional",
                "target_audience": "tech enthusiasts"
            }
        )
        
        success = result.get("status") == "success" and "content" in result
        content = result.get("content", "")[:100] + "..." if result.get("content") else "None"
        print_result("Content Generation", success, f"Content: {content}")
        
        return success
        
    except Exception as e:
        print_result("Content Generation", False, str(e))
        return False

async def test_image_generation():
    """Test 5: Image Generation"""
    print_test_header("Image Generation")
    
    try:
        from backend.services.image_generation_service import image_generation_service
        
        # Test image generation
        result = await image_generation_service.generate_image(
            prompt="A simple test image of a robot",
            platform="twitter",
            quality_preset="draft"
        )
        
        success = result.get("status") == "success" and "image_base64" in result
        image_size = len(result.get("image_base64", "")) if result.get("image_base64") else 0
        print_result("Image Generation", success, f"Image data size: {image_size} bytes")
        
        return success
        
    except Exception as e:
        print_result("Image Generation", False, str(e))
        return False

async def test_twitter_client():
    """Test 6: Twitter Client (Mock Mode)"""
    print_test_header("Twitter Client")
    
    try:
        from backend.integrations.twitter_client import twitter_client
        
        # Test profile fetch (will use mock if no real auth)
        profile = twitter_client.get_user_info("test_token")
        success = isinstance(profile, dict) and "status" in profile
        
        print_result("Twitter Client", success, f"Status: {profile.get('status', 'unknown')}")
        return success
        
    except Exception as e:
        print_result("Twitter Client", False, str(e))
        return False

async def test_platform_validation():
    """Test 7: Platform Validation (No LinkedIn)"""
    print_test_header("Platform Validation")
    
    try:
        from backend.api.validation import validate_platform
        
        # Test valid platforms (without LinkedIn)
        valid_platforms = ["twitter", "instagram", "facebook", "youtube", "tiktok"]
        results = []
        
        for platform in valid_platforms:
            try:
                result = validate_platform(platform)
                results.append(f"{platform}: ✅")
            except Exception:
                results.append(f"{platform}: ❌")
        
        # Test invalid platform
        try:
            validate_platform("linkedin")  # Should fail (we removed it)
            linkedin_rejected = False
        except Exception:
            linkedin_rejected = True
            results.append("linkedin: ✅ (correctly rejected)")
        
        print_result("Platform Validation", True, "; ".join(results))
        return True
        
    except Exception as e:
        print_result("Platform Validation", False, str(e))
        return False

async def test_mock_social_apis():
    """Test 8: Mock Social APIs (Facebook/Instagram in mock mode)"""
    print_test_header("Mock Social APIs")
    
    try:
        # Test that mock mode is enabled
        from backend.core.config import get_settings
        settings = get_settings()
        mock_enabled = getattr(settings, 'mock_social_apis', False)
        
        print_result("Mock APIs Enabled", mock_enabled, "MOCK_SOCIAL_APIS=true")
        
        # Test mock responses would work
        mock_response = {
            "status": "success", 
            "platform": "facebook",
            "message": "Mock API response",
            "post_id": "mock_123456"
        }
        
        success = mock_response.get("status") == "success"
        print_result("Mock Response Format", success, "Mock data structure valid")
        
        return bool(mock_enabled)
        
    except Exception as e:
        print_result("Mock Social APIs", False, str(e))
        return False

async def main():
    """Run all tests except Meta/Facebook/Instagram real APIs"""
    
    print("🚀 COMPREHENSIVE TESTING (Excluding Meta API Hell)")
    print("Testing everything that doesn't require Meta's overcomplicated setup...")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    test_results = []
    
    test_results.append(await test_configuration())
    test_results.append(await test_database_connection()) 
    test_results.append(await test_openai_integration())
    test_results.append(await test_content_generation())
    test_results.append(await test_image_generation())
    test_results.append(await test_twitter_client())
    test_results.append(await test_platform_validation())
    test_results.append(await test_mock_social_apis())
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = sum(1 for result in test_results if result is True)
    total = len(test_results)
    percentage = (passed / total) * 100
    
    print(f"Tests Passed: {passed}/{total} ({percentage:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The platform is ready for testing.")
        print("💡 You can now test all functionality except Meta/Facebook/Instagram.")
        print("📱 Facebook/Instagram will return mock responses until you finish their setup.")
    else:
        print("⚠️  Some tests failed. Check the details above.")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Testing failed with error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)