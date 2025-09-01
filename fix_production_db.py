#!/usr/bin/env python3
"""
Script to fix production database by creating missing social inbox tables
Run this with: python fix_production_db.py "your-database-url-here"
"""

import sys
import os
from sqlalchemy import create_engine, text
from urllib.parse import urlparse, urlunparse

def fix_database_url(db_url):
    """Fix the database URL to ensure it works correctly"""
    # Parse the URL
    parsed = urlparse(db_url)
    
    # If it's a postgres:// URL, change it to postgresql://
    if parsed.scheme == 'postgres':
        parsed = parsed._replace(scheme='postgresql')
    
    # Reconstruct the URL
    return urlunparse(parsed)

def create_social_inbox_tables(db_url):
    """Create all missing social inbox tables"""
    
    # Fix the database URL format
    db_url = fix_database_url(db_url)
    
    print(f"Connecting to database...")
    
    try:
        # Create engine with the production database URL
        engine = create_engine(db_url)
        
        # SQL to create all social inbox tables
        sql_script = """
        -- Create social_platform_connections table first (if it doesn't exist)
        CREATE TABLE IF NOT EXISTS social_platform_connections (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            platform VARCHAR(50) NOT NULL,
            platform_user_id VARCHAR(255),
            access_token TEXT,
            refresh_token TEXT,
            token_expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, platform)
        );

        -- Create social_interactions table
        CREATE TABLE IF NOT EXISTS social_interactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            connection_id INTEGER REFERENCES social_platform_connections(id),
            platform VARCHAR(50) NOT NULL,
            interaction_type VARCHAR(50) NOT NULL,
            external_id VARCHAR(255) UNIQUE,
            parent_external_id VARCHAR(255),
            author_platform_id VARCHAR(255),
            author_username VARCHAR(255) NOT NULL,
            author_display_name VARCHAR(255),
            author_profile_url TEXT,
            author_profile_image TEXT,
            author_verified BOOLEAN DEFAULT FALSE,
            content TEXT NOT NULL,
            media_urls TEXT[],
            hashtags TEXT[],
            mentions TEXT[],
            sentiment VARCHAR(50),
            intent VARCHAR(50),
            priority_score INTEGER DEFAULT 0,
            status VARCHAR(50) DEFAULT 'unread',
            response_strategy VARCHAR(100),
            assigned_to INTEGER,
            platform_metadata JSONB,
            platform_created_at TIMESTAMP,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indexes for social_interactions
        CREATE INDEX IF NOT EXISTS idx_social_interactions_user_id ON social_interactions(user_id);
        CREATE INDEX IF NOT EXISTS idx_social_interactions_status ON social_interactions(status);
        CREATE INDEX IF NOT EXISTS idx_social_interactions_platform ON social_interactions(platform);
        CREATE INDEX IF NOT EXISTS idx_social_interactions_priority ON social_interactions(priority_score DESC);
        CREATE INDEX IF NOT EXISTS idx_social_interactions_received_at ON social_interactions(received_at DESC);

        -- Create social_responses table
        CREATE TABLE IF NOT EXISTS social_responses (
            id SERIAL PRIMARY KEY,
            interaction_id INTEGER NOT NULL REFERENCES social_interactions(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id),
            response_text TEXT NOT NULL,
            response_type VARCHAR(50),
            ai_generated BOOLEAN DEFAULT FALSE,
            ai_confidence FLOAT,
            template_id INTEGER,
            sent_at TIMESTAMP,
            platform_response_id VARCHAR(255),
            platform_response_data JSONB,
            status VARCHAR(50) DEFAULT 'draft',
            approved_by INTEGER,
            approved_at TIMESTAMP,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indexes for social_responses
        CREATE INDEX IF NOT EXISTS idx_social_responses_interaction_id ON social_responses(interaction_id);
        CREATE INDEX IF NOT EXISTS idx_social_responses_user_id ON social_responses(user_id);
        CREATE INDEX IF NOT EXISTS idx_social_responses_status ON social_responses(status);

        -- Create response_templates table
        CREATE TABLE IF NOT EXISTS response_templates (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            intent_type VARCHAR(100),
            template_text TEXT NOT NULL,
            variables JSONB,
            usage_count INTEGER DEFAULT 0,
            success_rate FLOAT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indexes for response_templates
        CREATE INDEX IF NOT EXISTS idx_response_templates_user_id ON response_templates(user_id);
        CREATE INDEX IF NOT EXISTS idx_response_templates_category ON response_templates(category);
        CREATE INDEX IF NOT EXISTS idx_response_templates_intent ON response_templates(intent_type);

        -- Create knowledge_base_entries table
        CREATE TABLE IF NOT EXISTS knowledge_base_entries (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category VARCHAR(100),
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            keywords TEXT[],
            usage_count INTEGER DEFAULT 0,
            is_public BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indexes for knowledge_base_entries
        CREATE INDEX IF NOT EXISTS idx_knowledge_base_user_id ON knowledge_base_entries(user_id);
        CREATE INDEX IF NOT EXISTS idx_knowledge_base_category ON knowledge_base_entries(category);
        CREATE INDEX IF NOT EXISTS idx_knowledge_base_keywords ON knowledge_base_entries USING GIN(keywords);

        -- Create inbox_settings table
        CREATE TABLE IF NOT EXISTS inbox_settings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            auto_respond_enabled BOOLEAN DEFAULT FALSE,
            auto_respond_delay_minutes INTEGER DEFAULT 5,
            sentiment_filter VARCHAR(50)[],
            priority_threshold INTEGER DEFAULT 5,
            response_tone VARCHAR(50) DEFAULT 'professional',
            include_ai_disclosure BOOLEAN DEFAULT TRUE,
            max_auto_responses_per_hour INTEGER DEFAULT 10,
            business_hours_only BOOLEAN DEFAULT TRUE,
            business_hours_start TIME DEFAULT '09:00:00',
            business_hours_end TIME DEFAULT '17:00:00',
            business_days INTEGER[] DEFAULT ARRAY[1, 2, 3, 4, 5],
            timezone VARCHAR(50) DEFAULT 'UTC',
            notification_preferences JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Create index for inbox_settings
        CREATE INDEX IF NOT EXISTS idx_inbox_settings_user_id ON inbox_settings(user_id);

        -- We'll skip the triggers for now to avoid syntax issues
        
        -- Also fix the content_logs engagement_data column issue
        ALTER TABLE content_logs ADD COLUMN IF NOT EXISTS engagement_data JSONB DEFAULT '{}';
        """
        
        # Execute the SQL script
        with engine.connect() as conn:
            print("Creating social inbox tables...")
            
            # Split the script into individual statements and execute them
            statements = [s.strip() for s in sql_script.split(';') if s.strip()]
            
            for i, statement in enumerate(statements, 1):
                if statement:
                    try:
                        conn.execute(text(statement))
                        conn.commit()
                        print(f"✓ Executed statement {i}/{len(statements)}")
                    except Exception as e:
                        if "already exists" in str(e):
                            print(f"⚠️  Statement {i} - Already exists (skipping)")
                        else:
                            print(f"✗ Statement {i} failed: {e}")
                            raise
            
            # Verify tables were created
            print("\nVerifying tables...")
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN (
                    'social_interactions', 
                    'social_responses', 
                    'response_templates', 
                    'knowledge_base_entries',
                    'inbox_settings'
                )
                ORDER BY table_name;
            """))
            
            created_tables = [row[0] for row in result]
            print(f"\n✅ Successfully verified {len(created_tables)} tables:")
            for table in created_tables:
                print(f"   - {table}")
            
            # Check if engagement_data column was added
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'content_logs' 
                AND column_name = 'engagement_data';
            """))
            
            if result.fetchone():
                print("   - content_logs.engagement_data column")
                
        print("\n🎉 Database fix completed successfully!")
        print("The Social Inbox page should now load without errors.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the database URL is correct")
        print("2. Check that you have the necessary permissions")
        print("3. Ensure the database is accessible from your network")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_production_db.py <database-url>")
        print("Example: python fix_production_db.py 'postgresql://user:pass@host/dbname'")
        sys.exit(1)
    
    db_url = sys.argv[1]
    
    # You can also set it as an environment variable
    if db_url == "env":
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            print("Error: DATABASE_URL environment variable not set")
            sys.exit(1)
    
    success = create_social_inbox_tables(db_url)
    sys.exit(0 if success else 1)