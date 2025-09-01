# Render Deployment Troubleshooting Guide

## 🚨 **Fixed Critical Issues**

### **Issue #1: Server Crashes on Startup**
**Problem**: `python app.py` doesn't start a web server
**Solution**: ✅ **FIXED** - Now uses `uvicorn app:app --host 0.0.0.0 --port $PORT`

### **Issue #2: 404 Errors for All Endpoints** 
**Problem**: Server not properly binding to Render's port
**Solution**: ✅ **FIXED** - Proper uvicorn configuration with `$PORT` variable

### **Issue #3: Frontend Can't Connect to Backend**
**Problem**: Wrong API URL in frontend config  
**Solution**: ✅ **FIXED** - Using existing service `ai-social-backend.onrender.com`

### **Issue #4: Missing Dependencies Crash**
**Problem**: Optional dependencies like CrewAI causing import errors
**Solution**: ✅ **FIXED** - Graceful degradation with production config

## 🔧 **Deployment Steps**

### **1. Push Latest Changes**
```bash
git add .
git commit -m "fix: Render deployment configuration and stability"
git push origin master
```

### **2. Redeploy on Render**
1. Go to your Render dashboard
2. Find "ai-social-backend" service  
3. Click "Manual Deploy" or wait for auto-deploy
4. Monitor build logs for errors

### **3. Verify Deployment**
```bash
# Test locally first
python verify_deployment.py

# Test Render deployment
python verify_deployment.py --render
```

### **4. Check Health Endpoints**
- **Health Check**: https://ai-social-backend.onrender.com/render-health
- **API Status**: https://ai-social-backend.onrender.com/health  
- **Documentation**: https://ai-social-backend.onrender.com/docs

## 📊 **Diagnostic Endpoints**

### **Enhanced Health Check**
**URL**: `/render-health`
```json
{
  "status": "healthy",
  "mode": "production", 
  "version": "2.0.0",
  "python_version": "3.11.9",
  "available_routes": 45
}
```

### **Feature Status**
**URL**: `/health`  
Shows which features are available vs disabled due to missing dependencies.

### **API Documentation**
**URL**: `/docs`  
Interactive Swagger UI for testing all endpoints.

## 🔍 **Common Issues & Solutions**

### **Build Fails**
**Symptoms**: Build logs show pip install errors
**Solutions**:
1. Check `requirements.txt` has all dependencies
2. Verify Python version compatibility
3. Check for conflicting package versions

### **Server Won't Start**
**Symptoms**: Build succeeds but health check fails
**Solutions**:
1. Check logs for import errors
2. Verify environment variables are set
3. Test with verification script

### **404 Errors**
**Symptoms**: All API calls return 404
**Solutions**:
1. Verify server is running on correct port
2. Check CORS configuration
3. Ensure frontend uses correct backend URL

### **Image Generation Fails**
**Symptoms**: `/api/content/generate-image` returns errors
**Solutions**:
1. Verify `OPENAI_API_KEY` is set in Render environment
2. Check authentication (endpoints require login)
3. Test with valid request payload

### **Frontend Shows "Failed to Load Dashboard"**
**Symptoms**: Frontend loads but can't connect to API
**Solutions**:
1. Check `VITE_API_BASE_URL` points to correct backend
2. Verify CORS origins include frontend domain
3. Test backend health endpoint directly

## 🛠️ **Debugging Commands**

### **Check Server Status**
```bash
curl https://ai-social-backend.onrender.com/render-health
```

### **Test Image Endpoint**
```bash
curl -X GET https://ai-social-backend.onrender.com/api/content/generate-image
# Should return 403 (auth required), not 404
```

### **Verify Environment**
```bash
curl https://ai-social-backend.onrender.com/health
# Check environment variables and services status
```

## 📋 **Environment Variables Checklist**

### **Required Variables**
- ✅ `ENVIRONMENT=production`
- ✅ `OPENAI_API_KEY=your_openai_key`
- ✅ `SECRET_KEY=generated_secret`

### **Optional Variables** (will gracefully degrade if missing)
- `DATABASE_URL` (PostgreSQL connection)
- `REDIS_URL` (Cache service)  
- `TWITTER_API_KEY`, `LINKEDIN_CLIENT_ID`, etc. (Social media APIs)

### **Frontend Variables**
- ✅ `VITE_API_BASE_URL=https://ai-social-backend.onrender.com`
- `VITE_AUTH0_DOMAIN`, `VITE_AUTH0_CLIENT_ID` (Authentication)

## 🚀 **Performance Optimizations**

### **Free Tier Limitations**
- Single worker process (no concurrency issues)
- 750 hours/month (about 31 days)
- Sleeps after 15 minutes of inactivity
- 500MB RAM limit

### **Cold Start Mitigation**
- Added comprehensive health checks
- Graceful degradation for missing features
- Optimized import structure
- Production logging configuration

## 📞 **Getting Help**

### **If Still Having Issues**
1. **Check Render Logs**: Go to service → Logs tab
2. **Run Local Verification**: `python verify_deployment.py`
3. **Test Health Endpoints**: All should return 200 status
4. **Check Environment Variables**: Ensure all required keys are set

### **Error Patterns**
- **Import Errors**: Usually missing dependencies → Check graceful degradation
- **Port Binding**: Server not responding → Check uvicorn configuration  
- **CORS Errors**: Frontend can't connect → Check origins configuration
- **Auth Errors**: 403 responses → Expected for protected endpoints

## ✅ **Success Indicators**

Your deployment is working correctly when:
- ✅ Health endpoint returns `"status": "healthy"`
- ✅ Docs page loads at `/docs`
- ✅ Frontend can connect to backend
- ✅ Image endpoints return 403 (auth required) not 404
- ✅ No import errors in server logs

---
*Render Deployment Troubleshooting Guide - Updated with Latest Fixes*