# 🚀 Complete Social Media API Setup Guide
## Make Your AI Social Media Agent Fully Functional

**Created by:** [Tailored Agents](https://tailoredagents.com) - AI Development Specialists  
**Last Updated:** January 28, 2025  
**Purpose:** Complete guide to connect all social media APIs for production use

---

## 📋 **Quick Overview**

This guide walks you through connecting all social media APIs to make your AI Social Media Content Agent fully functional. Follow these steps to enable posting, analytics, and automation across all supported platforms.

### **Supported Platforms:**
- 🐦 **Twitter/X** (API v2)
- 💼 **** (Company & Personal Pages)
- 📸 **Instagram** (Business Accounts)
- 👥 **Facebook** (Pages & Business)
- 🎵 **TikTok** (Business API)

---

## 🛠️ **Prerequisites**

Before starting, ensure you have:
- ✅ **Business accounts** on each platform you want to connect
- ✅ **Administrative access** to social media accounts
- ✅ **Valid email addresses** for API registrations
- ✅ **Production domain** or use `http://localhost:8000` for development
- ✅ **Environment variables** access to update `.env` file

---

## 🔧 **Environment Configuration**

First, locate and prepare your environment file:

```bash
# File: /path/to/your/project/.env
# Add the following API credentials as you obtain them
```

---

# 1. 🐦 **Twitter/X API v2 Setup**

## **Step 1: Create Twitter Developer Account**

1. **Visit Twitter Developer Portal**
   - Go to: https://developer.twitter.com/
   - Click "Sign up for free account"
   - Use your business Twitter account

2. **Apply for Developer Access**
   - Select "Making a bot" or "Building tools for Twitter users"
   - Describe your AI social media agent use case
   - Wait for approval (usually instant to 24 hours)

## **Step 2: Create New App**

1. **Create New Project & App**
   ```
   Project Name: AI Social Media Agent
   App Name: [YourCompany]-Social-Agent
   ```

2. **Configure App Settings**
   - **App permissions**: Read and Write and Direct Messages
   - **Type of App**: Web App, Automated App or Bot
   - **Callback URLs**: `http://localhost:8000/auth/twitter/callback`
   - **Website URL**: Your production domain or `http://localhost:8000`

## **Step 3: Get API Credentials**

Navigate to your app's "Keys and tokens" section:

1. **API Key & Secret** (Consumer Keys)
   ```
   API Key: [Your API Key]
   API Secret Key: [Your API Secret]
   ```

2. **Bearer Token**
   ```
   Bearer Token: [Your Bearer Token]
   ```

3. **Access Token & Secret** (OAuth 1.0a)
   ```
   Access Token: [Your Access Token]
   Access Token Secret: [Your Access Token Secret]
   ```

4. **OAuth 2.0 Client ID & Secret**
   ```
   Client ID: [Your Client ID]
   Client Secret: [Your Client Secret]
   ```

## **Step 4: Update Environment Variables**

Add to your `.env` file:

```bash
# Twitter/X API v2 Configuration
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
TWITTER_CLIENT_ID=your_client_id_here
TWITTER_CLIENT_SECRET=your_client_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here
```

---

# 2. 💼 ** API Setup**

## **Step 1: Create  Developer Account**

1. **Visit  Developers**
   - Go to: https://www..com/developers/
   - Sign in with your  business account
   - Click "Create app"

2. **Create New Application**
   ```
   App name: AI Social Media Agent
    Page: [Your Company Page]
   Privacy policy URL: [Your privacy policy]
   App logo: [Upload your logo]
   ```

## **Step 2: Configure App Permissions**

Request the following permissions:
- ✅ **r_liteprofile** - Basic profile info
- ✅ **r_emailaddress** - Email address
- ✅ **w_member_social** - Share content as member
- ✅ **r_organization_social** - Read organization content
- ✅ **w_organization_social** - Share content as organization

## **Step 3: Set Redirect URLs**

Add these redirect URLs:
```
http://localhost:8000/auth//callback
https://yourdomain.com/auth//callback
```

## **Step 4: Get API Credentials**

From your app's "Auth" tab:

```
Client ID: [Your Client ID]
Client Secret: [Your Client Secret]
```

## **Step 5: Generate Access Token**

Use 's OAuth 2.0 flow or test with their authorization URL:
```
https://www..com/oauth/v2/authorization?response_type=code&client_id=[CLIENT_ID]&redirect_uri=[REDIRECT_URI]&scope=r_liteprofile%20r_emailaddress%20w_member_social
```

## **Step 6: Update Environment Variables**

```bash
#  API Configuration
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_ACCESS_TOKEN=your_access_token_here
LINKEDIN_USER_ID=your_user_id_here
```

---

# 3. 📸 **Instagram Business API Setup**

## **Step 1: Set Up Facebook Developer Account**

Instagram Business API requires Facebook Developer access:

1. **Visit Facebook Developers**
   - Go to: https://developers.facebook.com/
   - Click "Get Started"
   - Choose "Business" as your account type

2. **Create New App**
   ```
   App Display Name: AI Social Media Agent
   App Contact Email: [Your business email]
   App Purpose: Business
   ```

## **Step 2: Add Instagram Basic Display**

1. **Add Product**
   - In your app dashboard, click "+ Add Product"
   - Select "Instagram Basic Display"
   - Click "Set Up"

2. **Add Instagram Graph API**
   - Also add "Instagram Graph API" for business features
   - This enables posting and analytics

## **Step 3: Configure Instagram Business Account**

1. **Convert to Business Account**
   - Ensure your Instagram account is a Business account
   - Connect it to a Facebook Page
   - Go to Instagram Settings → Account → Switch to Professional Account

2. **Connect Facebook Page**
   - Your Instagram business account must be connected to a Facebook Page
   - This Page will be used for API access

## **Step 4: Get Instagram Credentials**

1. **App ID & Secret**
   ```
   App ID: [From Facebook App Dashboard]
   App Secret: [From Facebook App Dashboard → Settings → Basic]
   ```

2. **Access Token**
   - Use Facebook's Graph API Explorer: https://developers.facebook.com/tools/explorer/
   - Select your app and get a User Access Token
   - Extend it to a Long-Lived Token (60 days)

3. **Instagram Business Account ID**
   - Use Graph API call: `GET /{page-id}?fields=instagram_business_account`
   - Extract the Instagram Business Account ID

## **Step 5: Update Environment Variables**

```bash
# Instagram API Configuration
INSTAGRAM_APP_ID=your_app_id_here
INSTAGRAM_APP_SECRET=your_app_secret_here
INSTAGRAM_ACCESS_TOKEN=your_long_lived_access_token_here
INSTAGRAM_BUSINESS_ID=your_instagram_business_account_id_here
```

---

# 4. 👥 **Facebook Pages API Setup**

## **Step 1: Use Same Facebook App**

Use the same Facebook app created for Instagram:

1. **Add Facebook Pages Product**
   - In your app dashboard, add "Facebook Login"
   - Add "Pages API"

## **Step 2: Configure Page Permissions**

Request these permissions:
- ✅ **pages_show_list** - Access page list
- ✅ **pages_read_engagement** - Read page insights
- ✅ **pages_manage_posts** - Create and manage posts
- ✅ **pages_read_user_content** - Read user content on page
- ✅ **publish_to_groups** - Publish to groups (if needed)

## **Step 3: Get Page Access Token**

1. **Get User Access Token**
   - Use Facebook Login flow to get user token
   - Ensure user is admin of the target page

2. **Exchange for Page Access Token**
   ```bash
   GET /{page-id}?fields=access_token&access_token={user-access-token}
   ```

3. **Get Page ID**
   ```bash
   GET /me/accounts?access_token={user-access-token}
   ```

## **Step 4: Update Environment Variables**

```bash
# Facebook Pages API Configuration
FACEBOOK_APP_ID=your_app_id_here
FACEBOOK_APP_SECRET=your_app_secret_here
FACEBOOK_ACCESS_TOKEN=your_user_access_token_here
FACEBOOK_PAGE_ID=your_page_id_here
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_access_token_here
```

---

# 5. 🎵 **TikTok Business API Setup**

## **Step 1: Apply for TikTok Developer Access**

1. **Visit TikTok Developers**
   - Go to: https://developers.tiktok.com/
   - Click "Register" and create developer account
   - Complete business verification process

2. **Create New App**
   ```
   App Name: AI Social Media Agent
   App Description: AI-powered social media management platform
   Industry: Marketing & Advertising
   ```

## **Step 2: Configure App Settings**

1. **Add Login Kit**
   - Enable TikTok Login Kit
   - Set redirect URL: `http://localhost:8000/auth/tiktok/callback`

2. **Request Permissions**
   - **user.info.basic** - Basic user info
   - **video.publish** - Publish videos
   - **video.list** - List user videos

## **Step 3: Get API Credentials**

From your app dashboard:

```
Client Key: [Your Client Key]
Client Secret: [Your Client Secret]
```

## **Step 4: OAuth Flow for Access Token**

1. **Authorization URL**
   ```
   https://www.tiktok.com/auth/authorize/?client_key=[CLIENT_KEY]&scope=user.info.basic,video.publish&response_type=code&redirect_uri=[REDIRECT_URI]
   ```

2. **Exchange Code for Token**
   ```bash
   POST https://open-api.tiktok.com/oauth/access_token/
   ```

## **Step 5: Update Environment Variables**

```bash
# TikTok API Configuration
TIKTOK_CLIENT_ID=your_client_key_here
TIKTOK_CLIENT_SECRET=your_client_secret_here
TIKTOK_ACCESS_TOKEN=your_access_token_here
```

---

# 6. 🤖 **OpenAI API Setup**

## **Step 1: Create OpenAI Account**

1. **Visit OpenAI Platform**
   - Go to: https://platform.openai.com/
   - Sign up for an account
   - Add payment method for API usage

2. **Generate API Key**
   - Go to API Keys section
   - Click "Create new secret key"
   - Copy and store securely

## **Step 2: Update Environment Variables**

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
```

---

# 🔧 **Final Configuration**

## **Complete .env File Template**

```bash
# ===========================================
# AI Social Media Content Agent - API Configuration
# ===========================================

# Application Settings
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your_super_secret_key_here
DATABASE_URL=your_database_url_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here

# Twitter/X API v2
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here
TWITTER_CLIENT_ID=your_twitter_client_id_here
TWITTER_CLIENT_SECRET=your_twitter_client_secret_here
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here

#  API
LINKEDIN_CLIENT_ID=your__client_id_here
LINKEDIN_CLIENT_SECRET=your__client_secret_here
LINKEDIN_ACCESS_TOKEN=your__access_token_here
LINKEDIN_USER_ID=your__user_id_here

# Instagram Business API
INSTAGRAM_APP_ID=your_instagram_app_id_here
INSTAGRAM_APP_SECRET=your_instagram_app_secret_here
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token_here
INSTAGRAM_BUSINESS_ID=your_instagram_business_id_here

# Facebook Pages API
FACEBOOK_APP_ID=your_facebook_app_id_here
FACEBOOK_APP_SECRET=your_facebook_app_secret_here
FACEBOOK_ACCESS_TOKEN=your_facebook_access_token_here
FACEBOOK_PAGE_ID=your_facebook_page_id_here
FACEBOOK_PAGE_ACCESS_TOKEN=your_facebook_page_access_token_here

# TikTok Business API
TIKTOK_CLIENT_ID=your_tiktok_client_id_here
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret_here
TIKTOK_ACCESS_TOKEN=your_tiktok_access_token_here

# Authentication & Security
AUTH0_DOMAIN=your_auth0_domain_here
AUTH0_CLIENT_ID=your_auth0_client_id_here
AUTH0_CLIENT_SECRET=your_auth0_client_secret_here
AUTH0_AUDIENCE=your_auth0_audience_here

# Database & Cache
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

# 🧪 **Testing Your Setup**

## **1. Test API Connections**

Run the built-in API test script:

```bash
# Start your application
cd /path/to/your/project
source venv/bin/activate
python -m uvicorn backend.main:app --reload

# Test individual APIs
curl -X GET "http://localhost:8000/api/test/twitter"
curl -X GET "http://localhost:8000/api/test/" 
curl -X GET "http://localhost:8000/api/test/instagram"
curl -X GET "http://localhost:8000/api/test/facebook"
curl -X GET "http://localhost:8000/api/test/tiktok"
```

## **2. Verify Dashboard Integration**

1. **Access Dashboard**
   - Visit: http://localhost:5173
   - Go to Settings → Social Integrations
   - Check connection status for each platform

2. **Test Posting**
   - Create a test post in the dashboard
   - Schedule for immediate posting
   - Verify it appears on the target platform

---

# 🚨 **Troubleshooting**

## **Common Issues & Solutions**

### **Twitter API Issues**
```
❌ Error: "Forbidden" or "Unauthorized"
✅ Solution: Ensure app permissions include "Read and Write"
✅ Check: Bearer token is correctly set for v2 API calls
```

### ** API Issues**
```
❌ Error: "Invalid redirect_uri"
✅ Solution: Add exact redirect URI in  app settings
✅ Check: URI matches exactly (including trailing slashes)
```

### **Instagram API Issues**
```
❌ Error: "Instagram account not found"
✅ Solution: Ensure Instagram account is Business type
✅ Check: Account is connected to a Facebook Page
```

### **Facebook API Issues**
```
❌ Error: "App not approved for production"
✅ Solution: Submit app for review if using live users
✅ Check: Add test users for development
```

### **TikTok API Issues**
```
❌ Error: "Access denied" 
✅ Solution: Ensure business verification is complete
✅ Check: App is approved for required permissions
```

## **Rate Limiting**

Each platform has different rate limits:

- **Twitter**: 300 requests per 15 minutes (varies by endpoint)
- ****: 1000 requests per day per member
- **Instagram**: 200 requests per hour
- **Facebook**: Varies by app usage level
- **TikTok**: 10,000 requests per day

## **Token Refresh**

Most tokens expire and need refresh:

- **Twitter**: OAuth tokens don't expire, but can be revoked
- ****: Access tokens expire in 60 days
- **Instagram**: Long-lived tokens expire in 60 days
- **Facebook**: Same as Instagram
- **TikTok**: Access tokens expire in 24 hours

---

# 📞 **Support & Resources**

## **Official Documentation**
- 🐦 [Twitter API v2 Docs](https://developer.twitter.com/en/docs/twitter-api)
- 💼 [ API Docs](https://docs.microsoft.com/en-us//)
- 📸 [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)
- 👥 [Facebook Graph API](https://developers.facebook.com/docs/graph-api)
- 🎵 [TikTok API Docs](https://developers.tiktok.com/doc)
- 🤖 [OpenAI API Docs](https://platform.openai.com/docs)

## **Testing Tools**
- **Postman Collections**: Available for each API
- **Graph API Explorer**: For Facebook/Instagram testing
- **Twitter API Tester**: Built-in developer tools
- ** API Console**: Test endpoints directly

## **Need Help?**

If you encounter issues not covered in this guide:

1. **Check API Status Pages** for platform outages
2. **Review Rate Limiting** in your API dashboard
3. **Verify Permissions** are correctly configured
4. **Test with Postman** to isolate issues
5. **Contact Platform Support** for platform-specific issues

---

**🎉 Congratulations!** Your AI Social Media Content Agent is now fully connected and ready for production use across all major social platforms!

---

*Created with ❤️ by [Tailored Agents](https://tailoredagents.com) - Custom AI Solutions for Businesses*