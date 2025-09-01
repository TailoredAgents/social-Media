#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate secure secrets for production deployment
Run this script to generate secure keys for your environment variables
"""
import secrets
import string

def generate_secure_key(length=32):
    """Generate a secure random key of specified length"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_secret(length=64):
    """Generate a secure JWT secret"""
    return secrets.token_urlsafe(length)

def main():
    print("Generating Secure Production Secrets")
    print("=" * 50)
    print()
    
    # Generate all required secrets
    secrets_config = {
        "SECRET_KEY": generate_secure_key(32),
        "JWT_SECRET": generate_jwt_secret(64), 
        "ADMIN_JWT_SECRET": generate_jwt_secret(64),
    }
    
    print("Copy these to your Render Environment Variables:")
    print()
    
    for key, value in secrets_config.items():
        print(f"{key}={value}")
    
    print()
    print("IMPORTANT SECURITY NOTES:")
    print("1. Never commit these secrets to your repository")
    print("2. Store them securely in Render's environment variables")
    print("3. Use different secrets for each environment (dev/staging/prod)")
    print("4. These secrets are shown only once - save them now!")
    print()
    print("Database URL will be provided automatically by Render when you")
    print("   connect your PostgreSQL database to your web service.")
    print()
    
    # Generate a sample .env file for reference
    env_template = f"""# Production Environment Variables for Render
# DO NOT COMMIT THIS FILE TO VERSION CONTROL

# Application Environment
ENVIRONMENT=production
DEBUG=false

# Security & Authentication
SECRET_KEY={secrets_config["SECRET_KEY"]}
JWT_SECRET={secrets_config["JWT_SECRET"]}
JWT_ALGORITHM=HS256
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=1209600

# Admin System
ADMIN_JWT_SECRET={secrets_config["ADMIN_JWT_SECRET"]}
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database (will be set automatically by Render)
# DATABASE_URL=postgresql://username:password@hostname:port/database_name

# CORS & Security (update with your actual domain)
ALLOWED_HOSTS=www.lily-ai-socialmedia.com,lily-ai-socialmedia.com
CORS_ORIGINS=https://www.lily-ai-socialmedia.com,https://lily-ai-socialmedia.com

# AI Services (add your actual API keys)
OPENAI_API_KEY=your_actual_openai_api_key_here
SERPER_API_KEY=your_actual_serper_api_key_here

# Feature Flags
DEMO_MODE=false
MOCK_SOCIAL_APIS=false
SHOW_SAMPLE_DATA=false
ENABLE_REGISTRATION=true
REQUIRE_EMAIL_VERIFICATION=false
FEATURE_FLAGS=USE_STUB_INTEGRATIONS=0,WORKFLOW_V2=1,ENABLE_DEEP_RESEARCH=1

# Social Media APIs (optional - add as needed)
# TWITTER_API_KEY=your_twitter_api_key
# TWITTER_API_SECRET=your_twitter_api_secret
# LINKEDIN_CLIENT_ID=your_linkedin_client_id
# LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
"""
    
    # Write to a reference file (don't commit this!)
    with open("production_env_reference.txt", "w") as f:
        f.write(env_template)
    
    print(f"Reference file created: production_env_reference.txt")
    print("   (This file is git-ignored for security)")

if __name__ == "__main__":
    main()