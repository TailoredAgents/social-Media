"""
Advanced Database Connection Pool Manager
Enhanced connection pooling with dynamic scaling and health monitoring
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
from collections import defaultdict, deque

from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError, TimeoutError

from backend.core.config import get_settings, get_utc_now
from backend.db.database_optimized import db_optimizer

settings = get_settings()
logger = logging.getLogger(__name__)

@dataclass
class ConnectionPoolMetrics:
    """Connection pool performance metrics"""
    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    total_connections: int
    avg_connection_time: float
    peak_connections: int
    pool_exhaustion_count: int
    connection_errors: int
    slow_connections: int
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data

class ConnectionPoolManager:
    """
    Advanced connection pool manager with dynamic scaling and monitoring
    """
    
    def __init__(self):
        self.pools: Dict[str, Engine] = {}
        self.pool_metrics: Dict[str, ConnectionPoolMetrics] = {}
        self.connection_times = defaultdict(lambda: deque(maxlen=100))
        self.pool_configs = {}
        
        # Thresholds for dynamic scaling (optimized for production)
        self.scale_up_threshold = 0.75  # Scale up when 75% of connections are in use
        self.scale_down_threshold = 0.25  # Scale down when <25% of connections are in use
        self.max_pool_size = 100  # Increased for production workload
        self.min_pool_size = 10   # Higher minimum for production readiness
        
        # Health monitoring
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = {}
    
    def create_optimized_pool(
        self,
        database_url: str,
        pool_name: str = "default",
        initial_size: int = 15,  # Optimized for production
        max_overflow: int = 35,  # Increased overflow capacity
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Engine:
        """
        Create an optimized connection pool
        
        Args:
            database_url: Database connection URL
            pool_name: Name for the pool
            initial_size: Initial pool size
            max_overflow: Maximum overflow connections
            custom_config: Custom configuration overrides
            
        Returns:
            Configured SQLAlchemy engine
        """
        # Determine database type
        is_sqlite = database_url.startswith("sqlite")
        is_postgresql = database_url.startswith("postgresql")
        is_mysql = database_url.startswith("mysql")
        
        # Base configuration
        config = {
            "echo": settings.debug and settings.environment == "development",
            "echo_pool": settings.debug and settings.environment == "development",
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # 1 hour
            "pool_timeout": 30,
        }
        
        # Apply custom configuration
        if custom_config:
            config.update(custom_config)
        
        # Database-specific pool configuration
        if is_sqlite:
            config.update({
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 30,
                    "isolation_level": None
                }
            })
        else:
            config.update({
                "poolclass": QueuePool,
                "pool_size": initial_size,
                "max_overflow": max_overflow,
            })
            
            if is_postgresql:
                config["connect_args"] = {
                    "application_name": f"social_media_agent_{pool_name}",
                    "connect_timeout": 10,
                    "options": "-c timezone=UTC"
                }
                # Set isolation level using SQLAlchemy's parameter
                config["isolation_level"] = "READ COMMITTED"
            elif is_mysql:
                config["connect_args"] = {
                    "charset": "utf8mb4",
                    "connect_timeout": 10,
                    "read_timeout": 30,
                    "write_timeout": 30,
                    "autocommit": False
                }
        
        # Create engine
        engine = create_engine(database_url, **config)
        
        # Store configuration
        self.pool_configs[pool_name] = config
        self.pools[pool_name] = engine
        
        # Initialize metrics
        self.pool_metrics[pool_name] = ConnectionPoolMetrics(
            pool_size=initial_size,
            checked_in=0,
            checked_out=0,
            overflow=0,
            total_connections=0,
            avg_connection_time=0.0,
            peak_connections=0,
            pool_exhaustion_count=0,
            connection_errors=0,
            slow_connections=0,
            last_updated=get_utc_now()
        )
        
        # Add event listeners for monitoring
        self._add_pool_monitoring(engine, pool_name)
        
        # Add database-specific optimizations
        if is_postgresql:
            self._add_postgresql_optimizations(engine)
        elif is_mysql:
            self._add_mysql_optimizations(engine)
        elif is_sqlite:
            self._add_sqlite_optimizations(engine)
        
        logger.info(f"Created optimized connection pool '{pool_name}': size={initial_size}, overflow={max_overflow}")
        return engine
    
    def _add_pool_monitoring(self, engine: Engine, pool_name: str):
        """Add pool monitoring event listeners"""
        
        @event.listens_for(engine, "connect")
        def track_connect(dbapi_connection, connection_record):
            """Track connection creation"""
            start_time = time.time()
            connection_record.info['connect_start'] = start_time
            
            metrics = self.pool_metrics[pool_name]
            metrics.total_connections += 1
            
            # Update pool status
            if hasattr(engine.pool, 'checkedout'):
                metrics.checked_out = engine.pool.checkedout()
                metrics.checked_in = engine.pool.checkedin()
                metrics.overflow = engine.pool.overflow()
                
                current_total = metrics.checked_out + metrics.checked_in
                if current_total > metrics.peak_connections:
                    metrics.peak_connections = current_total
            
            metrics.last_updated = get_utc_now()
        
        @event.listens_for(engine, "checkout")
        def track_checkout(dbapi_connection, connection_record, connection_proxy):
            """Track connection checkout"""
            if 'connect_start' in connection_record.info:
                connection_time = (time.time() - connection_record.info['connect_start']) * 1000
                self.connection_times[pool_name].append(connection_time)
                
                # Update average connection time
                times = list(self.connection_times[pool_name])
                metrics = self.pool_metrics[pool_name]
                metrics.avg_connection_time = sum(times) / len(times)
                
                # Track slow connections (>500ms)
                if connection_time > 500:
                    metrics.slow_connections += 1
                    logger.warning(f"Slow connection in pool '{pool_name}': {connection_time:.2f}ms")
        
        @event.listens_for(engine, "close")
        def track_close(dbapi_connection, connection_record):
            """Track connection close"""
            metrics = self.pool_metrics[pool_name]
            metrics.last_updated = get_utc_now()
        
        @event.listens_for(engine, "close_detached")
        def track_detached_close(dbapi_connection):
            """Track detached connection close"""
            metrics = self.pool_metrics[pool_name]
            metrics.last_updated = get_utc_now()
    
    def _add_postgresql_optimizations(self, engine: Engine):
        """Add PostgreSQL-specific optimizations"""
        
        @event.listens_for(engine, "connect")
        def set_postgresql_session_config(dbapi_connection, connection_record):
            """Configure PostgreSQL session parameters"""
            with dbapi_connection.cursor() as cursor:
                # Performance optimizations
                cursor.execute("SET statement_timeout = '30s'")
                cursor.execute("SET lock_timeout = '10s'")
                cursor.execute("SET idle_in_transaction_session_timeout = '60s'")
                
                # Memory settings for better performance
                cursor.execute("SET work_mem = '16MB'")
                cursor.execute("SET maintenance_work_mem = '64MB'")
                
                # Connection-level optimizations
                cursor.execute("SET tcp_keepalives_idle = 600")
                cursor.execute("SET tcp_keepalives_interval = 30")
                cursor.execute("SET tcp_keepalives_count = 3")
    
    def _add_mysql_optimizations(self, engine: Engine):
        """Add MySQL-specific optimizations"""
        
        @event.listens_for(engine, "connect")
        def set_mysql_session_config(dbapi_connection, connection_record):
            """Configure MySQL session parameters"""
            with dbapi_connection.cursor() as cursor:
                # Performance optimizations
                cursor.execute("SET SESSION max_execution_time = 30000")  # 30 seconds
                cursor.execute("SET SESSION innodb_lock_wait_timeout = 10")
                
                # Memory settings
                cursor.execute("SET SESSION sort_buffer_size = 2097152")  # 2MB
                cursor.execute("SET SESSION join_buffer_size = 262144")   # 256KB
                
                # Character set for proper Unicode support
                cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
    
    def _add_sqlite_optimizations(self, engine: Engine):
        """Add SQLite-specific optimizations"""
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Configure SQLite pragma statements"""
            cursor = dbapi_connection.cursor()
            
            # Performance optimizations
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            # Query optimization
            cursor.execute("PRAGMA optimize")
            
            # Foreign key support
            cursor.execute("PRAGMA foreign_keys=ON")
            
            cursor.close()
    
    async def scale_pool_dynamically(self, pool_name: str = "default") -> Dict[str, Any]:
        """
        Dynamically scale connection pool based on usage
        
        Args:
            pool_name: Name of the pool to scale
            
        Returns:
            Scaling action taken
        """
        if pool_name not in self.pools:
            return {"error": f"Pool '{pool_name}' not found"}
        
        engine = self.pools[pool_name]
        metrics = self.pool_metrics[pool_name]
        
        try:
            # Calculate utilization
            total_connections = metrics.checked_out + metrics.checked_in
            if total_connections == 0:
                utilization = 0
            else:
                utilization = metrics.checked_out / total_connections
            
            current_pool_size = metrics.pool_size
            action_taken = "none"
            
            # Scale up if utilization is high
            if utilization > self.scale_up_threshold and current_pool_size < self.max_pool_size:
                new_size = min(current_pool_size + 5, self.max_pool_size)
                
                # Note: SQLAlchemy doesn't support dynamic pool resizing
                # This would require recreating the engine with new pool size
                # For now, we'll log the recommendation
                logger.info(f"Recommendation: Scale up pool '{pool_name}' from {current_pool_size} to {new_size}")
                action_taken = f"recommend_scale_up_to_{new_size}"
            
            # Scale down if utilization is low
            elif utilization < self.scale_down_threshold and current_pool_size > self.min_pool_size:
                new_size = max(current_pool_size - 2, self.min_pool_size)
                logger.info(f"Recommendation: Scale down pool '{pool_name}' from {current_pool_size} to {new_size}")
                action_taken = f"recommend_scale_down_to_{new_size}"
            
            return {
                "pool_name": pool_name,
                "current_size": current_pool_size,
                "utilization": utilization,
                "action": action_taken,
                "checked_out": metrics.checked_out,
                "checked_in": metrics.checked_in,
                "total_connections": total_connections
            }
            
        except Exception as e:
            logger.error(f"Error scaling pool '{pool_name}': {e}")
            return {"error": str(e)}
    
    async def health_check_pools(self) -> Dict[str, Any]:
        """
        Perform health check on all connection pools
        
        Returns:
            Health status of all pools
        """
        health_results = {}
        
        for pool_name, engine in self.pools.items():
            try:
                start_time = time.time()
                
                # Test connection
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1")).fetchone()
                
                response_time = (time.time() - start_time) * 1000
                
                # Get pool status
                pool_status = {
                    "healthy": True,
                    "response_time_ms": response_time,
                    "pool_size": engine.pool.size(),
                    "checked_in": engine.pool.checkedin(),
                    "checked_out": engine.pool.checkedout(),
                    "overflow": engine.pool.overflow(),
                    "status": engine.pool.status()
                }
                
                # Check for potential issues
                warnings = []
                if response_time > 1000:
                    warnings.append("Slow response time")
                if engine.pool.checkedout() / max(engine.pool.size(), 1) > 0.9:
                    warnings.append("High pool utilization")
                if hasattr(engine.pool, 'invalidated') and engine.pool.invalidated():
                    warnings.append("Pool has invalidated connections")
                
                pool_status["warnings"] = warnings
                health_results[pool_name] = pool_status
                
                # Update last health check time
                self.last_health_check[pool_name] = get_utc_now()
                
            except Exception as e:
                health_results[pool_name] = {
                    "healthy": False,
                    "error": str(e),
                    "last_check": get_utc_now().isoformat()
                }
                
                # Increment error count
                if pool_name in self.pool_metrics:
                    self.pool_metrics[pool_name].connection_errors += 1
        
        return {
            "timestamp": get_utc_now().isoformat(),
            "pools": health_results,
            "total_pools": len(self.pools)
        }
    
    def get_pool_metrics(self, pool_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get connection pool metrics
        
        Args:
            pool_name: Specific pool name (None for all pools)
            
        Returns:
            Pool metrics
        """
        if pool_name:
            if pool_name in self.pool_metrics:
                return self.pool_metrics[pool_name].to_dict()
            else:
                return {"error": f"Pool '{pool_name}' not found"}
        
        return {
            pool: metrics.to_dict() 
            for pool, metrics in self.pool_metrics.items()
        }
    
    def get_pool_recommendations(self) -> Dict[str, List[str]]:
        """
        Get optimization recommendations for all pools
        
        Returns:
            Recommendations for each pool
        """
        recommendations = {}
        
        for pool_name, metrics in self.pool_metrics.items():
            pool_recommendations = []
            
            # Check for high error rates
            if metrics.connection_errors > 10:
                pool_recommendations.append("Consider investigating connection errors")
            
            # Check for slow connections
            if metrics.slow_connections > 5:
                pool_recommendations.append("High number of slow connections detected")
            
            # Check average connection time
            if metrics.avg_connection_time > 200:
                pool_recommendations.append("Consider optimizing connection establishment")
            
            # Check pool exhaustion
            if metrics.pool_exhaustion_count > 0:
                pool_recommendations.append("Pool exhaustion detected, consider increasing pool size")
            
            # Check utilization for scaling
            total_connections = metrics.checked_out + metrics.checked_in
            if total_connections > 0:
                utilization = metrics.checked_out / total_connections
                if utilization > 0.8:
                    pool_recommendations.append("High utilization, consider scaling up")
                elif utilization < 0.2:
                    pool_recommendations.append("Low utilization, consider scaling down")
            
            recommendations[pool_name] = pool_recommendations
        
        return recommendations
    
    async def optimize_all_pools(self) -> Dict[str, Any]:
        """
        Run optimization tasks on all pools
        
        Returns:
            Optimization results
        """
        results = {}
        
        for pool_name in self.pools.keys():
            try:
                # Perform health check
                health = await self.health_check_pools()
                
                # Check for dynamic scaling opportunities
                scaling = await self.scale_pool_dynamically(pool_name)
                
                # Get recommendations
                recommendations = self.get_pool_recommendations()
                
                results[pool_name] = {
                    "health": health["pools"].get(pool_name, {}),
                    "scaling": scaling,
                    "recommendations": recommendations.get(pool_name, [])
                }
                
            except Exception as e:
                results[pool_name] = {"error": str(e)}
        
        return {
            "optimization_timestamp": get_utc_now().isoformat(),
            "pools": results
        }
    
    def close_all_pools(self):
        """Close all connection pools gracefully"""
        for pool_name, engine in self.pools.items():
            try:
                engine.dispose()
                logger.info(f"Closed connection pool '{pool_name}'")
            except Exception as e:
                logger.error(f"Error closing pool '{pool_name}': {e}")
        
        self.pools.clear()
        self.pool_metrics.clear()

# Global connection pool manager
connection_pool_manager = ConnectionPoolManager()