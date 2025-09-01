"""
Optimized Database Configuration with Connection Pooling and Performance Tuning
Production-ready database setup with advanced optimizations
"""
import logging
import time
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.orm import sessionmaker, Session, scoped_session, declarative_base
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.engine import Engine
import asyncio

from backend.core.config import get_settings, get_utc_now

settings = get_settings()
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """
    Advanced database optimization and monitoring
    """
    
    def __init__(self):
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "peak_connections": 0,
            "total_queries": 0,
            "slow_queries": 0,
            "avg_query_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        self.slow_query_threshold = 1.0  # seconds
        self.query_times = []
        
    def track_connection(self, dbapi_connection, connection_record):
        """Track new database connections"""
        self.connection_stats["total_connections"] += 1
        self.connection_stats["active_connections"] += 1
        
        if self.connection_stats["active_connections"] > self.connection_stats["peak_connections"]:
            self.connection_stats["peak_connections"] = self.connection_stats["active_connections"]
        
        logger.debug(f"New DB connection: {self.connection_stats['active_connections']} active")
    
    def track_disconnection(self, dbapi_connection, connection_record):
        """Track database disconnections"""
        self.connection_stats["active_connections"] = max(0, self.connection_stats["active_connections"] - 1)
        logger.debug(f"DB connection closed: {self.connection_stats['active_connections']} active")
    
    def track_query_start(self, conn, cursor, statement, parameters, context, executemany):
        """Track query execution start"""
        context._query_start_time = time.time()
    
    def track_query_end(self, conn, cursor, statement, parameters, context, executemany):
        """Track query execution end"""
        if hasattr(context, '_query_start_time'):
            query_time = time.time() - context._query_start_time
            
            self.connection_stats["total_queries"] += 1
            self.query_times.append(query_time)
            
            # Keep only last 1000 query times for average calculation
            if len(self.query_times) > 1000:
                self.query_times = self.query_times[-1000:]
            
            # Update average
            self.connection_stats["avg_query_time"] = sum(self.query_times) / len(self.query_times)
            
            # Track slow queries
            if query_time > self.slow_query_threshold:
                self.connection_stats["slow_queries"] += 1
                logger.warning(f"Slow query ({query_time:.2f}s): {statement[:100]}...")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        return {
            **self.connection_stats,
            "slow_query_percentage": (
                (self.connection_stats["slow_queries"] / max(1, self.connection_stats["total_queries"])) * 100
            ),
            "last_updated": get_utc_now().isoformat()
        }

# Global database optimizer
db_optimizer = DatabaseOptimizer()

def create_optimized_engine(database_url: str) -> Engine:
    """
    Create optimized database engine with connection pooling and performance tuning
    
    Args:
        database_url: Database connection URL
        
    Returns:
        Configured SQLAlchemy engine
    """
    # Determine database type and set appropriate configurations
    is_sqlite = database_url.startswith("sqlite")
    is_postgresql = database_url.startswith("postgresql")
    is_mysql = database_url.startswith("mysql")
    
    # Base engine arguments
    engine_args = {
        "echo": settings.debug and settings.environment == "development",
        "echo_pool": settings.debug and settings.environment == "development"
    }
    
    # Connection pool configuration
    if is_sqlite:
        # SQLite configuration for development
        engine_args.update({
            "poolclass": StaticPool,
            "connect_args": {
                "check_same_thread": False,
                "timeout": 30,
                # SQLite optimizations
                "isolation_level": None  # Autocommit mode for better performance
            }
        })
    else:
        # PostgreSQL/MySQL configuration for production
        engine_args.update({
            "poolclass": QueuePool,
            "pool_size": 25,          # Increased base connections for production
            "max_overflow": 40,       # Increased overflow for peak loads
            "pool_pre_ping": True,    # Verify connections before use
            "pool_recycle": 3600,     # Recycle connections every hour
            "pool_timeout": 30,       # Timeout for getting connection from pool
        })
        
        if is_postgresql:
            engine_args["connect_args"] = {
                "application_name": "social_media_agent",
                "connect_timeout": 10,
                # PostgreSQL specific optimizations
                "options": "-c timezone=UTC"
            }
            # Set isolation level using SQLAlchemy's parameter
            engine_args["isolation_level"] = "READ COMMITTED"
        elif is_mysql:
            engine_args["connect_args"] = {
                "charset": "utf8mb4",
                "connect_timeout": 10,
                "read_timeout": 30,
                "write_timeout": 30
            }
    
    # Create engine
    engine = create_engine(database_url, **engine_args)
    
    # Add event listeners for monitoring
    event.listen(engine, "connect", db_optimizer.track_connection)
    event.listen(engine, "close", db_optimizer.track_disconnection)
    event.listen(engine, "before_cursor_execute", db_optimizer.track_query_start)
    event.listen(engine, "after_cursor_execute", db_optimizer.track_query_end)
    
    # Database-specific optimizations
    if is_sqlite:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite optimizations"""
            cursor = dbapi_connection.cursor()
            
            # Performance optimizations
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            cursor.execute("PRAGMA synchronous=NORMAL")  # Faster but still safe
            cursor.execute("PRAGMA cache_size=10000")  # 10MB cache
            cursor.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
            
            # Foreign key support
            cursor.execute("PRAGMA foreign_keys=ON")
            
            cursor.close()
    
    elif is_postgresql:
        @event.listens_for(engine, "connect")
        def set_postgresql_optimizations(dbapi_connection, connection_record):
            """Set PostgreSQL optimizations"""
            cursor = dbapi_connection.cursor()
            
            # Set optimizations
            cursor.execute("SET statement_timeout = '30s'")
            cursor.execute("SET lock_timeout = '10s'")
            cursor.execute("SET idle_in_transaction_session_timeout = '60s'")
            
            cursor.close()
    
    logger.info(f"Optimized database engine created: {database_url.split('@')[0]}@***")
    return engine

def create_session_factory(engine: Engine) -> sessionmaker:
    """
    Create optimized session factory
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        Configured session factory
    """
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False  # Keep objects usable after commit
    )

# Create optimized database components
database_url = settings.get_database_url()
engine = create_optimized_engine(database_url)
SessionLocal = create_session_factory(engine)

# Thread-local scoped session for multi-threading scenarios
ScopedSession = scoped_session(SessionLocal)

Base = declarative_base()

# Connection management utilities
class DatabaseConnection:
    """Context manager for database connections with automatic cleanup"""
    
    def __init__(self, session_factory: sessionmaker = SessionLocal):
        self.session_factory = session_factory
        self.session: Optional[Session] = None
    
    def __enter__(self) -> Session:
        self.session = self.session_factory()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type:
                self.session.rollback()
            self.session.close()

@contextmanager
def get_db_connection() -> Generator[Session, None, None]:
    """
    Context manager for database connections
    
    Yields:
        Database session with automatic cleanup
        
    Usage:
        with get_db_connection() as db:
            user = db.query(User).first()
    """
    with DatabaseConnection() as session:
        yield session

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions
    
    Yields:
        Database session with automatic cleanup
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()

class QueryOptimizer:
    """
    Query optimization utilities
    """
    
    @staticmethod
    def optimize_query_for_pagination(query, page: int = 1, page_size: int = 50):
        """
        Optimize query for pagination
        
        Args:
            query: SQLAlchemy query
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Optimized query with limit and offset
        """
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size)
    
    @staticmethod
    def add_query_timeout(session: Session, timeout_seconds: int = 30):
        """
        Add query timeout to session
        
        Args:
            session: Database session
            timeout_seconds: Timeout in seconds
        """
        if database_url.startswith("postgresql"):
            session.execute(text(f"SET statement_timeout = '{timeout_seconds}s'"))
        elif database_url.startswith("mysql"):
            session.execute(text(f"SET SESSION max_execution_time = {timeout_seconds * 1000}"))
    
    @staticmethod
    def explain_query(session: Session, query) -> str:
        """
        Get query execution plan for optimization
        
        Args:
            session: Database session
            query: SQLAlchemy query
            
        Returns:
            Query execution plan
        """
        if database_url.startswith("postgresql"):
            explained = session.execute(text(f"EXPLAIN ANALYZE {query}")).fetchall()
        elif database_url.startswith("mysql"):
            explained = session.execute(text(f"EXPLAIN FORMAT=JSON {query}")).fetchall()
        else:
            explained = session.execute(text(f"EXPLAIN QUERY PLAN {query}")).fetchall()
        
        return str(explained)

class DatabaseHealthCheck:
    """
    Database health monitoring
    """
    
    @staticmethod
    async def check_connection_health() -> Dict[str, Any]:
        """
        Check database connection health
        
        Returns:
            Health status dictionary
        """
        health = {
            "database_connected": False,
            "connection_pool_status": "unknown",
            "query_response_time": None,
            "error": None
        }
        
        try:
            start_time = time.time()
            
            with get_db_connection() as db:
                # Simple health check query
                result = db.execute(text("SELECT 1")).fetchone()
                
                if result and result[0] == 1:
                    health["database_connected"] = True
                    health["query_response_time"] = (time.time() - start_time) * 1000  # ms
                    
                    # Check connection pool status
                    pool_status = engine.pool.status()
                    health["connection_pool_status"] = {
                        "size": engine.pool.size(),
                        "checked_in": engine.pool.checkedin(),
                        "checked_out": engine.pool.checkedout(),
                        "overflow": engine.pool.overflow(),
                        "status": pool_status
                    }
                    
        except Exception as e:
            health["error"] = str(e)
            logger.error(f"Database health check failed: {e}")
        
        return health
    
    @staticmethod
    def get_performance_metrics() -> Dict[str, Any]:
        """Get database performance metrics"""
        return db_optimizer.get_stats()

# Index management utilities
class IndexManager:
    """
    Database index management for performance optimization
    """
    
    @staticmethod
    def create_performance_indexes(session: Session):
        """
        Create performance indexes for common queries
        
        Args:
            session: Database session
        """
        # Common indexes for the social media platform
        indexes = [
            # User-related indexes
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            
            # Content-related indexes
            "CREATE INDEX IF NOT EXISTS idx_content_items_user_id ON content_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_content_items_platform ON content_items(platform)",
            "CREATE INDEX IF NOT EXISTS idx_content_items_published_at ON content_items(published_at)",
            "CREATE INDEX IF NOT EXISTS idx_content_items_status ON content_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_content_items_user_platform ON content_items(user_id, platform)",
            
            # Performance snapshots
            "CREATE INDEX IF NOT EXISTS idx_performance_content_id ON content_performance_snapshots(content_id)",
            "CREATE INDEX IF NOT EXISTS idx_performance_created_at ON content_performance_snapshots(created_at)",
            
            # Goals and metrics
            "CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)",
            
            # Research data
            "CREATE INDEX IF NOT EXISTS idx_research_user_id ON research_data(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_research_created_at ON research_data(created_at)",
            
            # User settings
            "CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id)",
            
            # Composite indexes for common query patterns
            "CREATE INDEX IF NOT EXISTS idx_content_user_platform_status ON content_items(user_id, platform, status)",
            "CREATE INDEX IF NOT EXISTS idx_content_platform_published ON content_items(platform, published_at DESC)"
        ]
        
        try:
            for index_sql in indexes:
                session.execute(text(index_sql))
            
            session.commit()
            logger.info(f"Created {len(indexes)} performance indexes")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating indexes: {e}")
            raise

# Global utilities
query_optimizer = QueryOptimizer()
health_check = DatabaseHealthCheck()
index_manager = IndexManager()

# Initialize performance indexes on startup
async def initialize_database_optimizations():
    """Initialize database optimizations"""
    try:
        with get_db_connection() as db:
            index_manager.create_performance_indexes(db)
        
        logger.info("Database optimizations initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database optimizations: {e}")