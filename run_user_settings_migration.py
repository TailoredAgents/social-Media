#!/usr/bin/env python3
"""
Run the specific user_settings migration on production.
This executes the exact same logic as migration 022.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from core.config import get_settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_user_settings_migration():
    """Run the user_settings migration manually"""
    try:
        settings = get_settings()
        
        # Create engine
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=True  # Show SQL commands
        )
        
        with engine.connect() as conn:
            # Check if user_settings table exists
            table_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_settings'
                );
            """)).scalar()
            
            if not table_exists:
                logger.info("Creating user_settings table from scratch...")
                
                # Create the complete user_settings table
                conn.execute(text("""
                    CREATE TABLE user_settings (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        
                        -- Brand settings
                        brand_name VARCHAR,
                        brand_voice VARCHAR DEFAULT 'professional',
                        primary_color VARCHAR DEFAULT '#3b82f6',
                        logo_url VARCHAR,
                        
                        -- Content preferences
                        content_frequency INTEGER DEFAULT 3,
                        preferred_platforms JSON DEFAULT '["twitter", "instagram"]'::json,
                        posting_times JSON DEFAULT '{"twitter": "09:00", "instagram": "10:00"}'::json,
                        
                        -- AI settings
                        creativity_level FLOAT DEFAULT 0.7,
                        enable_images BOOLEAN DEFAULT true,
                        enable_repurposing BOOLEAN DEFAULT true,
                        enable_autonomous_mode BOOLEAN NOT NULL DEFAULT false,
                        timezone VARCHAR NOT NULL DEFAULT 'UTC',
                        
                        -- Integrations
                        connected_accounts JSON,
                        
                        -- Social Inbox Settings
                        default_response_personality VARCHAR DEFAULT 'professional',
                        auto_response_enabled BOOLEAN DEFAULT false,
                        auto_response_confidence_threshold FLOAT DEFAULT 0.8,
                        auto_response_business_hours_only BOOLEAN DEFAULT true,
                        auto_response_delay_minutes INTEGER DEFAULT 5,
                        business_hours_start VARCHAR DEFAULT '09:00',
                        business_hours_end VARCHAR DEFAULT '17:00',
                        business_days JSON DEFAULT '["monday", "tuesday", "wednesday", "thursday", "friday"]'::json,
                        escalation_keywords JSON DEFAULT '["complaint", "lawsuit", "refund", "angry", "terrible"]'::json,
                        excluded_response_keywords JSON DEFAULT '["spam", "bot", "fake"]'::json,
                        
                        -- Timestamps
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                        updated_at TIMESTAMP WITH TIME ZONE,
                        
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    );
                """))
                
                # Create index
                conn.execute(text("CREATE INDEX ix_user_settings_id ON user_settings (id);"))
                
                logger.info("✅ user_settings table created successfully!")
                
            else:
                logger.info("user_settings table exists, checking for missing columns...")
                
                # List of columns to check/add
                columns_to_check = [
                    ('enable_autonomous_mode', 'BOOLEAN', 'false'),
                    ('timezone', 'VARCHAR', "'UTC'"),
                    ('default_response_personality', 'VARCHAR', "'professional'"),
                    ('auto_response_enabled', 'BOOLEAN', 'false'),
                    ('auto_response_confidence_threshold', 'FLOAT', '0.8'),
                    ('auto_response_business_hours_only', 'BOOLEAN', 'true'),
                    ('auto_response_delay_minutes', 'INTEGER', '5'),
                    ('business_hours_start', 'VARCHAR', "'09:00'"),
                    ('business_hours_end', 'VARCHAR', "'17:00'"),
                    ('business_days', 'JSON', None),
                    ('escalation_keywords', 'JSON', None),
                    ('excluded_response_keywords', 'JSON', None),
                ]
                
                for column_name, column_type, default_value in columns_to_check:
                    # Check if column exists
                    column_exists = conn.execute(text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = 'user_settings'
                            AND column_name = '{column_name}'
                        );
                    """)).scalar()
                    
                    if not column_exists:
                        logger.info(f"Adding missing column: {column_name}")
                        if default_value:
                            conn.execute(text(f"ALTER TABLE user_settings ADD COLUMN {column_name} {column_type} DEFAULT {default_value};"))
                        else:
                            conn.execute(text(f"ALTER TABLE user_settings ADD COLUMN {column_name} {column_type};"))
                
                # Set JSON defaults for new columns
                try:
                    conn.execute(text("""
                        UPDATE user_settings SET 
                            business_days = '["monday", "tuesday", "wednesday", "thursday", "friday"]'::json
                        WHERE business_days IS NULL
                    """))
                    conn.execute(text("""
                        UPDATE user_settings SET 
                            escalation_keywords = '["complaint", "lawsuit", "refund", "angry", "terrible"]'::json
                        WHERE escalation_keywords IS NULL
                    """))
                    conn.execute(text("""
                        UPDATE user_settings SET 
                            excluded_response_keywords = '["spam", "bot", "fake"]'::json
                        WHERE excluded_response_keywords IS NULL
                    """))
                    logger.info("✅ Updated JSON column defaults")
                except Exception as e:
                    logger.warning(f"Could not update JSON defaults: {e}")
            
            # Commit the transaction
            conn.commit()
            
            # Test the table
            result = conn.execute(text("SELECT COUNT(*) FROM user_settings")).scalar()
            logger.info(f"✅ user_settings table working. Found {result} records.")
            
            return True
            
    except Exception as e:
        logger.error(f"Error running user_settings migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🔧 Running user_settings migration...")
    success = run_user_settings_migration()
    if success:
        logger.info("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Migration failed!")
        sys.exit(1)