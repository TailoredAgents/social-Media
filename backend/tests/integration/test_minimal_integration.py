#!/usr/bin/env python3
"""
Minimal Integration Test
"""
import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.integrations.twitter_client import twitter_client
from backend.integrations.linkedin_client import linkedin_client
from backend.integrations.instagram_client import instagram_client
from backend.integrations.facebook_client import facebook_client

async def test_integrations():
    """Test basic integration functionality"""
    print("Testing Social Media Integration Components...")
    print("=" * 50)
    
    # Test 1: Check if all clients are properly initialized
    print("\n1. Client Initialization Tests:")
    
    clients = {
        "Twitter": twitter_client,
        "LinkedIn": linkedin_client,
        "Instagram": instagram_client,
        "Facebook": facebook_client
    }
    
    for name, client in clients.items():
        try:
            has_make_request = hasattr(client, '_make_request')
            has_endpoints = hasattr(client, 'endpoints') or hasattr(client, 'api_base')
            
            if has_make_request and has_endpoints:
                print(f"   PASS {name} client properly initialized")
            else:
                print(f"   FAIL {name} client missing required methods")
        except Exception as e:
            print(f"   ERROR {name} client test failed: {e}")
    
    # Test 2: Content validation tests
    print("\n2. Content Validation Tests:")
    
    # Twitter validation
    try:
        valid_tweet = "Hello Twitter!"
        invalid_tweet = "x" * 300  # Too long
        
        valid_result, _ = twitter_client.is_valid_tweet_text(valid_tweet)
        invalid_result, error_msg = twitter_client.is_valid_tweet_text(invalid_tweet)
        
        if valid_result and not invalid_result:
            print("   PASS Twitter content validation working")
        else:
            print("   FAIL Twitter content validation failed")
    except Exception as e:
        print(f"   ERROR Twitter validation test failed: {e}")
    
    # LinkedIn validation
    try:
        valid_post = "Hello LinkedIn!"
        invalid_post = "x" * 4000  # Too long
        
        valid_result, _ = validate_post_content(valid_post)
        invalid_result, error_msg = validate_post_content(invalid_post)
        
        if valid_result and not invalid_result:
            print("   PASS LinkedIn content validation working")
        else:
            print("   FAIL LinkedIn content validation failed")
    except Exception as e:
        print(f"   ERROR LinkedIn validation test failed: {e}")
    
    # Instagram validation
    try:
        valid_caption = "Hello Instagram!"
        invalid_caption = "x" * 2500  # Too long
        
        valid_result, _ = instagram_client.validate_caption(valid_caption)
        invalid_result, error_msg = instagram_client.validate_caption(invalid_caption)
        
        if valid_result and not invalid_result:
            print("   PASS Instagram content validation working")
        else:
            print("   FAIL Instagram content validation failed")
    except Exception as e:
        print(f"   ERROR Instagram validation test failed: {e}")
    
    # Facebook validation
    try:
        valid_post = "Hello Facebook!"
        invalid_post = "x" * 70000  # Too long
        
        valid_result, _ = facebook_client.validate_post_content(valid_post)
        invalid_result, error_msg = facebook_client.validate_post_content(invalid_post)
        
        if valid_result and not invalid_result:
            print("   PASS Facebook content validation working")
        else:
            print("   FAIL Facebook content validation failed")
    except Exception as e:
        print(f"   ERROR Facebook validation test failed: {e}")
    
    # Test 3: Hashtag extraction tests
    print("\n3. Hashtag Extraction Tests:")
    
    test_text = "Testing #AI #MachineLearning #SocialMedia #Testing"
    
    try:
        twitter_hashtags = twitter_client.extract_hashtags(test_text)
        linkedin_hashtags = extract_hashtags(test_text)
        instagram_hashtags = instagram_client.extract_hashtags(test_text)
        facebook_hashtags = facebook_client.extract_hashtags(test_text)
        
        expected_count = 4
        results = {
            "Twitter": len(twitter_hashtags) == expected_count,
            "LinkedIn": len(linkedin_hashtags) == expected_count,
            "Instagram": len(instagram_hashtags) == expected_count,
            "Facebook": len(facebook_hashtags) == expected_count
        }
        
        for platform, result in results.items():
            print(f"   {'PASS' if result else 'FAIL'} {platform} hashtag extraction")
            
    except Exception as e:
        print(f"   ERROR Hashtag extraction test failed: {e}")
    
    # Test 4: Error handling with invalid tokens
    print("\n4. Error Handling Tests:")
    
    invalid_token = "invalid_token_123"
    
    # Test Twitter error handling
    try:
        await twitter_client.get_user_profile(invalid_token)
        print("   FAIL Twitter should have failed with invalid token")
    except Exception as e:
        if any(keyword in str(e).lower() for keyword in ["token", "auth", "invalid", "401", "403"]):
            print("   PASS Twitter properly handles invalid tokens")
        else:
            print(f"   WARN Twitter error handling unclear: {e}")
    
    # Test LinkedIn error handling
    try:
        await get_user_profile(invalid_token)
        print("   FAIL LinkedIn should have failed with invalid token")
    except Exception as e:
        if any(keyword in str(e).lower() for keyword in ["token", "auth", "invalid", "401", "403"]):
            print("   PASS LinkedIn properly handles invalid tokens")
        else:
            print(f"   WARN LinkedIn error handling unclear: {e}")
    
    print("\n" + "=" * 50)
    print("Integration Tests Completed")
    print("=" * 50)

if __name__ == "__main__":
    try:
        asyncio.run(test_integrations())
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)