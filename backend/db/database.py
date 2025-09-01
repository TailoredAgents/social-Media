from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging
from fastapi import HTTPException
from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# POSTGRESQL ONLY - NO SQLITE
database_url = settings.get_database_url()

# Reject SQLite completely
if database_url.startswith("sqlite"):
    raise ValueError("SQLite is not supported! This application requires PostgreSQL.")

logger.info(f"Using PostgreSQL database: {database_url.replace('BbsIYQtjBnhKwRL3F9kXbv1wrtsVxuTg', '***')}")

# PostgreSQL production settings ONLY
engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=20,  # Maximum number of persistent connections in the pool
    max_overflow=30,  # Maximum number of connections that can overflow the pool
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,  # Recycle connections every hour
    echo=False,  # Set to True for query debugging
    connect_args={
        "connect_timeout": 10,
        "application_name": "ai_social_media_agent"
    }
    )

# Add connection pool event listeners for monitoring
@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Log database connections"""
    logger.debug("Database connection established")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection checkout from pool"""
    logger.debug("Connection checked out from pool")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection checkin to pool"""
    logger.debug("Connection checked in to pool")

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Prevent lazy loading issues
)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Database dependency that provides a database session with enhanced error handling.
    
    Features:
    - Automatic transaction rollback on errors
    - Connection pool monitoring
    - Query performance logging
    """
    db = SessionLocal()
    try:
        yield db
        # Commit any pending transactions
        db.commit()
    except Exception as e:
        # Rollback on any exception
        db.rollback()
        
        # Filter out expected authentication 401s from database error logs
        if isinstance(e, HTTPException) and e.status_code == 401:
            # This is an expected authentication error, don't log as database error
            raise
        
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        db.close()

def get_db_connection_info():
    """Get current database connection pool information"""
    try:
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_out_connections": pool.checkedout(),
            "checked_in_connections": pool.checkedin(),
            "invalid_connections": pool.invalidated(),
            "overflow_connections": pool.overflow() if hasattr(pool, 'overflow') else 0,
            "total_connections": pool.size() + (pool.overflow() if hasattr(pool, 'overflow') else 0),
            "database_url_scheme": database_url.split("://")[0] if "://" in database_url else "unknown"
        }
    except Exception as e:
        logger.error(f"Error getting connection pool info: {str(e)}")
        return {"error": str(e)}

def health_check_database():
    """Perform a database health check"""
    try:
        with engine.connect() as connection:
            # Test basic query
            result = connection.execute("SELECT 1")
            result.fetchone()
            
            # Get connection pool info
            pool_info = get_db_connection_info()
            
            return {
                "status": "healthy",
                "connection_test": "passed",
                "pool_info": pool_info
            }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "connection_test": "failed"
        }