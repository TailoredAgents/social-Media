#!/usr/bin/env python3
"""
Test Twitter OAuth 2.0 Real Setup
Run this after configuring your Twitter Developer Portal credentials
"""
import asyncio
from backend.core.config import get_settings
from backend.integrations.twitter_client import twitter_client

async def test_twitter_oauth():
    """Test Twitter OAuth 2.0 configuration"""
    print("🐦 Testing Twitter OAuth 2.0 Setup")
    print("=" * 50)
    
    settings = get_settings()
    
    # Check credentials
    print("1. Checking Credentials:")
    print(f"   Client ID: {'✅ Set' if settings.twitter_client_id else '❌ Missing'}")
    print(f"   Client Secret: {'✅ Set' if settings.twitter_client_secret else '❌ Missing'}")
    
    if not settings.twitter_client_id or not settings.twitter_client_secret:
        print("\n❌ Missing Twitter OAuth credentials!")
        print("Please update your .env file with:")
        print("TWITTER_CLIENT_ID=your_client_id_from_developer_portal")
        print("TWITTER_CLIENT_SECRET=your_client_secret_from_developer_portal")
        return
    
    # Test OAuth URL generation
    print("\n2. Testing OAuth URL Generation:")
    try:
        auth_url, state = twitter_client.get_oauth_authorization_url(
            redirect_uri="http://localhost:8000/api/social/callback/twitter",
            state="test_user:twitter"
        )
        print(f"   ✅ OAuth URL generated successfully")
        print(f"   🔗 URL: {auth_url[:80]}...")
        
        print(f"\n3. Next Steps:")
        print(f"   1. Visit this URL to test OAuth: {auth_url}")
        print(f"   2. Complete authorization on Twitter")
        print(f"   3. You'll be redirected to your callback URL")
        print(f"   4. Check your server logs for the authorization code")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error generating OAuth URL: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_twitter_oauth())