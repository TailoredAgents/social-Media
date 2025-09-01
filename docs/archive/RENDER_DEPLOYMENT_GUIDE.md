# 🚀 Complete Render Deployment Guide
## Deploy Your AI Social Media Content Agent in 5 Minutes

**Created by:** [Tailored Agents](https://tailoredagents.com) - AI Development Specialists  
**Last Updated:** January 28, 2025  
**Purpose:** Simple, step-by-step deployment guide for Render

---

## 📋 **Quick Overview**

This guide will help you deploy your AI Social Media Content Agent to Render with:
- ✅ **Automated deployment** via Blueprint
- ✅ **PostgreSQL database** with migrations
- ✅ **Redis cache** for performance
- ✅ **Environment variables** setup
- ✅ **Health checks** and monitoring
- ✅ **Custom domains** support

**Total Deployment Time:** ~5-10 minutes

---

## 🛠️ **Prerequisites**

Before starting, ensure you have:
- ✅ **Render account** (free tier available)
- ✅ **GitHub repository** with your project
- ✅ **API keys** ready (OpenAI, social media platforms)
- ✅ **Domain name** (optional, for custom URLs)

---

## 🚀 **Method 1: One-Click Blueprint Deployment (Recommended)**

### **Step 1: Fork & Prepare Repository**

1. **Fork the repository** to your GitHub account
2. **Clone to your local machine**:
   ```bash
   git clone https://github.com/yourusername/ai-social-media-agent.git
   cd ai-social-media-agent
   ```

3. **Verify deployment files** are present:
   ```bash
   ls -la render.yaml build.sh backend/requirements.txt
   ```

### **Step 2: Deploy with Blueprint**

1. **Visit Render Dashboard**: https://dashboard.render.com/
2. **Click "New"** → **"Blueprint"**
3. **Connect GitHub** and select your repository
4. **Name your blueprint**: `ai-social-agent`
5. **Click "Apply"** - Render will automatically:
   - Create PostgreSQL database
   - Set up Redis instance
   - Deploy backend API
   - Deploy frontend React app
   - Configure environment variables

### **Step 3: Configure Environment Variables**

After deployment, add your API keys in the Render dashboard:

**Backend Service Environment Variables:**
```bash
# Required for basic functionality
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=automatically_generated_by_render

# Social Media APIs (add as needed)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret

LINKEDIN_CLIENT_ID=your__client_id
LINKEDIN_CLIENT_SECRET=your__client_secret

INSTAGRAM_APP_ID=your_instagram_app_id
INSTAGRAM_APP_SECRET=your_instagram_app_secret

# Optional: Additional services
SERPER_API_KEY=your_serper_api_key_for_search
```

### **Step 4: Verify Deployment**

1. **Check service status** in Render dashboard
2. **Visit your backend URL**: `https://your-app-name-backend.onrender.com/docs`
3. **Visit your frontend URL**: `https://your-app-name-frontend.onrender.com`
4. **Test health endpoint**: `https://your-app-name-backend.onrender.com/api/v1/health`

---

## 🔧 **Method 2: Manual Service Creation**

If you prefer manual setup:

### **Backend API Service**

1. **New Web Service**
   - **Environment**: Python
   - **Build Command**: 
     ```bash
     cd backend && pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
     ```

2. **Environment Variables**:
   ```bash
   ENVIRONMENT=production
   DEBUG=false
   DATABASE_URL=${postgresql_connection_string}
   REDIS_URL=${redis_connection_string}
   OPENAI_API_KEY=your_key_here
   ```

### **Frontend React Service**

1. **New Static Site**
   - **Environment**: Node
   - **Build Command**: 
     ```bash
     cd frontend && npm ci && npm run build
     ```
   - **Publish Directory**: `frontend/dist`

2. **Environment Variables**:
   ```bash
   VITE_API_URL=https://your-backend.onrender.com
   VITE_ENVIRONMENT=production
   ```

### **Database & Redis**

1. **PostgreSQL Database**:
   - **Name**: `ai-social-db`
   - **Plan**: Starter (free)

2. **Redis Instance**:
   - **Name**: `ai-social-redis`
   - **Plan**: Starter (free)

---

## ⚙️ **Advanced Configuration**

### **Custom Domains**

1. **Add custom domain** in Render dashboard
2. **Update CORS origins** in environment variables:
   ```bash
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

### **Database Migrations**

If you have database migrations:
```bash
# Add to build command
cd backend && alembic upgrade head
```

### **Scaling & Performance**

1. **Upgrade plans** for better performance:
   - **Backend**: Starter → Standard
   - **Database**: Starter → Standard
   - **Redis**: Starter → Standard

2. **Auto-scaling** configuration:
   ```yaml
   # In render.yaml
   autoDeploy: true
   scaling:
     minInstances: 1
     maxInstances: 3
   ```

---

## 🔍 **Monitoring & Health Checks**

### **Built-in Health Endpoints**

Your deployment includes comprehensive health checks:

- **`/api/v1/health`** - Complete system health
- **`/api/v1/ready`** - Kubernetes readiness probe
- **`/api/v1/live`** - Kubernetes liveness probe
- **`/api/v1/metrics`** - Prometheus metrics

### **Render Monitoring**

1. **Service Metrics**: CPU, Memory, Response times
2. **Log Streaming**: Real-time application logs
3. **Alerts**: Set up notifications for downtime
4. **Uptime Monitoring**: Built-in uptime tracking

### **Custom Monitoring**

Connect external monitoring:
```bash
# Add to environment variables
SENTRY_DSN=your_sentry_dsn_for_error_tracking
DATADOG_API_KEY=your_datadog_key_for_metrics
```

---

## 🚨 **Troubleshooting**

### **Common Issues & Solutions**

#### **Build Failures**
```bash
❌ Error: "Module not found"
✅ Solution: Check requirements.txt and package.json dependencies
✅ Command: Add missing dependencies and redeploy
```

#### **Database Connection Issues**
```bash
❌ Error: "Connection refused"
✅ Solution: Ensure DATABASE_URL is set correctly
✅ Check: Database service is running and accessible
```

#### **Environment Variable Issues**
```bash
❌ Error: "OpenAI API key not found"
✅ Solution: Add OPENAI_API_KEY in service environment variables
✅ Restart: Redeploy service after adding variables
```

#### **CORS Issues**
```bash
❌ Error: "CORS policy blocked"
✅ Solution: Update CORS_ORIGINS environment variable
✅ Include: Both frontend URLs (with/without www)
```

### **Performance Issues**

1. **Slow Response Times**:
   - Upgrade service plan
   - Enable Redis caching
   - Optimize database queries

2. **Memory Usage**:
   - Monitor via Render dashboard
   - Upgrade to higher memory plan
   - Optimize Python memory usage

### **Debug Commands**

Access service logs:
```bash
# Via Render Dashboard
# Go to Service → Logs → View real-time logs

# Check specific endpoints
curl https://your-app.onrender.com/api/v1/health
curl https://your-app.onrender.com/api/v1/ready
```

---

## 📊 **Cost Optimization**

### **Free Tier Usage**

Render's free tier includes:
- ✅ **750 hours/month** of service time
- ✅ **PostgreSQL database** (90 days)
- ✅ **Static site hosting**
- ✅ **Custom domains**

### **Paid Plans Benefits**

**Starter Plan ($7/month per service):**
- No sleep mode (always available)
- Faster builds and deployments
- Priority support
- Enhanced monitoring

**Professional Plan ($25/month per service):**
- Auto-scaling
- Advanced health checks
- Team collaboration
- Priority builds

### **Cost-Saving Tips**

1. **Use free database** for development/testing
2. **Combine services** where possible
3. **Monitor usage** via dashboard
4. **Scale down** non-production environments

---

## 🔐 **Security Best Practices**

### **Environment Variables**

- ✅ **Never commit secrets** to repository
- ✅ **Use Render's secret management**
- ✅ **Rotate API keys** regularly
- ✅ **Use different keys** for staging/production

### **HTTPS & Domains**

- ✅ **Always use HTTPS** (automatic on Render)
- ✅ **Configure CORS** properly
- ✅ **Set secure headers** (already configured)
- ✅ **Use custom domains** for production

### **Database Security**

- ✅ **Use connection pooling**
- ✅ **Enable SSL** for database connections
- ✅ **Regular backups** (automatic on Render)
- ✅ **Monitor access** logs

---

## 🆕 **Continuous Deployment**

### **Auto-Deploy Setup**

1. **Enable auto-deploy** in Render dashboard
2. **Connect GitHub branch** (usually `main` or `master`)
3. **Every push** triggers automatic deployment
4. **Build status** shown in GitHub commits

### **Branch Strategies**

**Recommended setup:**
- **`main`** → Production deployment
- **`staging`** → Staging environment
- **`develop`** → Development environment

### **CI/CD Integration**

Add GitHub Actions for additional checks:
```yaml
# .github/workflows/deploy.yml
name: Deploy to Render
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          cd backend && python -m pytest
          cd frontend && npm test
```

---

## 📞 **Support & Resources**

### **Official Documentation**
- 🔗 [Render Docs](https://render.com/docs)
- 🔗 [FastAPI Deployment](https://render.com/docs/deploy-fastapi)
- 🔗 [React Deployment](https://render.com/docs/deploy-create-react-app)
- 🔗 [Database Guide](https://render.com/docs/databases)

### **Community Support**
- 💬 [Render Community](https://community.render.com/)
- 📧 [Support Email](mailto:support@render.com)
- 📋 [Status Page](https://status.render.com/)

### **AI Social Media Agent Support**
- 📧 **Email**: support@tailoredagents.com
- 🌐 **Website**: https://tailoredagents.com
- 📚 **Documentation**: See SOCIAL_MEDIA_API_SETUP_GUIDE.md

---

## ✅ **Deployment Checklist**

### **Pre-Deployment**
- [ ] Repository forked and cloned
- [ ] API keys collected and ready
- [ ] Domain name configured (if using)
- [ ] Render account created

### **During Deployment**
- [ ] Blueprint applied successfully
- [ ] All services deployed (backend, frontend, database, redis)
- [ ] Environment variables configured
- [ ] Health checks passing

### **Post-Deployment**
- [ ] Frontend accessible and working
- [ ] Backend API responding (check `/docs`)
- [ ] Database connected and tables created
- [ ] Social media APIs connected
- [ ] Monitoring and alerts configured
- [ ] Custom domain configured (if applicable)

### **Production Ready**
- [ ] All API integrations tested
- [ ] Performance monitoring active
- [ ] Backup strategy confirmed
- [ ] Security settings reviewed
- [ ] Team access configured

---

**🎉 Congratulations!** Your AI Social Media Content Agent is now live on Render and ready to help you dominate social media with AI-powered content creation!

---

*Deployment made simple by [Tailored Agents](https://tailoredagents.com) - Custom AI Solutions for Businesses*