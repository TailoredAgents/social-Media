# Cloudflare Custom Domain Configuration Guide

## Prerequisites
- Domain purchased and ready to transfer to Cloudflare
- Render backend and frontend services deployed
- Backend service should be running at: `your-backend.onrender.com`
- Frontend service should be running at: `your-frontend.onrender.com`

## Step 1: Add Domain to Cloudflare

1. **Login to Cloudflare Dashboard**: https://dash.cloudflare.com
2. **Add Site**: Click "+ Add site" and enter your domain (e.g., `lily-ai-socialmedia.com`)
3. **Select Plan**: Choose "Free" plan (sufficient for most use cases)
4. **DNS Scan**: Cloudflare will scan your existing DNS records
5. **Update Nameservers**: 
   - Copy the two nameservers provided by Cloudflare
   - Go to your domain registrar and update nameservers
   - Wait 24-48 hours for propagation

## Step 2: DNS Records Configuration

Add these DNS records in Cloudflare DNS section:

### Backend API (A Record)
```
Type: A
Name: api
Content: [Get IP from Render backend service settings]
TTL: Auto
Proxy Status: ✅ Proxied (orange cloud)
Comment: Backend API endpoint
```

### Frontend (CNAME Records)
```
Type: CNAME
Name: www
Content: your-frontend.onrender.com
TTL: Auto
Proxy Status: ✅ Proxied (orange cloud)
Comment: Website with www
```

```
Type: CNAME
Name: @ (root domain)
Content: your-frontend.onrender.com
TTL: Auto
Proxy Status: ✅ Proxied (orange cloud)
Comment: Root domain redirect
```

## Step 3: SSL/TLS Configuration

Go to **SSL/TLS** tab:

### Overview
- **Encryption Mode**: Full (strict)
- **Always Use HTTPS**: ON

### Edge Certificates
- ✅ **Always Use HTTPS**: ON
- ✅ **HTTP Strict Transport Security (HSTS)**: Enable with these settings:
  - Max Age Header: 6 months
  - Include Subdomains: ON
  - No-Sniff Header: ON

### Origin Server
- Generate Origin Certificate (valid for 15 years)
- Install on Render (if supported by plan)

## Step 4: Page Rules for Performance

Create these page rules (**Rules** → **Page Rules**):

### Rule 1: API Bypass Cache
```
URL: api.lily-ai-socialmedia.com/*
Settings:
- SSL: Full (strict)
- Cache Level: Bypass
- Browser Integrity Check: On
- Security Level: Medium
```

### Rule 2: Website Performance
```
URL: *.lily-ai-socialmedia.com/*
Settings:
- SSL: Full (strict)  
- Always Use HTTPS: On
- Browser Cache TTL: 4 hours
- Security Level: Medium
```

## Step 5: Security Configuration

### Security → WAF
- **Security Level**: Medium
- **Browser Integrity Check**: ON
- **Challenge Passage**: 30 minutes

### Security → Response Headers
Add these custom response headers:
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
X-XSS-Protection: 1; mode=block
```

## Step 6: Performance Optimization

### Speed → Optimization
- ✅ **Auto Minify**: CSS, HTML, JavaScript
- ✅ **Brotli**: ON
- ✅ **Early Hints**: ON
- ⚠️ **Rocket Loader**: OFF (can break React apps)

### Caching → Configuration
- **Browser Cache TTL**: 4 hours
- **Always Online**: ON
- **Development Mode**: OFF (enable only when making changes)

## Step 7: Custom Domains in Render

### Frontend Static Site
1. Go to your Static Site in Render Dashboard
2. **Settings** → **Custom Domains**
3. Add domains:
   - `lily-ai-socialmedia.com`
   - `www.lily-ai-socialmedia.com`
4. Wait for SSL certificate provisioning

### Backend Web Service  
1. Go to your Web Service in Render Dashboard
2. **Settings** → **Custom Domains**
3. Add domain:
   - `api.lily-ai-socialmedia.com` 
4. Wait for SSL certificate provisioning

## Step 8: Update Production Environment Variables

Add these environment variables to your **Backend Web Service** in Render:

```bash
# Production CORS Configuration
ALLOWED_ORIGINS=https://lily-ai-socialmedia.com,https://www.lily-ai-socialmedia.com

# Update base URLs for production
FRONTEND_URL=https://lily-ai-socialmedia.com
API_BASE_URL=https://api.lily-ai-socialmedia.com
```

Add these environment variables to your **Frontend Static Site** in Render:

```bash
# Production API Configuration  
VITE_API_BASE_URL=https://api.lily-ai-socialmedia.com
VITE_APP_TITLE=Lily AI Social Media
VITE_ENVIRONMENT=production
```

## Step 9: Testing and Verification

### DNS Propagation Check
```bash
# Check if DNS has propagated
dig lily-ai-socialmedia.com
dig api.lily-ai-socialmedia.com
dig www.lily-ai-socialmedia.com
```

### SSL Certificate Test
- Visit https://lily-ai-socialmedia.com
- Check for valid SSL certificate (green lock icon)
- Test API endpoint: https://api.lily-ai-socialmedia.com/docs

### Performance Testing
- Test website speed: https://pagespeed.web.dev/
- Check security headers: https://securityheaders.com/

## Troubleshooting

### Common Issues:

**DNS Not Resolving:**
- Wait 24-48 hours for nameserver propagation
- Check nameservers at domain registrar
- Verify DNS records in Cloudflare

**SSL Certificate Errors:**
- Ensure encryption mode is "Full (strict)"
- Wait for Render custom domain SSL provisioning
- Check origin certificate configuration

**CORS Errors:**
- Verify ALLOWED_ORIGINS environment variable
- Check Cloudflare proxy status (must be proxied)
- Ensure API subdomain is correctly configured

**502 Bad Gateway:**
- Verify backend service is running in Render
- Check custom domain configuration in Render
- Verify A record points to correct IP

## Production Checklist

- [ ] Domain added to Cloudflare
- [ ] Nameservers updated at registrar  
- [ ] DNS records configured (A, CNAME)
- [ ] SSL/TLS encryption set to "Full (strict)"
- [ ] HSTS enabled
- [ ] Page rules created for performance
- [ ] Security headers configured
- [ ] Performance optimization enabled
- [ ] Custom domains added to Render services
- [ ] Environment variables updated
- [ ] SSL certificates provisioned
- [ ] DNS propagation complete
- [ ] Website and API accessible via custom domain
- [ ] CORS working correctly
- [ ] Performance and security tests passed

## Support Resources

- **Cloudflare Documentation**: https://developers.cloudflare.com/
- **Render Custom Domains**: https://render.com/docs/custom-domains
- **SSL/TLS Best Practices**: https://developers.cloudflare.com/ssl/