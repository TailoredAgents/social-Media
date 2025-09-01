#!/usr/bin/env python3
"""
Database Migration Script

This script initializes the database and runs all Alembic migrations
to bring the database schema up to the latest version.

Usage:
    python run_migrations.py [--reset]
    
Options:
    --reset  Drop all tables and recreate from scratch
"""

import sys
import os
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.core.config import get_settings
from backend.db.database import Base, engine
from backend.db.models import *  # Import all models

def run_migrations(reset_db=False):
    """Run database migrations"""
    
    settings = get_settings()
    
    print("🔧 Database Migration Script")
    print(f"Database URL: {settings.database_url}")
    print(f"Reset Database: {reset_db}")
    print("-" * 50)
    
    try:
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
    
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    if reset_db:
        print("🗑️  Dropping all tables...")
        try:
            # Drop all tables
            Base.metadata.drop_all(bind=engine)
            print("✅ All tables dropped")
            
            # Drop alembic_version table to reset migration history
            with engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
                conn.commit()
            print("✅ Migration history reset")
            
        except Exception as e:
            print(f"❌ Error dropping tables: {e}")
            return False
    
    # Run Alembic migrations
    try:
        print("🔄 Running Alembic migrations...")
        
        # Set up Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Get current revision
        try:
            current_rev = command.current(alembic_cfg)
            print(f"📍 Current database revision: {current_rev}")
        except Exception:
            print("📍 No current database revision (new database)")
        
        # Upgrade to head
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations completed successfully")
        
        # Show final revision
        final_rev = command.current(alembic_cfg)
        print(f"📍 Final database revision: {final_rev}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    # Verify table creation
    try:
        print("🔍 Verifying table creation...")
        
        with engine.connect() as conn:
            # Check if key tables exist
            tables_to_check = [
                'users', 'user_settings', 'goals', 'goal_progress', 'milestones',
                'memory_content', 'memories', 'notifications',
                'content_items', 'content_performance_snapshots',
                'content_logs', 'metrics', 'refresh_token_blacklist'
            ]
            
            existing_tables = []
            missing_tables = []
            
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    existing_tables.append(table)
                except Exception:
                    missing_tables.append(table)
            
            print(f"✅ Existing tables ({len(existing_tables)}): {', '.join(existing_tables)}")
            if missing_tables:
                print(f"⚠️  Missing tables ({len(missing_tables)}): {', '.join(missing_tables)}")
            else:
                print("✅ All expected tables exist")
                
    except Exception as e:
        print(f"❌ Table verification failed: {e}")
        return False
    
    print("\n🎉 Database migration completed successfully!")
    print("The database is now ready for use.")
    
    return True

def show_migration_history():
    """Show migration history"""
    try:
        alembic_cfg = Config("alembic.ini")
        command.history(alembic_cfg)
    except Exception as e:
        print(f"❌ Failed to show migration history: {e}")

def main():
    parser = argparse.ArgumentParser(description="Database Migration Script")
    parser.add_argument("--reset", action="store_true", 
                       help="Drop all tables and recreate from scratch")
    parser.add_argument("--history", action="store_true",
                       help="Show migration history")
    
    args = parser.parse_args()
    
    if args.history:
        show_migration_history()
        return
    
    success = run_migrations(reset_db=args.reset)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()