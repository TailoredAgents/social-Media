#!/usr/bin/env python3
"""
Fallback FastAPI app with minimal dependencies
This will start even if some routers fail to load
"""
import sys
import os
import logging
from pathlib import Path

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting AI Social Media Content Agent (Fallback Mode)")
logger.info("Python version: {}".format(sys.version))
logger.info("Working directory: {}".format(os.getcwd()))

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
    logger.info("Added backend path: {}".format(backend_path))

# Import FastAPI with better error handling
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    logger.info("FastAPI imported successfully")
except ImportError as e:
    logger.error("Failed to import FastAPI: {}".format(e))
    logger.error("Please ensure FastAPI is installed: pip install fastapi")
    sys.exit(1)

# Create FastAPI app
app = FastAPI(
    title="AI Social Media Content Agent",
    description="Complete autonomous social media management platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware with specific configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ai-social-frontend.onrender.com",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:4173",
        "*"  # Allow all as fallback
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Cache-Control"
    ],
    expose_headers=["*"],
    max_age=86400,  # 24 hours
)

# Track loaded routers
loaded_routers = []
failed_routers = []

# Essential routers (must load for basic functionality)
essential_routers = [
    ("content", "backend.api.content_real"),
    ("memory", "backend.api.memory"),
]

# Optional routers (app will work even if these fail)
optional_routers = [
    ("system_logs", "backend.api.system_logs"),
    ("autonomous_stub", "backend.api.autonomous_stub"),
    ("goals", "backend.api.goals"),
    ("notifications_stub", "backend.api.notifications_stub"),
    ("workflow_stub", "backend.api.workflow_stub"),
    ("metrics", "backend.api.metrics_stub"),
]

# Load essential routers first
for router_name, module_path in essential_routers:
    try:
        module = __import__(module_path, fromlist=['router'])
        router = getattr(module, 'router', None)
        if router:
            app.include_router(router, tags=[router_name])
            loaded_routers.append(router_name)
            logger.info("{} router loaded successfully".format(router_name))
        else:
            failed_routers.append((router_name, "No router attribute"))
            logger.error("CRITICAL: {} router has no router attribute".format(router_name))
    except Exception as e:
        failed_routers.append((router_name, str(e)))
        logger.error("CRITICAL: {} router failed to load: {}".format(router_name, e))

# Load optional routers (failures are logged but don't prevent startup)
for router_name, module_path in optional_routers:
    try:
        module = __import__(module_path, fromlist=['router'])
        router = getattr(module, 'router', None)
        if router:
            app.include_router(router, tags=[router_name])
            loaded_routers.append(router_name)
            logger.info("{} router loaded successfully".format(router_name))
        else:
            failed_routers.append((router_name, "No router attribute"))
            logger.warning("Optional router {} has no router attribute".format(router_name))
    except Exception as e:
        failed_routers.append((router_name, str(e)))
        logger.warning("Optional router {} failed to load: {}".format(router_name, e))

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint with detailed status"""
    return {
        "message": "AI Social Media Content Agent API",
        "status": "operational",
        "version": "2.0.0",
        "mode": "fallback" if len(failed_routers) > 0 else "full",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "loaded_modules": loaded_routers,
        "failed_modules": [f[0] for f in failed_routers],
        "total_routes": len(app.routes),
        "api_docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "python_version": "{}.{}.{}".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "uptime": "Running",
        "features": {
            "environment": os.getenv("ENVIRONMENT", "production"),
            "available_features": loaded_routers,
            "missing_dependencies": ["{}: {}".format(name, error) for name, error in failed_routers],
            "total_features": len(loaded_routers),
            "status": "healthy" if len(loaded_routers) > 0 else "degraded"
        },
        "endpoints": {
            "total_routes": len(app.routes),
            "api_routes": len([r for r in app.routes if hasattr(r, 'path') and '/api/' in str(r.path)])
        },
        "services": {
            "openai": "available" if os.getenv("OPENAI_API_KEY") else "missing_key",
            "database": "configured" if os.getenv("DATABASE_URL") else "not_configured",
            "redis": "configured" if os.getenv("REDIS_URL") else "not_configured"
        }
    }

@app.get("/render-health")
async def render_health():
    """Render-specific health check"""
    return {
        "status": "healthy",
        "mode": "fallback" if len(failed_routers) > 0 else "production",
        "version": "2.0.0",
        "python_version": sys.version,
        "available_routes": len(app.routes),
        "loaded_modules": loaded_routers,
        "failed_modules": len(failed_routers),
        "ready": True
    }

# Basic error handling endpoints to prevent 404s
@app.get("/api/notifications/")
@app.options("/api/notifications/")
async def notifications_fallback():
    """Fallback for notifications endpoint"""
    return {
        "notifications": [],
        "total": 0,
        "message": "Notifications service not available - using fallback"
    }

@app.get("/api/system/logs")
@app.options("/api/system/logs")
async def system_logs_fallback():
    """Fallback for system logs endpoint"""
    return {
        "logs": [],
        "total": 0,
        "message": "System logs service not available - using fallback"
    }

@app.get("/api/system/logs/stats")
@app.options("/api/system/logs/stats")
async def system_logs_stats_fallback():
    """Fallback for system logs stats endpoint"""
    return {
        "total_errors": 0,
        "total_warnings": 0,
        "errors_last_hour": 0,
        "errors_last_day": 0,
        "message": "System logs service not available - using fallback"
    }

@app.get("/api/workflow/status/summary")
@app.options("/api/workflow/status/summary")
async def workflow_status_fallback():
    """Fallback for workflow status endpoint"""
    return {
        "status": "unavailable",
        "message": "Workflow service not available - using fallback"
    }

@app.get("/api/metrics")
@app.options("/api/metrics")
async def metrics_fallback():
    """Fallback for metrics endpoint"""
    return {
        "metrics": {},
        "message": "Metrics service not available - using fallback"
    }

@app.get("/api/autonomous/research/latest")
@app.options("/api/autonomous/research/latest")
async def autonomous_research_fallback():
    """Fallback for autonomous research endpoint"""
    return {
        "research": [],
        "message": "Autonomous research service not available - using fallback"
    }

# Handle all OPTIONS requests (CORS preflight)
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle CORS preflight requests for any path"""
    return {"message": "CORS preflight OK"}

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler with helpful information"""
    available_endpoints = [
        "/docs",
        "/health",
        "/render-health",
        "/api/content/",
        "/api/memory/"
    ]
    
    # Add loaded router endpoints
    for router_name in loaded_routers:
        if router_name in ["content", "memory", "goals"]:
            available_endpoints.append("/api/{}/".format(router_name))
    
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": "The requested endpoint does not exist",
            "available_endpoints": available_endpoints,
            "loaded_modules": loaded_routers,
            "documentation": "/docs",
            "mode": "fallback" if len(failed_routers) > 0 else "production"
        }
    )

# Log startup summary
logger.info("=" * 50)
logger.info("Loaded {} routers successfully".format(len(loaded_routers)))
logger.info("Failed to load {} routers".format(len(failed_routers)))
logger.info("Total routes: {}".format(len(app.routes)))
logger.info("App ready to start")
logger.info("=" * 50)

# Export the app
__all__ = ["app"]