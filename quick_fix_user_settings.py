#!/usr/bin/env python3
"""
Quick fix for user_settings table - single command to run on production
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text
from core.config import get_settings

def quick_fix():
    settings = get_settings()
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Check if table exists
        exists = conn.execute(text("""
            SELECT EXISTS (SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'user_settings');
        """)).scalar()
        
        if not exists:
            print("Creating user_settings table...")
            conn.execute(text("""
                CREATE TABLE user_settings (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    brand_name VARCHAR,
                    brand_voice VARCHAR DEFAULT 'professional',
                    primary_color VARCHAR DEFAULT '#3b82f6',
                    logo_url VARCHAR,
                    content_frequency INTEGER DEFAULT 3,
                    preferred_platforms JSON DEFAULT '["twitter", "instagram"]',
                    posting_times JSON DEFAULT '{"twitter": "09:00", "instagram": "10:00"}',
                    creativity_level FLOAT DEFAULT 0.7,
                    enable_images BOOLEAN DEFAULT true,
                    enable_repurposing BOOLEAN DEFAULT true,
                    enable_autonomous_mode BOOLEAN DEFAULT false,
                    timezone VARCHAR DEFAULT 'UTC',
                    connected_accounts JSON,
                    default_response_personality VARCHAR DEFAULT 'professional',
                    auto_response_enabled BOOLEAN DEFAULT false,
                    auto_response_confidence_threshold FLOAT DEFAULT 0.8,
                    auto_response_business_hours_only BOOLEAN DEFAULT true,
                    auto_response_delay_minutes INTEGER DEFAULT 5,
                    business_hours_start VARCHAR DEFAULT '09:00',
                    business_hours_end VARCHAR DEFAULT '17:00',
                    business_days JSON DEFAULT '["monday", "tuesday", "wednesday", "thursday", "friday"]',
                    escalation_keywords JSON DEFAULT '["complaint", "lawsuit", "refund", "angry", "terrible"]',
                    excluded_response_keywords JSON DEFAULT '["spam", "bot", "fake"]',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE
                );
                CREATE INDEX ix_user_settings_id ON user_settings (id);
            """))
            conn.commit()
            print("✅ user_settings table created!")
        else:
            print("Table already exists")
        
        count = conn.execute(text("SELECT COUNT(*) FROM user_settings")).scalar()
        print(f"Table has {count} records")

if __name__ == "__main__":
    quick_fix()