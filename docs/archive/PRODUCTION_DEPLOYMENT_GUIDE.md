# Lily AI - Complete Production Deployment Guide

## 🚀 Final Step-by-Step Production Setup

This guide provides the complete, finalized instructions for deploying Lily AI to production with Render and Cloudflare.

## Prerequisites

- ✅ GitHub repository with your code
- ✅ Domain name purchased (e.g., `lily-ai-socialmedia.com`)
- ✅ Cloudflare account (free plan is sufficient)
- ✅ Render account

---

# Part 1: Backend Deployment on Render

## Step 1: Create PostgreSQL Database

1. **Login to Render Dashboard**: https://dashboard.render.com
2. **Create Database**:
   - Click "New +" → "PostgreSQL"
   - **Name**: `lily-ai-production-db`
   - **Database**: `lily_ai_production`
   - **User**: `lily_ai_user`
   - **Region**: Choose closest to your users
   - **Plan**: Select based on your needs (Starter for small scale)
3. **Save Database Connection String** - You'll need this for the backend service

## Step 2: Create Backend Web Service

1. **Create Web Service**:
   - Click "New +" → "Web Service"
   - **Connect Repository**: Link your GitHub repository
   - **Name**: `lily-ai-backend`
   - **Region**: Same as database
   - **Branch**: `main` (or your production branch)
   - **Runtime**: `Python 3`
   
2. **Build Settings**:
   ```bash
   # Build Command:
   pip install -r requirements.txt && python -m alembic upgrade head
   
   # Start Command:
   uvicorn app:app --host 0.0.0.0 --port $PORT
   ```

## Step 3: Configure Backend Environment Variables

Add these environment variables in your Render backend service:

```bash
# Database Configuration
DATABASE_URL=postgresql://lily_ai_user:PASSWORD@HOST:PORT/lily_ai_production

# Basic Configuration
ENVIRONMENT=production
SECRET_KEY=your_generated_secret_key_here
API_DOMAIN=api.lily-ai-socialmedia.com
FRONTEND_URL=https://lily-ai-socialmedia.com

# CORS Configuration
ALLOWED_ORIGINS=https://lily-ai-socialmedia.com,https://www.lily-ai-socialmedia.com

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin Configuration
ADMIN_SECRET_KEY=your_admin_secret_key_here
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Optional: Social Media API Keys for Development
TWITTER_API_KEY=dev_key_only
TWITTER_API_SECRET=dev_secret_only
LINKEDIN_CLIENT_ID=dev_client_id
LINKEDIN_CLIENT_SECRET=dev_client_secret
```

**🔐 Generate Secure Keys**:
Run this script to generate production secrets:
```bash
python3 scripts/generate_secrets.py
```

---

# Part 2: Frontend Deployment on Render

## Step 1: Create Static Site Service

1. **Create Static Site**:
   - Click "New +" → "Static Site"
   - **Connect Repository**: Same GitHub repository
   - **Name**: `lily-ai-frontend`
   - **Branch**: `main`
   
2. **Build Settings**:
   ```bash
   # Build Command:
   npm ci && npm run build
   
   # Publish Directory:
   dist
   
   # Node Version:
   18
   ```

## Step 2: Configure Frontend Environment Variables

Add these environment variables in your Render static site:

```bash
# API Configuration
VITE_API_BASE_URL=https://api.lily-ai-socialmedia.com

# App Configuration
VITE_APP_TITLE=Lily AI Social Media
VITE_ENVIRONMENT=production

# Optional: Analytics/Monitoring
VITE_SENTRY_DSN=your_sentry_dsn_here
VITE_GOOGLE_ANALYTICS_ID=your_ga_id_here
```

---

# Part 3: Cloudflare Setup (Complete Guide)

## Step 1: Add Domain to Cloudflare

1. **Login to Cloudflare**: https://dash.cloudflare.com
2. **Add Site**: 
   - Click "+ Add site"
   - Enter your domain: `lily-ai-socialmedia.com`
   - Select "Free" plan
3. **Update Nameservers**:
   - Copy the 2 nameservers provided by Cloudflare
   - Go to your domain registrar
   - Replace existing nameservers with Cloudflare's nameservers
   - Wait 24-48 hours for propagation

## Step 2: Configure DNS Records

In Cloudflare DNS section, add these records:

### Backend API Record
```
Type: A
Name: api
Content: [Your Render Backend IP Address]
TTL: Auto
Proxy Status: ✅ Proxied (orange cloud)
```

**To get Render Backend IP**:
1. Go to your backend service in Render
2. Settings → Custom Domains → Add `api.lily-ai-socialmedia.com`
3. Render will provide the IP address to use

### Frontend Records
```
Type: CNAME
Name: www
Content: lily-ai-frontend.onrender.com
TTL: Auto
Proxy Status: ✅ Proxied (orange cloud)
```

```
Type: CNAME  
Name: @ (root domain)
Content: lily-ai-frontend.onrender.com
TTL: Auto
Proxy Status: ✅ Proxied (orange cloud)
```

## Step 3: SSL/TLS Configuration

1. **Go to SSL/TLS tab** in Cloudflare
2. **Overview**:
   - Set **Encryption Mode**: Full (strict)
   - Enable **Always Use HTTPS**
3. **Edge Certificates**:
   - ✅ **Always Use HTTPS**: ON
   - ✅ **HTTP Strict Transport Security (HSTS)**:
     - Enable HSTS
     - Max Age: 6 months
     - Include subdomains: ✅
     - Preload: ✅

## Step 4: Performance & Security Configuration

### Page Rules (Rules → Page Rules)

**Rule 1: API Cache Bypass**
```
URL: api.lily-ai-socialmedia.com/*
Settings:
- Cache Level: Bypass
- SSL: Full (strict)
- Security Level: Medium
```

**Rule 2: Website Performance**
```
URL: *.lily-ai-socialmedia.com/*
Settings:
- Always Use HTTPS: On
- Browser Cache TTL: 4 hours
- SSL: Full (strict)
```

### Security Headers (Security → Response Headers)
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
X-XSS-Protection: 1; mode=block
```

### Speed Optimization (Speed → Optimization)
- ✅ **Auto Minify**: CSS, HTML, JavaScript
- ✅ **Brotli Compression**
- ✅ **Early Hints**
- ❌ **Rocket Loader**: OFF (can break React)

---

# Part 4: Custom Domains in Render

## Backend Custom Domain
1. **Go to Backend Service** in Render
2. **Settings → Custom Domains**
3. **Add Domain**: `api.lily-ai-socialmedia.com`
4. **Wait for SSL** certificate provisioning

## Frontend Custom Domain  
1. **Go to Frontend Service** in Render
2. **Settings → Custom Domains**
3. **Add Domains**:
   - `lily-ai-socialmedia.com`
   - `www.lily-ai-socialmedia.com`
4. **Wait for SSL** certificate provisioning

---

# Part 5: Database Setup & Admin Creation

## Step 1: Run Database Migrations

After backend deployment:
1. **Go to Render Backend Service**
2. **Environment → Shell**
3. **Run**:
   ```bash
   python -m alembic upgrade head
   ```

## Step 2: Create Super Admin User

1. **In Render Shell**:
   ```bash
   python scripts/create_super_admin.py
   ```
   
2. **Follow prompts**:
   - Enter admin email (your email)
   - Enter admin username
   - Enter secure password
   - Confirm details

## Step 3: Create Registration Keys

1. **In Render Shell**:
   ```bash
   python scripts/create_registration_keys.py
   ```
   
2. **Configure keys**:
   - Description: "Production launch keys"
   - Max uses: 10 per key
   - Number of keys: 3-5
   - Expiry: 90 days
   - Save keys to file for distribution

---

# Part 6: Testing & Verification

## DNS & SSL Testing

**Check DNS Propagation**:
```bash
dig lily-ai-socialmedia.com
dig api.lily-ai-socialmedia.com
dig www.lily-ai-socialmedia.com
```

**Test SSL Certificates**:
- Visit: https://lily-ai-socialmedia.com ✅
- Visit: https://www.lily-ai-socialmedia.com ✅
- Visit: https://api.lily-ai-socialmedia.com/docs ✅

## Functionality Testing

**Test Registration**:
1. Visit your website
2. Try to register with a registration key
3. Confirm user creation works

**Test API**:
1. Login with admin credentials
2. Access admin endpoints
3. Create additional registration keys via API

**Test Social Media Credentials**:
1. Login as a regular user
2. Add social media credentials
3. Verify encryption and storage

## Performance Testing

- **PageSpeed Insights**: https://pagespeed.web.dev/
- **Security Headers**: https://securityheaders.com/
- **SSL Labs**: https://www.ssllabs.com/ssltest/

---

# Summary: Final Environment Variables

## Backend Environment Variables (Render Web Service)

```bash
# Core Configuration
ENVIRONMENT=production
SECRET_KEY=[generated-secret-key]
DATABASE_URL=postgresql://lily_ai_user:[password]@[host]:5432/lily_ai_production

# API Configuration  
API_DOMAIN=api.lily-ai-socialmedia.com
FRONTEND_URL=https://lily-ai-socialmedia.com
ALLOWED_ORIGINS=https://lily-ai-socialmedia.com,https://www.lily-ai-socialmedia.com

# Authentication
JWT_SECRET_KEY=[generated-jwt-key]
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin System
ADMIN_SECRET_KEY=[generated-admin-key]
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=[your-email]
SMTP_PASSWORD=[app-password]
```

## Frontend Environment Variables (Render Static Site)

```bash
# API Configuration
VITE_API_BASE_URL=https://api.lily-ai-socialmedia.com

# App Configuration
VITE_APP_TITLE=Lily AI Social Media
VITE_ENVIRONMENT=production

# Optional: Monitoring
VITE_SENTRY_DSN=[sentry-dsn]
VITE_GOOGLE_ANALYTICS_ID=[ga-id]
```

---

# 🎉 Production Deployment Complete!

Your Lily AI platform is now live at:
- **Website**: https://lily-ai-socialmedia.com
- **API**: https://api.lily-ai-socialmedia.com
- **Admin**: https://api.lily-ai-socialmedia.com/docs (with admin credentials)

## Next Steps

1. **Distribute registration keys** to initial users
2. **Monitor performance** via Render dashboards
3. **Set up monitoring** (Sentry, Google Analytics)
4. **Configure backups** for database
5. **Plan scaling** as user base grows

## Support

- **Render Documentation**: https://render.com/docs
- **Cloudflare Documentation**: https://developers.cloudflare.com/
- **Project Issues**: [Your GitHub repository]/issues