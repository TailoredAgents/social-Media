# Lily AI Social Media Agent - Render & Cloudflare Deployment Guide (2025)

This comprehensive guide covers deploying the Lily AI Social Media Content Agent using Render for backend hosting and Cloudflare for frontend DNS and CDN services, based on the latest 2025 best practices.

## Overview

- **Backend**: FastAPI deployed on Render with PostgreSQL database
- **Frontend**: React app deployed on Render with custom domain via Cloudflare
- **Database**: PostgreSQL hosted on Render
- **DNS/CDN**: Cloudflare for domain management and performance

## Prerequisites

- GitHub repository with your Lily AI Social Media Agent code
- Render account (free tier available)
- Cloudflare account (free tier available) 
- Custom domain (optional but recommended for production)

## Part 1: Backend Deployment on Render

### 1. Prepare Your FastAPI Application

Ensure your project has the following files:

**requirements.txt**
```txt
fastapi>=0.95.0
uvicorn>=0.21.0
sqlalchemy>=2.0.0
alembic>=1.8.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-multipart>=0.0.6
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
```

**render.yaml** (Optional - for Infrastructure as Code)
```yaml
services:
  - type: web
    name: lily-ai-backend
    env: python
    plan: starter
    buildCommand: pip install -r requirements.txt && alembic upgrade head
    startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: lily-ai-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: JWT_SECRET
        generateValue: true
      - key: ALLOWED_ORIGINS
        value: https://lily-ai-socialmedia.com,https://www.lily-ai-socialmedia.com

databases:
  - name: lily-ai-db
    plan: starter
    databaseName: lily_ai_db
    user: lily_ai_user
```

### 2. Environment Variables Configuration

Configure the following environment variables in Render:

**Required Environment Variables:**
```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@hostname:port/database_name
POSTGRES_SERVER=hostname
POSTGRES_PORT=5432
POSTGRES_DB=lily_ai_db
POSTGRES_USER=lily_ai_user
POSTGRES_PASSWORD=your_secure_password

# Application Security
SECRET_KEY=your_super_secret_key_here
JWT_SECRET=your_jwt_secret_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=production
DEBUG=false

# CORS Configuration
ALLOWED_ORIGINS=https://lily-ai-socialmedia.com,https://www.lily-ai-socialmedia.com

# Admin System
ADMIN_JWT_SECRET=your_admin_jwt_secret_here
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Social Media API Keys (if applicable)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
LINKEDIN_CLIENT_ID=your__client_id
LINKEDIN_CLIENT_SECRET=your__client_secret

# Email Configuration (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 3. Deploy Backend to Render

1. **Create Web Service**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: `lily-ai-backend`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
     - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
     - **Plan**: Choose based on your needs (Starter for production)

2. **Create PostgreSQL Database**:
   - Click "New +" → "PostgreSQL"
   - **Name**: `lily-ai-db`
   - **Database Name**: `lily_ai_db`
   - **User**: `lily_ai_user`
   - **Plan**: Choose based on your needs

3. **Configure Environment Variables**:
   - In your web service settings, add all the environment variables listed above
   - For `DATABASE_URL`, use the connection string from your PostgreSQL service

### 4. Database Setup

**Create Super Admin User**:
After deployment, run the admin creation script:
```bash
# SSH into your Render service or use the console
python scripts/create_super_admin.py
```

**Create Initial Registration Keys**:
Use the admin API to create registration keys for new users:
```bash
curl -X POST "https://your-app.onrender.com/api/admin/registration-keys" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Initial registration keys",
    "max_uses": 10,
    "expires_at": "2025-12-31T23:59:59"
  }'
```

## Part 2: Frontend Deployment

### 1. Prepare React Application

**Environment Variables for Frontend (.env.production)**:
```bash
VITE_API_BASE_URL=https://your-backend.onrender.com
VITE_APP_TITLE=Lily AI Social Media
VITE_ENVIRONMENT=production
```

**Build Configuration (vite.config.js)**:
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['@heroicons/react', 'framer-motion']
        }
      }
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

### 2. Deploy Frontend to Render

1. **Create Static Site**:
   - Go to Render Dashboard
   - Click "New +" → "Static Site"
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: `lily-ai-frontend`
     - **Build Command**: `npm run build`
     - **Publish Directory**: `dist`

2. **Configure Build Settings**:
   - **Node Version**: `18` or `20`
   - **Build Command**: `npm ci && npm run build`
   - **Publish Directory**: `dist`

## Part 3: Cloudflare Domain Configuration

### 1. Add Domain to Cloudflare

1. **Sign up/Login** to [Cloudflare](https://dash.cloudflare.com)
2. **Add Site** - Enter your domain (e.g., `lily-ai-socialmedia.com`)
3. **Choose Plan** - Free plan is sufficient for most use cases
4. **Update Nameservers** at your domain registrar to Cloudflare's nameservers

### 2. DNS Configuration

**A Records (for backend API):**
```
Type: A
Name: api
Content: [Your Render backend IP - get from Render dashboard]
TTL: Auto
Proxy Status: Proxied
```

**CNAME Records (for frontend):**
```
Type: CNAME
Name: www
Content: your-frontend.onrender.com
TTL: Auto
Proxy Status: Proxied

Type: CNAME
Name: @
Content: your-frontend.onrender.com
TTL: Auto
Proxy Status: Proxied
```

### 3. SSL/TLS Configuration

1. Go to **SSL/TLS** → **Overview**
2. Set encryption mode to **Full (strict)**
3. Enable **Always Use HTTPS**
4. Configure **HSTS** for enhanced security

### 4. Page Rules for Performance

Create page rules to optimize performance:

```
URL: www.lily-ai-socialmedia.com/api/*
Settings:
- SSL: Full (strict)
- Cache Level: Bypass

URL: *.lily-ai-socialmedia.com/*
Settings:
- SSL: Full (strict)
- Always Use HTTPS: On
- Browser Cache TTL: 4 hours
```

## Part 4: Custom Domain Setup on Render

### 1. Configure Custom Domain for Frontend

1. Go to your **Static Site** in Render
2. Click **Settings** → **Custom Domains**
3. Add your domains:
   - `lily-ai-socialmedia.com`
   - `www.lily-ai-socialmedia.com`

### 2. Configure Custom Domain for Backend

1. Go to your **Web Service** in Render
2. Click **Settings** → **Custom Domains**
3. Add your API subdomain:
   - `api.lily-ai-socialmedia.com`

## Part 5: Production Configuration

### 1. Security Headers

Configure security headers in Cloudflare:

**Security → Response Headers:**
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

### 2. Performance Optimization

**Speed → Optimization:**
- Enable **Auto Minify** for CSS, HTML, JS
- Enable **Brotli** compression
- Enable **Rocket Loader** (optional)

**Caching → Configuration:**
- Set **Browser Cache TTL** to 4 hours
- Enable **Development Mode** when making changes

### 3. Environment-Specific Configurations

**Backend CORS Configuration (app.py):**
```python
from fastapi.middleware.cors import CORSMiddleware

# Update CORS origins for production
if environment == "production":
    allowed_origins = [
        "https://lily-ai-socialmedia.com",
        "https://www.lily-ai-socialmedia.com",
        "https://api.lily-ai-socialmedia.com"
    ]
else:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Part 6: Monitoring and Maintenance

### 1. Render Monitoring

- Monitor service health in Render dashboard
- Set up log monitoring and alerts
- Monitor database performance and usage

### 2. Cloudflare Analytics

- Monitor traffic patterns and performance
- Set up security alerts for potential threats
- Monitor cache hit ratios and optimization opportunities

### 3. Database Backups

- Configure automated backups in Render
- Consider upgrading to paid PostgreSQL plan for production
- Set up monitoring for database connections and performance

## Troubleshooting Common Issues

### 1. CORS Errors
- Verify ALLOWED_ORIGINS environment variable includes all your domains
- Check that Cloudflare proxy settings don't interfere with CORS headers

### 2. Database Connection Issues
- Verify DATABASE_URL is correctly formatted
- Check PostgreSQL service status in Render
- Ensure database migrations have run successfully

### 3. SSL Certificate Issues
- Verify Cloudflare SSL mode is set to "Full (strict)"
- Check that Render services have SSL enabled
- Wait for DNS propagation (can take up to 48 hours)

### 4. Build Failures
- Check build logs in Render dashboard
- Verify all dependencies are listed in requirements.txt/package.json
- Ensure environment variables are properly set

## Cost Considerations

### Free Tier Limitations

**Render Free Tier:**
- 750 hours/month compute time
- PostgreSQL databases expire after 90 days
- Services sleep after 15 minutes of inactivity
- 100GB bandwidth/month

**Cloudflare Free Tier:**
- Unlimited bandwidth
- Basic DDoS protection
- SSL certificates
- 3 Page Rules

### Recommended Upgrades for Production

**Render:**
- Starter plan ($7/month) for web services
- Standard PostgreSQL ($15/month) for persistent database

**Cloudflare:**
- Pro plan ($20/month) for enhanced performance and security
- Additional Page Rules as needed

## Conclusion

This setup provides a robust, scalable deployment for the Lily AI Social Media Agent using modern cloud infrastructure. The combination of Render's ease of deployment and Cloudflare's performance optimization creates an excellent foundation for a production social media management platform.

Key benefits of this architecture:
- **Scalability**: Both Render and Cloudflare scale automatically
- **Performance**: Cloudflare CDN ensures fast global access
- **Security**: Multiple layers of security including SSL, CORS, and admin controls
- **Cost-Effective**: Can start with free tiers and scale as needed
- **Reliability**: Both platforms offer high uptime guarantees

Remember to regularly monitor your deployment, keep dependencies updated, and scale resources as your user base grows.