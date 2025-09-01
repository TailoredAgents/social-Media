#!/usr/bin/env python3
"""
Database migration to add Industry Style Presets & Brand Parameters to user_settings table
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from sqlalchemy import create_engine, text
from backend.core.config import get_settings
from backend.db.database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_image_preset_columns():
    """Add industry presets and brand parameters columns to user_settings table"""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    
    # Detect database type
    is_sqlite = "sqlite" in settings.database_url.lower()
    
    # List of columns to add
    if is_sqlite:
        new_columns = [
            ('secondary_color', 'VARCHAR', "'#10b981'"),
            ('industry_type', 'VARCHAR', "'general'"),
            ('visual_style', 'VARCHAR', "'modern'"),
            ('image_mood', 'TEXT', "'[\"professional\", \"clean\"]'"),  # SQLite uses TEXT for JSON
            ('brand_keywords', 'TEXT', "'[]'"),
            ('avoid_list', 'TEXT', "'[]'"),
            ('enable_auto_image_generation', 'BOOLEAN', '1'),  # SQLite uses 1/0 for boolean
            ('preferred_image_style', 'TEXT', "'{\"lighting\": \"natural\", \"composition\": \"rule_of_thirds\", \"color_temperature\": \"neutral\"}'"),
            ('custom_image_prompts', 'TEXT', "'{}'"),
            ('image_quality', 'VARCHAR', "'high'"),
            ('image_aspect_ratio', 'VARCHAR', "'1:1'"),
        ]
    else:
        new_columns = [
            ('secondary_color', 'VARCHAR', "'#10b981'"),
            ('industry_type', 'VARCHAR', "'general'"),
            ('visual_style', 'VARCHAR', "'modern'"),
            ('image_mood', 'JSON', "'[\"professional\", \"clean\"]'"),
            ('brand_keywords', 'JSON', "'[]'"),
            ('avoid_list', 'JSON', "'[]'"),
            ('enable_auto_image_generation', 'BOOLEAN', 'true'),
            ('preferred_image_style', 'JSON', "'{\"lighting\": \"natural\", \"composition\": \"rule_of_thirds\", \"color_temperature\": \"neutral\"}'"),
            ('custom_image_prompts', 'JSON', "'{}'"),
            ('image_quality', 'VARCHAR', "'high'"),
            ('image_aspect_ratio', 'VARCHAR', "'1:1'"),
        ]
    
    try:
        with engine.connect() as conn:
            # Check if user_settings table exists (database-specific)
            if is_sqlite:
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='user_settings';
                """)).fetchone()
                table_exists = result is not None
            else:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'user_settings'
                    );
                """)).scalar()
                table_exists = result
            
            if not table_exists:
                logger.error("user_settings table does not exist!")
                return
                
            logger.info(f"Adding industry preset and brand parameter columns... (Database: {'SQLite' if is_sqlite else 'PostgreSQL'})")
            
            for column_name, column_type, default_value in new_columns:
                try:
                    # Check if column already exists (database-specific)
                    if is_sqlite:
                        column_info = conn.execute(text(f"PRAGMA table_info(user_settings)")).fetchall()
                        column_exists = any(col[1] == column_name for col in column_info)
                    else:
                        column_exists = conn.execute(text(f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns 
                                WHERE table_name = 'user_settings' 
                                AND column_name = '{column_name}'
                            );
                        """)).scalar()
                    
                    if not column_exists:
                        # Add the column
                        conn.execute(text(f"""
                            ALTER TABLE user_settings 
                            ADD COLUMN {column_name} {column_type} DEFAULT {default_value};
                        """))
                        conn.commit()
                        logger.info(f"✅ Added column: {column_name}")
                    else:
                        logger.info(f"⚠️ Column {column_name} already exists, skipping")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to add column {column_name}: {e}")
                    conn.rollback()
                    
            logger.info("🎉 Industry preset columns migration completed!")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    add_image_preset_columns()