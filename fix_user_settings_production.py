#!/usr/bin/env python3
"""
Script to fix the missing user_settings table in production.
This should be run on the production server where the database is accessible.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.orm import sessionmaker

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from core.config import get_settings
from db.models import Base, UserSettings, User

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_user_settings_table():
    """Create the user_settings table if it doesn't exist"""
    try:
        settings = get_settings()
        
        # Create engine
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False
        )
        
        # Check if table exists
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        logger.info(f"Existing tables: {existing_tables}")
        
        if 'user_settings' not in existing_tables:
            logger.info("user_settings table not found. Creating it...")
            
            # Create only the UserSettings table
            UserSettings.__table__.create(engine, checkfirst=True)
            logger.info("✅ user_settings table created successfully!")
            
            # Create a session to add default settings for existing users
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                # Get all users without settings
                users_without_settings = session.query(User).outerjoin(UserSettings).filter(UserSettings.id == None).all()
                
                logger.info(f"Found {len(users_without_settings)} users without settings")
                
                # Create default settings for each user
                for user in users_without_settings:
                    user_setting = UserSettings(
                        user_id=user.id,
                        brand_voice='professional',
                        primary_color='#3b82f6',
                        content_frequency=3,
                        preferred_platforms=['twitter', 'instagram'],
                        posting_times={'twitter': '09:00', 'instagram': '10:00'},
                        creativity_level=0.7,
                        enable_images=True,
                        enable_repurposing=True,
                        enable_autonomous_mode=False,
                        timezone='UTC',
                        default_response_personality='professional',
                        auto_response_enabled=False,
                        auto_response_confidence_threshold=0.8,
                        auto_response_business_hours_only=True,
                        auto_response_delay_minutes=5,
                        business_hours_start='09:00',
                        business_hours_end='17:00',
                        business_days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
                        escalation_keywords=['complaint', 'lawsuit', 'refund', 'angry', 'terrible'],
                        excluded_response_keywords=['spam', 'bot', 'fake']
                    )
                    session.add(user_setting)
                
                session.commit()
                logger.info(f"✅ Created default settings for {len(users_without_settings)} users")
                
            except Exception as e:
                logger.error(f"Error creating default user settings: {e}")
                session.rollback()
            finally:
                session.close()
                
        else:
            logger.info("user_settings table already exists")
            
            # Verify the table has all required columns
            columns = [col['name'] for col in inspector.get_columns('user_settings')]
            required_columns = [
                'id', 'user_id', 'brand_name', 'brand_voice', 'primary_color', 'logo_url',
                'content_frequency', 'preferred_platforms', 'posting_times', 'creativity_level',
                'enable_images', 'enable_repurposing', 'enable_autonomous_mode', 'timezone',
                'connected_accounts', 'default_response_personality', 'auto_response_enabled',
                'auto_response_confidence_threshold', 'auto_response_business_hours_only',
                'auto_response_delay_minutes', 'business_hours_start', 'business_hours_end',
                'business_days', 'escalation_keywords', 'excluded_response_keywords',
                'created_at', 'updated_at'
            ]
            
            missing_columns = [col for col in required_columns if col not in columns]
            if missing_columns:
                logger.warning(f"Missing columns: {missing_columns}")
                logger.info("Consider running the full migration: alembic upgrade head")
            else:
                logger.info("✅ user_settings table has all required columns")
        
        # Test the table by trying to query it
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            count = session.query(UserSettings).count()
            logger.info(f"✅ user_settings table working correctly. Found {count} records.")
        except Exception as e:
            logger.error(f"Error querying user_settings table: {e}")
        finally:
            session.close()
            
        return True
        
    except Exception as e:
        logger.error(f"Error creating user_settings table: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔧 Starting user_settings table fix...")
    success = create_user_settings_table()
    if success:
        logger.info("✅ user_settings table fix completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ user_settings table fix failed!")
        sys.exit(1)