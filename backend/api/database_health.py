"""
Database Health Check API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from backend.db.database import get_db
from backend.utils.db_checks import check_critical_tables_exist, get_table_row_count
from backend.auth.dependencies import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/database", tags=["database-health"])

@router.get("/health")
async def check_database_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Check database connection and critical table status
    Public endpoint for monitoring
    """
    try:
        # Check critical tables
        table_status = check_critical_tables_exist(db)
        
        # Get row counts for existing tables
        table_counts = {}
        for table in table_status['existing']:
            count = get_table_row_count(db, table)
            if count is not None:
                table_counts[table] = count
        
        health_status = {
            "status": "healthy" if table_status['all_exist'] else "degraded",
            "database_connected": True,
            "tables": {
                "total_critical": len(table_status['existing']) + len(table_status['missing']),
                "existing": len(table_status['existing']),
                "missing": len(table_status['missing']),
                "existing_tables": table_status['existing'],
                "missing_tables": table_status['missing'],
                "row_counts": table_counts
            }
        }
        
        # Log any missing tables  
        if table_status['missing']:
            logger.warning(f"Missing critical database tables: {table_status['missing']}")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database_connected": False,
            "error": str(e),
            "tables": {
                "total_critical": 0,
                "existing": 0,
                "missing": "unknown"
            }
        }

@router.get("/schema/verify") 
async def verify_schema_integrity(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Detailed schema verification for admin users
    Requires authentication
    """
    try:
        table_status = check_critical_tables_exist(db)
        
        # Detailed table information
        detailed_info = {}
        for table in table_status['existing']:
            count = get_table_row_count(db, table)
            detailed_info[table] = {
                "exists": True,
                "row_count": count,
                "status": "ok"
            }
        
        for table in table_status['missing']:
            detailed_info[table] = {
                "exists": False,
                "row_count": None,
                "status": "missing"
            }
        
        return {
            "schema_status": "complete" if table_status['all_exist'] else "incomplete",
            "total_tables_checked": len(detailed_info),
            "missing_count": len(table_status['missing']),
            "tables": detailed_info,
            "recommendations": [
                "Run database migrations: python run_migrations.py"
            ] if table_status['missing'] else []
        }
        
    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema verification failed: {str(e)}"
        )

@router.post("/migrate")
async def trigger_migration(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Trigger database migration (admin only)
    For emergency use when migrations haven't run
    """
    try:
        # Import here to avoid circular dependencies
        from run_migrations import run_migrations
        
        logger.info(f"Manual migration triggered by user {current_user.id}")
        
        success = run_migrations(reset_db=False)
        
        if success:
            return {
                "status": "success",
                "message": "Database migrations completed successfully",
                "triggered_by": current_user.id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Migration failed - check server logs"
            )
            
    except Exception as e:
        logger.error(f"Manual migration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )