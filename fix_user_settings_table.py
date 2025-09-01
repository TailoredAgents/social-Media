#!/usr/bin/env python3
"""
Fix User Settings Table Script

This script ensures the user_settings table exists with all required columns
for the production database. It's designed to be safe to run multiple times.

Usage:
    python fix_user_settings_table.py
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, Column, Integer, String, Float, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from backend.core.config import get_settings
from backend.db.database import engine

def check_table_exists(conn, table_name):
    """Check if a table exists in the database"""
    result = conn.execute(text(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = '{table_name}'
        );
    """))
    return result.scalar()

def check_column_exists(conn, table_name, column_name):
    """Check if a column exists in a table"""
    result = conn.execute(text(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = '{table_name}'
            AND column_name = '{column_name}'
        );
    """))
    return result.scalar()

def create_user_settings_table(conn):
    """Create the user_settings table with all columns"""
    print("🔧 Creating user_settings table...")
    
    # Create the table with all columns
    conn.execute(text("""
        CREATE TABLE user_settings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            
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
            enable_autonomous_mode BOOLEAN DEFAULT false,
            timezone VARCHAR DEFAULT 'UTC',
            
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
            updated_at TIMESTAMP WITH TIME ZONE
        );
    """))
    
    # Create index
    conn.execute(text("CREATE INDEX ix_user_settings_id ON user_settings (id);"))
    
    conn.commit()
    print("✅ user_settings table created successfully")

def add_missing_columns(conn):
    """Add any missing columns to existing user_settings table"""
    print("🔧 Checking for missing columns in user_settings table...")
    
    # Define all columns that should exist
    required_columns = [
        ('brand_name', 'VARCHAR'),
        ('brand_voice', 'VARCHAR DEFAULT \'professional\''),
        ('primary_color', 'VARCHAR DEFAULT \'#3b82f6\''),
        ('logo_url', 'VARCHAR'),
        ('content_frequency', 'INTEGER DEFAULT 3'),
        ('preferred_platforms', 'JSON'),
        ('posting_times', 'JSON'),
        ('creativity_level', 'FLOAT DEFAULT 0.7'),
        ('enable_images', 'BOOLEAN DEFAULT true'),
        ('enable_repurposing', 'BOOLEAN DEFAULT true'),
        ('enable_autonomous_mode', 'BOOLEAN DEFAULT false'),
        ('timezone', 'VARCHAR DEFAULT \'UTC\''),
        ('connected_accounts', 'JSON'),
        ('default_response_personality', 'VARCHAR DEFAULT \'professional\''),
        ('auto_response_enabled', 'BOOLEAN DEFAULT false'),
        ('auto_response_confidence_threshold', 'FLOAT DEFAULT 0.8'),
        ('auto_response_business_hours_only', 'BOOLEAN DEFAULT true'),
        ('auto_response_delay_minutes', 'INTEGER DEFAULT 5'),
        ('business_hours_start', 'VARCHAR DEFAULT \'09:00\''),
        ('business_hours_end', 'VARCHAR DEFAULT \'17:00\''),
        ('business_days', 'JSON'),
        ('escalation_keywords', 'JSON'),
        ('excluded_response_keywords', 'JSON'),
        ('created_at', 'TIMESTAMP WITH TIME ZONE DEFAULT now()'),
        ('updated_at', 'TIMESTAMP WITH TIME ZONE'),
    ]
    
    missing_columns = []
    for column_name, column_type in required_columns:
        if not check_column_exists(conn, 'user_settings', column_name):
            missing_columns.append((column_name, column_type))
    
    if missing_columns:
        print(f"Found {len(missing_columns)} missing columns: {[col[0] for col in missing_columns]}")
        
        for column_name, column_type in missing_columns:
            try:
                print(f"Adding column: {column_name}")
                conn.execute(text(f"ALTER TABLE user_settings ADD COLUMN {column_name} {column_type};"))
            except Exception as e:
                print(f"Warning: Could not add column {column_name}: {e}")
        
        # Set default JSON values for specific columns
        json_defaults = [
            ('preferred_platforms', '["twitter", "instagram"]'),
            ('posting_times', '{"twitter": "09:00", "instagram": "10:00"}'),
            ('business_days', '["monday", "tuesday", "wednesday", "thursday", "friday"]'),
            ('escalation_keywords', '["complaint", "lawsuit", "refund", "angry", "terrible"]'),
            ('excluded_response_keywords', '["spam", "bot", "fake"]'),
        ]
        
        for column_name, default_value in json_defaults:
            try:
                conn.execute(text(f"""
                    UPDATE user_settings 
                    SET {column_name} = '{default_value}'::json 
                    WHERE {column_name} IS NULL
                """))
            except Exception as e:
                print(f"Warning: Could not set default for {column_name}: {e}")
        
        conn.commit()
        print("✅ Missing columns added successfully")
    else:
        print("✅ All required columns already exist")

def fix_user_settings_table():
    """Main function to fix the user_settings table"""
    
    settings = get_settings()
    print("🔧 User Settings Table Fix Script")
    print(f"Database URL: {settings.database_url}")
    print("-" * 50)
    
    try:
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Check if user_settings table exists
            if check_table_exists(conn, 'user_settings'):
                print("✅ user_settings table exists")
                add_missing_columns(conn)
            else:
                print("❌ user_settings table does not exist")
                create_user_settings_table(conn)
            
            # Final verification
            print("\n🔍 Final verification...")
            result = conn.execute(text("SELECT COUNT(*) FROM user_settings"))
            count = result.scalar()
            print(f"✅ user_settings table accessible with {count} rows")
            
            print("\n🎉 User settings table fix completed successfully!")
            return True
    
    except Exception as e:
        print(f"❌ Error fixing user_settings table: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point"""
    success = fix_user_settings_table()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()