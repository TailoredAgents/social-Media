#!/usr/bin/env python3
"""
Database Migration Script
Run this before deployment to update database schema
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_migrations():
    """Run Alembic database migrations"""
    logger.info("Starting database migrations...")
    
    try:
        # Run Alembic migrations
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], capture_output=True, text=True, cwd=str(project_root))
        
        if result.returncode == 0:
            logger.info("✅ Database migrations completed successfully")
            if result.stdout:
                logger.info(f"Migration output: {result.stdout}")
            return True
        else:
            logger.error(f"❌ Migration failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Migration errors: {result.stderr}")
            if result.stdout:
                logger.info(f"Migration output: {result.stdout}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to run migrations: {e}")
        return False

def run_schema_safety_net():
    """Run schema safety net to ensure critical tables exist"""
    logger.info("Running database schema safety net...")
    
    try:
        from backend.db.ensure_columns import (
            ensure_user_columns, 
            ensure_notifications_table, 
            ensure_content_logs_table, 
            ensure_social_inbox_tables
        )
        
        ensure_user_columns()
        ensure_notifications_table()
        ensure_content_logs_table()
        ensure_social_inbox_tables()
        
        logger.info("✅ Schema safety net completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema safety net failed: {e}")
        return False

def main():
    """Main migration process"""
    logger.info("=" * 60)
    logger.info("DATABASE MIGRATION SCRIPT")
    logger.info("=" * 60)
    
    # Check if we're in production
    environment = os.getenv("ENVIRONMENT", "development")
    render_env = os.getenv("RENDER")
    is_production = environment == "production" or bool(render_env)
    
    logger.info(f"Environment: {environment}")
    logger.info(f"Render deployment: {'Yes' if render_env else 'No'}")
    logger.info(f"Running in production mode: {is_production}")
    
    success = True
    
    # Run migrations
    if not run_migrations():
        success = False
        logger.warning("Migrations failed, but continuing with schema safety net...")
    
    # Run schema safety net
    if not run_schema_safety_net():
        success = False
        logger.warning("Schema safety net failed")
    
    # Final status
    logger.info("=" * 60)
    if success:
        logger.info("✅ DATABASE MIGRATION COMPLETED SUCCESSFULLY")
        sys.exit(0)
    else:
        logger.error("❌ DATABASE MIGRATION COMPLETED WITH ERRORS")
        logger.error("Please check the logs above and fix any issues")
        sys.exit(1)

if __name__ == "__main__":
    main()