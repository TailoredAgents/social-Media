"""
Performance Dashboard API
Real-time performance monitoring dashboard with metrics visualization
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from backend.services.apm_service import apm_service
from backend.services.redis_cache import redis_cache
from backend.services.connection_pool_manager import connection_pool_manager
from backend.services.error_recovery_service import error_recovery_service
from backend.services.platform_optimization_service import platform_optimization_service
from backend.api.performance_monitoring import performance_api
from backend.db.database_optimized import health_check

logger = logging.getLogger(__name__)

# Create router for dashboard endpoints
dashboard_router = APIRouter(prefix="/dashboard", tags=["Performance Dashboard"])

class PerformanceDashboard:
    """
    Performance dashboard service providing comprehensive system insights
    """
    
    def __init__(self):
        self.dashboard_cache_ttl = 60  # Cache dashboard data for 1 minute
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview"""
        try:
            # Gather data from all monitoring services
            apm_summary = await apm_service.get_performance_summary()
            cache_stats = await redis_cache.get_cache_stats()
            db_health = await health_check.check_connection_health()
            error_analysis = await error_recovery_service.analyze_error_patterns()
            pool_metrics = connection_pool_manager.get_pool_metrics()
            
            # System health calculation
            health_components = {
                'apm': apm_summary.get('health_score', 0),
                'database': 100 if db_health.get('database_connected') else 0,
                'cache': 100 if cache_stats.get('redis_connected') else 80,  # 80 if fallback works
                'errors': max(0, 100 - error_analysis.get('total_errors', 0))
            }
            
            overall_health = sum(health_components.values()) / len(health_components)
            
            # Status determination
            if overall_health >= 90:
                status = "healthy"
            elif overall_health >= 75:
                status = "degraded"
            elif overall_health >= 50:
                status = "unhealthy"
            else:
                status = "critical"
            
            return {
                'status': status,
                'overall_health_score': round(overall_health, 2),
                'health_components': health_components,
                'summary': {
                    'active_alerts': apm_summary.get('active_alerts', 0),
                    'critical_alerts': apm_summary.get('critical_alerts', 0),
                    'total_errors': error_analysis.get('total_errors', 0),
                    'cache_hit_ratio': cache_stats.get('hit_ratio', 0),
                    'database_response_time': db_health.get('query_response_time', 0),
                    'active_connections': db_health.get('connection_pool_status', {}).get('checked_out', 0)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system overview: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def get_performance_metrics(self, hours: int = 1) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        try:
            # Get metrics from APM service
            current_metrics = await apm_service.get_current_metrics()
            historical_metrics = await apm_service.get_metrics_history(hours)
            
            # Get compression and response metrics
            compression_stats = await performance_api.get_compression_stats()
            endpoint_metrics = await performance_api.get_performance_metrics()
            
            return {
                'current': current_metrics,
                'historical': historical_metrics,
                'compression': compression_stats,
                'endpoints': endpoint_metrics,
                'period_hours': hours
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {'error': str(e)}
    
    async def get_alerts_dashboard(self) -> Dict[str, Any]:
        """Get alerts dashboard data"""
        try:
            # Get active alerts
            active_alerts = await apm_service.get_active_alerts()
            
            # Get error recovery recommendations
            recovery_recommendations = await error_recovery_service.get_recovery_recommendations()
            
            # Get system health from error perspective
            error_health = await error_recovery_service.get_system_health()
            
            # Categorize alerts by severity
            alerts_by_severity = {
                'critical': [],
                'error': [],
                'warning': [],
                'info': []
            }
            
            for alert in active_alerts:
                severity = alert.get('severity', 'info')
                alerts_by_severity[severity].append(alert)
            
            return {
                'active_alerts': active_alerts,
                'alerts_by_severity': alerts_by_severity,
                'total_alerts': len(active_alerts),
                'error_health': error_health,
                'recovery_recommendations': recovery_recommendations,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get alerts dashboard: {e}")
            return {'error': str(e)}
    
    async def get_infrastructure_status(self) -> Dict[str, Any]:
        """Get infrastructure component status"""
        try:
            # Database status
            db_health = await health_check.check_connection_health()
            
            # Cache status
            cache_health = await redis_cache.health_check()
            
            # Connection pool status
            pool_health = await connection_pool_manager.health_check_pools()
            
            # Error recovery status
            error_health = await error_recovery_service.get_system_health()
            
            # Compile infrastructure status
            components = {
                'database': {
                    'status': 'healthy' if db_health.get('database_connected') else 'unhealthy',
                    'response_time': db_health.get('query_response_time', 0),
                    'details': db_health
                },
                'cache': {
                    'status': cache_health.get('status', 'unknown'),
                    'redis_connected': cache_health.get('redis_connected', False),
                    'hit_ratio': cache_health.get('hit_ratio', 0),
                    'details': cache_health
                },
                'connection_pools': {
                    'status': 'healthy' if pool_health.get('total_pools', 0) > 0 else 'unhealthy',
                    'total_pools': pool_health.get('total_pools', 0),
                    'details': pool_health
                },
                'error_recovery': {
                    'status': error_health.get('status', 'unknown'),
                    'health_score': error_health.get('health_score', 0),
                    'details': error_health
                }
            }
            
            # Calculate overall infrastructure health
            healthy_components = sum(1 for comp in components.values() if comp['status'] == 'healthy')
            total_components = len(components)
            infrastructure_health = (healthy_components / total_components) * 100
            
            return {
                'overall_health': infrastructure_health,
                'healthy_components': healthy_components,
                'total_components': total_components,
                'components': components,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get infrastructure status: {e}")
            return {'error': str(e)}
    
    async def get_platform_optimization_dashboard(self) -> Dict[str, Any]:
        """Get platform optimization dashboard"""
        try:
            platforms = ['twitter', 'instagram', 'facebook', 'linkedin', 'tiktok']
            platform_data = {}
            
            for platform in platforms:
                try:
                    metrics = await platform_optimization_service.get_platform_performance_metrics(platform)
                    platform_data[platform] = metrics
                except Exception as e:
                    platform_data[platform] = {'error': str(e)}
            
            return {
                'platforms': platform_data,
                'total_platforms': len(platforms),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get platform optimization dashboard: {e}")
            return {'error': str(e)}
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for live dashboard updates"""
        try:
            # Get current metrics
            current_metrics = await apm_service.get_current_metrics()
            
            # Get latest alerts (last 5 minutes)
            active_alerts = await apm_service.get_active_alerts()
            recent_alerts = [
                alert for alert in active_alerts
                if datetime.fromisoformat(alert['timestamp']) >= datetime.utcnow() - timedelta(minutes=5)
            ]
            
            # Get performance summary
            performance_summary = await apm_service.get_performance_summary()
            
            # Get quick infrastructure status
            db_response_time = 0
            cache_connected = False
            
            try:
                db_health = await health_check.check_connection_health()
                db_response_time = db_health.get('query_response_time', 0)
                
                cache_health = await redis_cache.health_check()
                cache_connected = cache_health.get('redis_connected', False)
            except:
                pass
            
            return {
                'system_status': performance_summary.get('status', 'unknown'),
                'health_score': performance_summary.get('health_score', 0),
                'metrics': {
                    'cpu_usage': current_metrics.get('system', {}).get('cpu_percent', 0),
                    'memory_usage': current_metrics.get('system', {}).get('memory_percent', 0),
                    'response_time': current_metrics.get('system', {}).get('response_time_avg', 0),
                    'error_rate': current_metrics.get('system', {}).get('error_rate', 0),
                    'cache_hit_ratio': current_metrics.get('application', {}).get('cache_hit_ratio', 0),
                    'database_response_time': db_response_time
                },
                'alerts': {
                    'total_active': len(active_alerts),
                    'recent_count': len(recent_alerts),
                    'critical_count': len([a for a in active_alerts if a.get('severity') == 'critical'])
                },
                'infrastructure': {
                    'cache_connected': cache_connected,
                    'database_healthy': db_response_time < 1000 if db_response_time > 0 else False
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {e}")
            return {'error': str(e)}

# Global dashboard service
dashboard_service = PerformanceDashboard()

# API Endpoints
@dashboard_router.get("/overview")
async def get_dashboard_overview():
    """Get comprehensive dashboard overview"""
    try:
        # Try to get from cache first
        cached_data = await redis_cache.get("system", "dashboard_overview")
        if cached_data:
            return JSONResponse(content=cached_data)
        
        # Generate fresh data
        overview = await dashboard_service.get_system_overview()
        
        # Cache the result
        await redis_cache.set(
            "system", 
            "dashboard_overview", 
            overview, 
            ttl=dashboard_service.dashboard_cache_ttl
        )
        
        return JSONResponse(content=overview)
        
    except Exception as e:
        logger.error(f"Dashboard overview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@dashboard_router.get("/metrics")
async def get_dashboard_metrics(
    hours: int = Query(default=1, ge=1, le=24, description="Hours of historical data")
):
    """Get detailed performance metrics"""
    try:
        metrics = await dashboard_service.get_performance_metrics(hours)
        return JSONResponse(content=metrics)
        
    except Exception as e:
        logger.error(f"Dashboard metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@dashboard_router.get("/alerts")
async def get_dashboard_alerts():
    """Get alerts dashboard"""
    try:
        alerts = await dashboard_service.get_alerts_dashboard()
        return JSONResponse(content=alerts)
        
    except Exception as e:
        logger.error(f"Dashboard alerts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@dashboard_router.get("/infrastructure")
async def get_infrastructure_dashboard():
    """Get infrastructure status dashboard"""
    try:
        infrastructure = await dashboard_service.get_infrastructure_status()
        return JSONResponse(content=infrastructure)
        
    except Exception as e:
        logger.error(f"Infrastructure dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@dashboard_router.get("/platforms")
async def get_platform_dashboard():
    """Get platform optimization dashboard"""
    try:
        platforms = await dashboard_service.get_platform_optimization_dashboard()
        return JSONResponse(content=platforms)
        
    except Exception as e:
        logger.error(f"Platform dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@dashboard_router.get("/realtime")
async def get_realtime_metrics():
    """Get real-time metrics for live updates"""
    try:
        metrics = await dashboard_service.get_real_time_metrics()
        return JSONResponse(content=metrics)
        
    except Exception as e:
        logger.error(f"Real-time metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@dashboard_router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve a specific alert"""
    try:
        success = await apm_service.resolve_alert(alert_id)
        
        if success:
            return JSONResponse(content={
                'status': 'success',
                'message': f'Alert {alert_id} resolved',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Alert resolution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@dashboard_router.get("/health")
async def get_dashboard_health():
    """Quick health check endpoint for the dashboard itself"""
    try:
        start_time = datetime.utcnow()
        
        # Quick health checks
        apm_running = apm_service.is_monitoring
        
        # Test cache connectivity
        cache_test = None
        try:
            cache_test = await redis_cache.get("system", "health_test")
            await redis_cache.set("system", "health_test", "ok", ttl=60)
        except:
            pass
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return JSONResponse(content={
            'status': 'healthy',
            'apm_monitoring': apm_running,
            'cache_connectivity': cache_test is not None,
            'response_time_ms': response_time,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Dashboard health check error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )

# Dashboard configuration endpoint
@dashboard_router.get("/config")
async def get_dashboard_config():
    """Get dashboard configuration"""
    return JSONResponse(content={
        'refresh_intervals': {
            'realtime': 5,      # seconds
            'metrics': 30,      # seconds
            'overview': 60,     # seconds
            'infrastructure': 120  # seconds
        },
        'chart_config': {
            'max_data_points': 100,
            'time_formats': {
                '1h': '%H:%M',
                '6h': '%H:%M',
                '24h': '%H:%M',
                '7d': '%m/%d %H:%M'
            }
        },
        'alert_severities': ['info', 'warning', 'error', 'critical'],
        'platform_list': ['twitter', 'instagram', 'facebook', 'linkedin', 'tiktok'],
        'version': '1.0.0',
        'last_updated': datetime.utcnow().isoformat()
    })

# Export the router for inclusion in main app
__all__ = ['dashboard_router', 'dashboard_service']