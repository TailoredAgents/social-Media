#!/usr/bin/env python3
"""
Test script to verify OpenAI API connectivity
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

def test_openai_connection():
    """Test OpenAI API connectivity with a simple GPT-4o-mini request"""
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please set OPENAI_API_KEY in your .env file")
        return False
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        print("🔄 Testing OpenAI API connectivity...")
        
        # Make a simple test request to GPT-5 mini
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {
                    "role": "user", 
                    "content": "Hello! This is a test message. Please respond with 'API connection successful!'"
                }
            ],
            max_tokens=50,
            temperature=0
        )
        
        # Extract and display response
        message = response.choices[0].message.content
        print(f"✅ Success! OpenAI API Response: {message}")
        print(f"📊 Model used: {response.model}")
        print(f"🔢 Tokens used: {response.usage.total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing OpenAI API: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting OpenAI API connectivity test...")
    print("=" * 50)
    
    success = test_openai_connection()
    
    print("=" * 50)
    if success:
        print("✅ OpenAI API test completed successfully!")
        print("Your environment is ready for AI social media content generation.")
    else:
        print("❌ OpenAI API test failed!")
        print("Please check your API key and try again.")