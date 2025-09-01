"""
Production Monitoring, Alerting, and Health Check Endpoints
Comprehensive monitoring system for production readiness
"""
import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

from backend.db.database import get_db
from backend.core.config import get_utc_now
from backend.db.database_optimized import health_check as db_health, db_optimizer
from backend.services.redis_cache import redis_cache
from backend.services.quota_management import quota_manager
from backend.services.metrics_collection import metrics_collector
from backend.integrations.performance_optimizer import PerformanceOptimizer
from backend.auth.dependencies import get_current_active_user
from backend.db.models import User

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])
logger = logging.getLogger(__name__)

# Global monitoring state
monitoring_state = {
    "startup_time": get_utc_now(),
    "health_checks": [],
    "alerts": [],
    "system_metrics": {},
    "last_health_check": None
}

class SystemMonitor:
    """
    Comprehensive system monitoring for production environments
    
    Features:
    - Real-time health checks
    - Performance monitoring
    - Resource usage tracking
    - Alert management
    - Integration status monitoring
    - Database performance tracking
    """
    
    def __init__(self):
        self.performance_optimizer = PerformanceOptimizer()
        self.alert_thresholds = {
            "cpu_usage": 80.0,          # 80% CPU usage
            "memory_usage": 85.0,       # 85% memory usage
            "disk_usage": 90.0,         # 90% disk usage
            "response_time": 1000.0,    # 1000ms response time
            "error_rate": 5.0,          # 5% error rate
            "database_connections": 90.0 # 90% of pool capacity
        }
        
        self.metrics_history = []
        self.max_history_size = 1000
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        
        health_status = {
            "timestamp": get_utc_now().isoformat(),
            "overall_status": "healthy",
            "uptime_seconds": (get_utc_now() - monitoring_state["startup_time"]).total_seconds(),
            "components": {},
            "alerts": [],
            "performance_metrics": {}
        }
        
        # Check database health
        try:
            db_health_result = await db_health.check_connection_health()
            health_status["components"]["database"] = {
                "status": "healthy" if db_health_result["database_connected"] else "unhealthy",
                "response_time_ms": db_health_result.get("query_response_time", 0),
                "connection_pool": db_health_result.get("connection_pool_status", {}),
                "error": db_health_result.get("error")
            }
            
            if not db_health_result["database_connected"]:
                health_status["overall_status"] = "degraded"
                health_status["alerts"].append({
                    "severity": "critical",
                    "message": "Database connection failed",
                    "component": "database"
                })
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall_status"] = "critical"
        
        # Check Redis cache health
        try:
            cache_health = await redis_cache.health_check()
            health_status["components"]["cache"] = cache_health
            
            if cache_health["status"] == "unhealthy":
                health_status["overall_status"] = "degraded"
                health_status["alerts"].append({
                    "severity": "warning",
                    "message": "Redis cache unavailable, using fallback",
                    "component": "cache"
                })
                
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            health_status["components"]["cache"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check quota management
        try:
            quota_stats = await quota_manager.get_quota_stats()
            health_status["components"]["quota_management"] = {
                "status": "healthy" if not quota_stats.critical_platforms else "warning",
                "critical_platforms": quota_stats.critical_platforms,
                "average_utilization": quota_stats.average_utilization,
                "total_requests": quota_stats.total_requests_today
            }
            
            if quota_stats.critical_platforms:
                health_status["alerts"].append({
                    "severity": "warning",
                    "message": f"Critical quota usage on platforms: {', '.join(quota_stats.critical_platforms)}",
                    "component": "quota_management"
                })
                
        except Exception as e:
            logger.error(f"Quota management health check failed: {e}")
            health_status["components"]["quota_management"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # System resource monitoring
        try:
            system_metrics = self._get_system_metrics()
            health_status["performance_metrics"] = system_metrics
            
            # Check for resource alerts
            if system_metrics["cpu_percent"] > self.alert_thresholds["cpu_usage"]:
                health_status["alerts"].append({
                    "severity": "warning",
                    "message": f"High CPU usage: {system_metrics['cpu_percent']:.1f}%",
                    "component": "system"
                })
            
            if system_metrics["memory_percent"] > self.alert_thresholds["memory_usage"]:
                health_status["alerts"].append({
                    "severity": "warning",
                    "message": f"High memory usage: {system_metrics['memory_percent']:.1f}%",
                    "component": "system"
                })
                
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
            health_status["performance_metrics"] = {"error": str(e)}
        
        # Update overall status based on alerts
        if health_status["alerts"]:
            critical_alerts = [a for a in health_status["alerts"] if a["severity"] == "critical"]
            if critical_alerts:
                health_status["overall_status"] = "critical"
            elif health_status["overall_status"] == "healthy":
                health_status["overall_status"] = "warning"
        
        # Store health check result
        monitoring_state["last_health_check"] = health_status
        monitoring_state["health_checks"].append({
            "timestamp": health_status["timestamp"],
            "status": health_status["overall_status"],
            "alert_count": len(health_status["alerts"])
        })
        
        # Keep only last 100 health checks
        if len(monitoring_state["health_checks"]) > 100:
            monitoring_state["health_checks"] = monitoring_state["health_checks"][-100:]
        
        return health_status
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_mb = memory.total / 1024 / 1024
        memory_used_mb = memory.used / 1024 / 1024
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_gb = disk.total / 1024 / 1024 / 1024
        disk_used_gb = disk.used / 1024 / 1024 / 1024
        
        # Network metrics
        network = psutil.net_io_counters()
        
        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "cpu_percent": cpu_percent,
            "cpu_count": cpu_count,
            "memory_total_mb": round(memory_mb, 2),
            "memory_used_mb": round(memory_used_mb, 2),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk_gb, 2),
            "disk_used_gb": round(disk_used_gb, 2),
            "disk_percent": (disk_used_gb / disk_gb) * 100,
            "network_bytes_sent": network.bytes_sent,
            "network_bytes_recv": network.bytes_recv,
            "process_memory_mb": round(process_memory.rss / 1024 / 1024, 2),
            "process_threads": process.num_threads(),
            "timestamp": get_utc_now().isoformat()
        }
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all social media integrations"""
        
        integration_status = {
            "timestamp": get_utc_now().isoformat(),
            "platforms": {},
            "overall_status": "healthy"
        }
        
        platforms = ["twitter", "instagram", "facebook", "linkedin", "tiktok"]
        
        for platform in platforms:
            try:
                # Get quota status for platform
                quota_info = await quota_manager.get_platform_quota(platform)
                
                platform_status = {
                    "status": "healthy" if quota_info.status.value in ["normal", "warning"] else "degraded",
                    "quota_utilization": quota_info.utilization_percent,
                    "quota_status": quota_info.status.value,
                    "requests_remaining": quota_info.quota_limit - quota_info.current_usage,
                    "reset_time": quota_info.reset_time.isoformat(),
                    "burst_available": quota_info.burst_available
                }
                
                integration_status["platforms"][platform] = platform_status
                
                # Update overall status
                if platform_status["status"] == "degraded":
                    integration_status["overall_status"] = "degraded"
                    
            except Exception as e:
                logger.error(f"Failed to get {platform} integration status: {e}")
                integration_status["platforms"][platform] = {
                    "status": "error",
                    "error": str(e)
                }
                integration_status["overall_status"] = "degraded"
        
        return integration_status

# Global system monitor instance
system_monitor = SystemMonitor()

# Health check endpoints
@router.get("/health", summary="System Health Check")
async def health_check():
    """
    Comprehensive system health check
    
    Returns overall system status and component health details.
    Used by load balancers and monitoring systems.
    """
    try:
        health_status = await system_monitor.get_system_health()
        
        # Return appropriate HTTP status code
        if health_status["overall_status"] == "critical":
            raise HTTPException(status_code=503, detail=health_status)
        elif health_status["overall_status"] == "degraded":
            raise HTTPException(status_code=206, detail=health_status)
        
        return health_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e), "status": "critical"})

@router.get("/health/detailed", summary="Detailed Health Information")
async def detailed_health_check(current_user: User = Depends(get_current_active_user)):
    """
    Detailed health information for authenticated users
    
    Includes comprehensive system metrics, performance data, and diagnostic information.
    """
    try:
        health_status = await system_monitor.get_system_health()
        
        # Add detailed metrics
        health_status["database_performance"] = db_optimizer.get_stats()
        health_status["cache_metrics"] = await redis_cache.get_cache_stats()
        health_status["integration_status"] = await system_monitor.get_integration_status()
        
        return health_status
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@router.get("/metrics", summary="System Metrics")
async def get_system_metrics(current_user: User = Depends(get_current_active_user)):
    """
    Get comprehensive system performance metrics
    
    Returns detailed metrics for monitoring and alerting systems.
    """
    try:
        metrics = {
            "timestamp": get_utc_now().isoformat(),
            "system": system_monitor._get_system_metrics(),
            "database": db_optimizer.get_stats(),
            "cache": await redis_cache.get_cache_stats(),
            "quota": await quota_manager.get_quota_stats(),
            "integrations": await system_monitor.get_integration_status()
        }
        
        # Add to metrics history
        system_monitor.metrics_history.append(metrics)
        if len(system_monitor.metrics_history) > system_monitor.max_history_size:
            system_monitor.metrics_history = system_monitor.metrics_history[-system_monitor.max_history_size:]
        
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@router.get("/metrics/history", summary="Historical Metrics")
async def get_metrics_history(
    hours: int = 24,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get historical system metrics
    
    Args:
        hours: Number of hours of history to retrieve (max 168 = 1 week)
    """
    try:
        hours = min(hours, 168)  # Limit to 1 week
        cutoff_time = get_utc_now() - timedelta(hours=hours)
        
        # Filter metrics history
        filtered_metrics = [
            m for m in system_monitor.metrics_history
            if datetime.fromisoformat(m["timestamp"]) >= cutoff_time
        ]
        
        return {
            "period_hours": hours,
            "metrics_count": len(filtered_metrics),
            "metrics": filtered_metrics,
            "summary": {
                "avg_cpu": sum(m["system"]["cpu_percent"] for m in filtered_metrics) / len(filtered_metrics) if filtered_metrics else 0,
                "avg_memory": sum(m["system"]["memory_percent"] for m in filtered_metrics) / len(filtered_metrics) if filtered_metrics else 0,
                "avg_response_time": sum(m["database"]["avg_query_time"] for m in filtered_metrics) / len(filtered_metrics) if filtered_metrics else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Historical metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@router.get("/alerts", summary="System Alerts")
async def get_system_alerts(current_user: User = Depends(get_current_active_user)):
    """
    Get current system alerts and warnings
    
    Returns active alerts across all system components.
    """
    try:
        health_status = await system_monitor.get_system_health()
        
        return {
            "timestamp": get_utc_now().isoformat(),
            "alert_count": len(health_status["alerts"]),
            "alerts": health_status["alerts"],
            "system_status": health_status["overall_status"],
            "alert_history": monitoring_state["alerts"][-50:]  # Last 50 alerts
        }
        
    except Exception as e:
        logger.error(f"Alert retrieval failed: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@router.post("/alerts/acknowledge", summary="Acknowledge Alert")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Acknowledge a system alert
    
    Args:
        alert_id: ID of the alert to acknowledge
    """
    try:
        # In a production system, this would update alert status in database
        monitoring_state["alerts"].append({
            "id": alert_id,
            "action": "acknowledged",
            "user_id": current_user.id,
            "timestamp": get_utc_now().isoformat()
        })
        
        return {
            "success": True,
            "message": f"Alert {alert_id} acknowledged",
            "acknowledged_by": current_user.email,
            "timestamp": get_utc_now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Alert acknowledgment failed: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@router.get("/status", summary="Service Status Dashboard")
async def service_status():
    """
    Public service status dashboard
    
    Returns high-level service status for public status pages.
    """
    try:
        health_status = await system_monitor.get_system_health()
        integration_status = await system_monitor.get_integration_status()
        
        return {
            "service_name": "AI Social Media Content Agent",
            "status": health_status["overall_status"],
            "timestamp": get_utc_now().isoformat(),
            "uptime_seconds": health_status["uptime_seconds"],
            "components": {
                "api": {"status": "operational" if health_status["overall_status"] != "critical" else "major_outage"},
                "database": {"status": health_status["components"]["database"]["status"]},
                "cache": {"status": health_status["components"]["cache"]["status"]},
                "integrations": {"status": integration_status["overall_status"]}
            },
            "incident_count": len([a for a in health_status["alerts"] if a["severity"] == "critical"])
        }
        
    except Exception as e:
        logger.error(f"Service status check failed: {e}")
        return {
            "service_name": "AI Social Media Content Agent",
            "status": "major_outage",
            "timestamp": get_utc_now().isoformat(),
            "error": str(e)
        }

from pydantic import BaseModel, Field

class FrontendLogEntry(BaseModel):
    level: str = Field(..., pattern="^(error|warn|info|debug)$")
    message: str = Field(..., max_length=1000)
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: Optional[str] = Field(None)
    session_id: Optional[str] = Field(None)
    url: Optional[str] = Field(None)
    user_agent: Optional[str] = Field(None)

@router.post("/frontend-logs", response_model=None)
async def receive_frontend_logs(
    log_entry: FrontendLogEntry,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receive and process frontend logs for monitoring and debugging.
    
    This endpoint collects frontend logs to provide operational telemetry
    in production environments.
    """
    try:
        # Create standardized log entry
        # Try to extract user information from request headers if available
        user_id = None
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # We could decode the JWT here, but for logging purposes
                # we'll just note that an authenticated request was made
                user_id = "authenticated_user"
        except:
            pass  # Anonymous logging is allowed
        
        log_data = {
            "source": "frontend",
            "level": log_entry.level,
            "message": log_entry.message,
            "data": log_entry.data,
            "timestamp": log_entry.timestamp or get_utc_now().isoformat(),
            "session_id": log_entry.session_id,
            "url": log_entry.url,
            "user_agent": log_entry.user_agent,
            "user_id": user_id
        }
        
        # Log to backend logger with appropriate level
        if log_entry.level == "error":
            logger.error(f"Frontend Error: {log_entry.message}", extra=log_data)
        elif log_entry.level == "warn":
            logger.warning(f"Frontend Warning: {log_entry.message}", extra=log_data)
        elif log_entry.level == "info":
            logger.info(f"Frontend Info: {log_entry.message}", extra=log_data)
        else:  # debug
            logger.debug(f"Frontend Debug: {log_entry.message}", extra=log_data)
        
        # Store in monitoring state for dashboard
        monitoring_state["health_checks"].append({
            "check_type": "frontend_log",
            "timestamp": log_data["timestamp"],
            "status": "error" if log_entry.level == "error" else "healthy",
            "details": log_data
        })
        
        # Keep only last 1000 logs to prevent memory issues
        if len(monitoring_state["health_checks"]) > 1000:
            monitoring_state["health_checks"] = monitoring_state["health_checks"][-1000:]
        
        return {
            "status": "success",
            "message": "Log entry received",
            "timestamp": log_data["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Error processing frontend log: {e}")
        return {
            "status": "error", 
            "message": f"Failed to process log: {str(e)}"
        }

@router.get("/frontend-logs")
async def get_frontend_logs(
    limit: int = 100,
    level: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get recent frontend logs for debugging (admin only)"""
    try:
        # Filter frontend logs from monitoring state
        frontend_logs = [
            check for check in monitoring_state["health_checks"]
            if check["check_type"] == "frontend_log"
        ]
        
        # Filter by level if specified
        if level:
            frontend_logs = [
                log for log in frontend_logs 
                if log["details"]["level"] == level
            ]
        
        # Sort by timestamp (most recent first) and limit
        frontend_logs = sorted(
            frontend_logs, 
            key=lambda x: x["timestamp"], 
            reverse=True
        )[:limit]
        
        return {
            "status": "success",
            "logs": frontend_logs,
            "count": len(frontend_logs)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving frontend logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")

# Background monitoring tasks
async def continuous_monitoring():
    """Background task for continuous system monitoring"""
    while True:
        try:
            # Perform health check every 60 seconds
            await system_monitor.get_system_health()
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Continuous monitoring error: {e}")
            await asyncio.sleep(60)

# Initialize monitoring on startup
@router.on_event("startup")
async def start_monitoring():
    """Start background monitoring tasks"""
    asyncio.create_task(continuous_monitoring())
    logger.info("Production monitoring system started")