#!/usr/bin/env python3
"""
Production database fix: Add missing industry preset columns to user_settings table.
Run this script to fix the database schema mismatch causing 500 errors.

Usage: python fix_user_settings_columns.py
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from core.config import get_settings
except ImportError:
    # Fallback for production environment
    import os
    from pydantic_settings import BaseSettings
    
    class Settings(BaseSettings):
        database_url: str = os.getenv('DATABASE_URL', 'postgresql://localhost/socialmedia')
        
    def get_settings():
        return Settings()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_production_database():
    """Add missing industry preset columns to production PostgreSQL database"""
    try:
        settings = get_settings()
        engine = create_engine(settings.database_url)
        
        # List of columns to add with their PostgreSQL types and defaults
        new_columns = [
            ('secondary_color', 'VARCHAR(50)', "'#10b981'"),
            ('industry_type', 'VARCHAR(100)', "'general'"),
            ('visual_style', 'VARCHAR(100)', "'modern'"),
            ('image_mood', 'JSON', "'[\"professional\", \"clean\"]'"),
            ('brand_keywords', 'JSON', "'[]'"),
            ('avoid_list', 'JSON', "'[]'"),
            ('enable_auto_image_generation', 'BOOLEAN', 'true'),
            ('preferred_image_style', 'JSON', '\'{"lighting": "natural", "composition": "rule_of_thirds", "color_temperature": "neutral"}\''),
            ('custom_image_prompts', 'JSON', "'{}'"),
            ('image_quality', 'VARCHAR(50)', "'high'"),
            ('image_aspect_ratio', 'VARCHAR(20)', "'1:1'"),
        ]
        
        with engine.connect() as conn:
            # Check if user_settings table exists
            table_check = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user_settings'
                );
            """)).scalar()
            
            if not table_check:
                logger.error("❌ user_settings table does not exist!")
                return False
            
            logger.info("✅ user_settings table found")
            
            # Add each missing column
            for column_name, column_type, default_value in new_columns:
                try:
                    # Check if column already exists
                    column_exists = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'user_settings' 
                            AND column_name = :column_name
                        );
                    """), {"column_name": column_name}).scalar()
                    
                    if not column_exists:
                        # Add the column
                        alter_sql = f"""
                            ALTER TABLE user_settings 
                            ADD COLUMN {column_name} {column_type} DEFAULT {default_value};
                        """
                        conn.execute(text(alter_sql))
                        conn.commit()
                        logger.info(f"✅ Added column: {column_name}")
                    else:
                        logger.info(f"⚠️  Column {column_name} already exists, skipping")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to add column {column_name}: {e}")
                    conn.rollback()
                    return False
            
            # Verify all columns were added
            logger.info("🔍 Verifying all columns exist...")
            existing_columns = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'user_settings'
                ORDER BY column_name;
            """)).fetchall()
            
            existing_column_names = [row[0] for row in existing_columns]
            missing_columns = []
            
            for column_name, _, _ in new_columns:
                if column_name not in existing_column_names:
                    missing_columns.append(column_name)
            
            if missing_columns:
                logger.error(f"❌ Still missing columns: {missing_columns}")
                return False
            else:
                logger.info("✅ All industry preset columns verified!")
            
            logger.info("🎉 Production database schema fix completed!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Database fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🔧 Starting production database schema fix for user_settings...")
    logger.info("This will add missing industry preset columns to fix 500 errors")
    
    success = fix_production_database()
    if success:
        logger.info("✅ Database fix completed successfully!")
        logger.info("The user settings API should now work without errors.")
        logger.info("You should now be able to see the frontend changes!")
        sys.exit(0)
    else:
        logger.error("❌ Database fix failed!")
        sys.exit(1)