"""
Ensure critical database columns exist on startup
This bypasses Alembic migration issues in production
"""
import logging
from sqlalchemy import text
from backend.db.database import engine

logger = logging.getLogger(__name__)

def ensure_content_logs_table():
    """
    Ensure content_logs table exists with all required columns and proper foreign key constraints
    """
    try:
        with engine.connect() as conn:
            # Check if content_logs table exists
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'content_logs'
            """)).fetchall()
            
            if not result:
                logger.info("Creating missing content_logs table...")
                
                # Create content_logs table based on models.py with explicit foreign key
                conn.execute(text("""
                    CREATE TABLE content_logs (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        platform VARCHAR NOT NULL,
                        content TEXT NOT NULL,
                        content_type VARCHAR NOT NULL,
                        status VARCHAR DEFAULT 'draft',
                        engagement_data JSON DEFAULT '{}',
                        scheduled_for TIMESTAMP WITH TIME ZONE,
                        published_at TIMESTAMP WITH TIME ZONE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE,
                        platform_post_id VARCHAR,
                        external_post_id VARCHAR,
                        CONSTRAINT fk_content_logs_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """))
                
                # Create indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_content_logs_user_id ON content_logs (user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_content_logs_platform ON content_logs (platform)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_content_logs_status ON content_logs (status)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_content_logs_created_at ON content_logs (created_at)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_content_logs_external_post_id ON content_logs (external_post_id)"))
                
                conn.commit()
                logger.info("✅ Successfully created content_logs table with foreign key constraints")
            else:
                logger.info("✅ Content_logs table already exists")
                
                # Check if foreign key constraint exists (PostgreSQL specific)
                fk_check = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu 
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = 'content_logs'
                        AND kcu.column_name = 'user_id'
                        AND ccu.table_name = 'users'
                        AND ccu.column_name = 'id'
                """)).scalar()
                
                if fk_check == 0:
                    logger.info("Adding missing foreign key constraint to content_logs table...")
                    try:
                        conn.execute(text("""
                            ALTER TABLE content_logs 
                            ADD CONSTRAINT fk_content_logs_user_id 
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                        """))
                        conn.commit()
                        logger.info("✅ Successfully added foreign key constraint to content_logs")
                    except Exception as fk_error:
                        logger.warning(f"Could not add foreign key constraint: {fk_error}")
                        conn.rollback()
                
                # Check and add missing columns to existing content_logs table
                missing_columns = [
                    ('scheduled_for', 'TIMESTAMP WITH TIME ZONE'),
                    ('platform_post_id', 'VARCHAR'),
                    ('external_post_id', 'VARCHAR'),
                ]
                
                # Get existing columns
                existing_columns = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'content_logs'
                """)).fetchall()
                
                existing_column_names = {row[0] for row in existing_columns}
                
                for column_name, column_type in missing_columns:
                    if column_name not in existing_column_names:
                        logger.info(f"Adding missing {column_name} column to content_logs table")
                        try:
                            conn.execute(text(f"""
                                ALTER TABLE content_logs 
                                ADD COLUMN {column_name} {column_type}
                            """))
                            conn.commit()
                            logger.info(f"✅ Successfully added {column_name} column to content_logs")
                        except Exception as col_error:
                            logger.warning(f"Could not add {column_name} column: {col_error}")
                            conn.rollback()
                
                # Create missing indexes
                if 'external_post_id' not in existing_column_names:
                    try:
                        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_content_logs_external_post_id ON content_logs (external_post_id)"))
                        conn.commit()
                    except Exception as idx_error:
                        logger.warning(f"Could not create external_post_id index: {idx_error}")
                        conn.rollback()
                
    except Exception as e:
        logger.error(f"❌ Error ensuring content_logs table: {e}")
        pass

def ensure_notifications_table():
    """
    Ensure notifications table exists with all required columns
    """
    try:
        with engine.connect() as conn:
            # Check if notifications table exists
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'notifications'
            """)).fetchall()
            
            if not result:
                logger.info("Creating missing notifications table...")
                
                # Create notifications table
                conn.execute(text("""
                    CREATE TABLE notifications (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        title VARCHAR(255) NOT NULL,
                        message TEXT,
                        notification_type VARCHAR(50) DEFAULT 'info',
                        priority VARCHAR(20) DEFAULT 'medium',
                        goal_id INTEGER,
                        content_id INTEGER, 
                        workflow_id INTEGER,
                        is_read BOOLEAN DEFAULT FALSE,
                        is_dismissed BOOLEAN DEFAULT FALSE,
                        read_at TIMESTAMP,
                        action_url VARCHAR(500),
                        action_label VARCHAR(100),
                        notification_metadata JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP
                    )
                """))
                
                # Create indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_is_read ON notifications (is_read)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications (created_at)"))
                
                conn.commit()
                logger.info("✅ Successfully created notifications table")
            else:
                logger.info("✅ Notifications table already exists")
                
    except Exception as e:
        logger.error(f"❌ Error ensuring notifications table: {e}")
        pass

def ensure_social_inbox_tables():
    """
    Ensure all social inbox tables exist with proper structure
    Handle data type mismatches by dropping and recreating tables if needed
    """
    try:
        with engine.connect() as conn:
            logger.info("Checking social inbox tables...")
            
            # First, check for and fix any existing tables with wrong schema
            _fix_existing_social_inbox_schemas(conn)
            
            # 1. Social Platform Connections table
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = 'social_platform_connections'
            """)).fetchall()
            
            if not result:
                logger.info("Creating social_platform_connections table...")
                conn.execute(text("""
                    CREATE TABLE social_platform_connections (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        platform VARCHAR NOT NULL,
                        platform_user_id VARCHAR NOT NULL,
                        platform_username VARCHAR NOT NULL,
                        platform_display_name VARCHAR,
                        profile_image_url VARCHAR,
                        profile_url VARCHAR,
                        access_token TEXT NOT NULL,
                        refresh_token TEXT,
                        token_expires_at TIMESTAMP WITH TIME ZONE,
                        token_type VARCHAR DEFAULT 'Bearer',
                        scope VARCHAR,
                        is_active BOOLEAN DEFAULT TRUE,
                        is_verified BOOLEAN DEFAULT FALSE,
                        connection_status VARCHAR DEFAULT 'connected',
                        platform_metadata JSON DEFAULT '{}',
                        rate_limit_remaining INTEGER,
                        rate_limit_reset TIMESTAMP WITH TIME ZONE,
                        daily_post_count INTEGER DEFAULT 0,
                        daily_post_limit INTEGER,
                        last_error TEXT,
                        error_count INTEGER DEFAULT 0,
                        last_error_at TIMESTAMP WITH TIME ZONE,
                        auto_post_enabled BOOLEAN DEFAULT TRUE,
                        preferred_posting_times JSON DEFAULT '{}',
                        content_filters JSON DEFAULT '{}',
                        connected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        last_used_at TIMESTAMP WITH TIME ZONE,
                        last_refreshed_at TIMESTAMP WITH TIME ZONE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE,
                        UNIQUE(user_id, platform)
                    )
                """))
                
                # Create indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_platform_connections_user_id ON social_platform_connections (user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_platform_connections_platform ON social_platform_connections (platform)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_platform_connections_platform_user_id ON social_platform_connections (platform_user_id)"))
                conn.commit()
                logger.info("✅ Successfully created social_platform_connections table")
            else:
                logger.info("✅ Social_platform_connections table already exists, checking for missing columns...")
                
                # Check and add missing columns to existing table
                missing_columns = [
                    ('rate_limit_remaining', 'INTEGER'),
                    ('rate_limit_reset', 'TIMESTAMP WITH TIME ZONE'),
                    ('daily_post_count', 'INTEGER DEFAULT 0'),
                    ('daily_post_limit', 'INTEGER'),
                    ('last_error', 'TEXT'),
                    ('error_count', 'INTEGER DEFAULT 0'),
                    ('last_error_at', 'TIMESTAMP WITH TIME ZONE'),
                    ('auto_post_enabled', 'BOOLEAN DEFAULT TRUE'),
                    ('preferred_posting_times', 'JSON DEFAULT \'{}\''),
                    ('content_filters', 'JSON DEFAULT \'{}\''),
                    ('last_refreshed_at', 'TIMESTAMP WITH TIME ZONE'),
                ]
                
                # Get existing columns
                existing_columns = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'social_platform_connections'
                """)).fetchall()
                
                existing_column_names = {row[0] for row in existing_columns}
                
                columns_added = 0
                for column_name, column_type in missing_columns:
                    if column_name not in existing_column_names:
                        logger.info(f"Adding missing {column_name} column to social_platform_connections table")
                        try:
                            conn.execute(text(f"""
                                ALTER TABLE social_platform_connections 
                                ADD COLUMN {column_name} {column_type}
                            """))
                            conn.commit()
                            columns_added += 1
                            logger.info(f"✅ Successfully added {column_name} column")
                        except Exception as col_error:
                            logger.warning(f"Could not add {column_name} column: {col_error}")
                            conn.rollback()
                
                if columns_added > 0:
                    logger.info(f"✅ Added {columns_added} missing columns to social_platform_connections table")
                else:
                    logger.info("✅ All required columns already exist in social_platform_connections table")
            
            # 2. Social Interactions table
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = 'social_interactions'
            """)).fetchall()
            
            if not result:
                logger.info("Creating social_interactions table...")
                conn.execute(text("""
                    CREATE TABLE social_interactions (
                        id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        connection_id INTEGER REFERENCES social_platform_connections(id),
                        platform VARCHAR NOT NULL,
                        interaction_type VARCHAR NOT NULL,
                        external_id VARCHAR NOT NULL,
                        parent_external_id VARCHAR,
                        author_platform_id VARCHAR NOT NULL,
                        author_username VARCHAR NOT NULL,
                        author_display_name VARCHAR,
                        author_profile_url VARCHAR,
                        author_profile_image VARCHAR,
                        author_verified BOOLEAN DEFAULT FALSE,
                        content TEXT NOT NULL,
                        media_urls JSON DEFAULT '[]',
                        hashtags JSON DEFAULT '[]',
                        mentions JSON DEFAULT '[]',
                        sentiment VARCHAR DEFAULT 'neutral',
                        intent VARCHAR,
                        priority_score FLOAT DEFAULT 0.0,
                        status VARCHAR DEFAULT 'unread',
                        assigned_to INTEGER REFERENCES users(id),
                        response_strategy VARCHAR DEFAULT 'auto',
                        platform_metadata JSON DEFAULT '{}',
                        platform_created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        last_updated_at TIMESTAMP WITH TIME ZONE,
                        UNIQUE(platform, external_id)
                    )
                """))
                
                # Create indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_interactions_user_id ON social_interactions (user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_interactions_platform ON social_interactions (platform)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_interactions_interaction_type ON social_interactions (interaction_type)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_interactions_external_id ON social_interactions (external_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_interactions_status ON social_interactions (status)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_interactions_priority_score ON social_interactions (priority_score)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_interactions_received_at ON social_interactions (received_at)"))
                conn.commit()
                logger.info("✅ Successfully created social_interactions table")
            
            # 3. Response Templates table
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = 'response_templates'
            """)).fetchall()
            
            if not result:
                logger.info("Creating response_templates table...")
                conn.execute(text("""
                    CREATE TABLE response_templates (
                        id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        name VARCHAR NOT NULL,
                        description TEXT,
                        trigger_type VARCHAR NOT NULL,
                        trigger_conditions JSON DEFAULT '{}',
                        keywords JSON DEFAULT '[]',
                        platforms JSON DEFAULT '[]',
                        response_text TEXT NOT NULL,
                        variables JSON DEFAULT '[]',
                        personality_style VARCHAR DEFAULT 'professional',
                        tone VARCHAR DEFAULT 'helpful',
                        auto_approve BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT TRUE,
                        priority INTEGER DEFAULT 1,
                        usage_count INTEGER DEFAULT 0,
                        avg_satisfaction FLOAT DEFAULT 0.0,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE
                    )
                """))
                
                # Create indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_response_templates_user_id ON response_templates (user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_response_templates_trigger_type ON response_templates (trigger_type)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_response_templates_is_active ON response_templates (is_active)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_response_templates_priority ON response_templates (priority)"))
                conn.commit()
                logger.info("✅ Successfully created response_templates table")
            
            # 4. Interaction Responses table
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = 'interaction_responses'
            """)).fetchall()
            
            if not result:
                logger.info("Creating interaction_responses table...")
                conn.execute(text("""
                    CREATE TABLE interaction_responses (
                        id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
                        interaction_id VARCHAR NOT NULL REFERENCES social_interactions(id) ON DELETE CASCADE,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        response_text TEXT NOT NULL,
                        media_urls JSON DEFAULT '[]',
                        response_type VARCHAR DEFAULT 'manual',
                        template_id VARCHAR REFERENCES response_templates(id),
                        ai_confidence_score FLOAT DEFAULT 0.0,
                        platform VARCHAR NOT NULL,
                        platform_response_id VARCHAR,
                        platform_url VARCHAR,
                        status VARCHAR DEFAULT 'draft',
                        sent_at TIMESTAMP WITH TIME ZONE,
                        failure_reason TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE
                    )
                """))
                
                # Create indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_interaction_responses_interaction_id ON interaction_responses (interaction_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_interaction_responses_user_id ON interaction_responses (user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_interaction_responses_status ON interaction_responses (status)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_interaction_responses_created_at ON interaction_responses (created_at)"))
                conn.commit()
                logger.info("✅ Successfully created interaction_responses table")
            
            # 5. Company Knowledge table
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = 'company_knowledge'
            """)).fetchall()
            
            if not result:
                logger.info("Creating company_knowledge table...")
                conn.execute(text("""
                    CREATE TABLE company_knowledge (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        title VARCHAR NOT NULL,
                        topic VARCHAR NOT NULL,
                        content TEXT NOT NULL,
                        summary VARCHAR,
                        keywords JSON DEFAULT '[]',
                        tags JSON DEFAULT '[]',
                        embedding_vector JSON,
                        context_type VARCHAR DEFAULT 'general',
                        platforms JSON DEFAULT '["facebook", "instagram", "twitter"]',
                        usage_count INTEGER DEFAULT 0,
                        effectiveness_score FLOAT DEFAULT 0.0,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE
                    )
                """))
                
                # Create indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_company_knowledge_user_id ON company_knowledge (user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_company_knowledge_topic ON company_knowledge (topic)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_company_knowledge_is_active ON company_knowledge (is_active)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_company_knowledge_usage_count ON company_knowledge (usage_count)"))
                conn.commit()
                logger.info("✅ Successfully created company_knowledge table")
                
            logger.info("✅ All social inbox tables verified/created successfully")
            
    except Exception as e:
        logger.error(f"❌ Error ensuring social inbox tables: {e}")
        pass

def ensure_user_columns():
    """
    Ensure all required columns exist in the users table.
    Based on migration 016_convert_to_open_saas_auth.py
    This is a safety net for production where migrations might not run properly.
    """
    required_columns = [
        # Core auth columns
        ('is_superuser', 'BOOLEAN DEFAULT FALSE'),
        ('is_verified', 'BOOLEAN DEFAULT FALSE'), 
        ('is_active', 'BOOLEAN DEFAULT TRUE'),
        ('auth_provider', 'VARCHAR(50) DEFAULT \'local\''),
        
        # Email verification columns (CRITICAL - missing these causes 500 errors)
        ('email_verified', 'BOOLEAN DEFAULT FALSE'),
        ('email_verification_token', 'VARCHAR(255)'),
        ('email_verification_sent_at', 'TIMESTAMP'),
        
        # Password reset columns
        ('password_reset_token', 'VARCHAR(255)'),
        ('password_reset_sent_at', 'TIMESTAMP'),
        
        # Two-factor authentication columns
        ('two_factor_enabled', 'BOOLEAN DEFAULT FALSE'),
        ('two_factor_secret', 'VARCHAR(255)'),
        ('two_factor_backup_codes', 'JSON'),
        
        # Multi-tenancy columns (CRITICAL - missing causes registration failures)
        ('default_organization_id', 'VARCHAR(255)'),
        
        # Subscription columns
        ('tier', 'VARCHAR(50) DEFAULT \'free\''),
        ('subscription_status', 'VARCHAR(50) DEFAULT \'free\''),
        ('subscription_end_date', 'TIMESTAMP'),
        ('stripe_customer_id', 'VARCHAR(255)'),
        ('stripe_subscription_id', 'VARCHAR(255)'),
        
        # Timestamps (commonly missing)
        ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ('updated_at', 'TIMESTAMP'),
    ]
    
    try:
        with engine.connect() as conn:
            logger.info("Checking for missing columns in users table...")
            
            # Get all existing columns
            existing_columns = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users'
            """)).fetchall()
            
            existing_column_names = {row[0] for row in existing_columns}
            logger.info(f"Found {len(existing_column_names)} existing columns in users table")
            
            columns_added = 0
            for column_name, column_type in required_columns:
                if column_name not in existing_column_names:
                    logger.info(f"Adding missing {column_name} column to users table")
                    
                    try:
                        conn.execute(text(f"""
                            ALTER TABLE users 
                            ADD COLUMN {column_name} {column_type}
                        """))
                        conn.commit()
                        columns_added += 1
                        logger.info(f"✅ Successfully added {column_name} column")
                    except Exception as col_error:
                        logger.error(f"❌ Failed to add {column_name} column: {col_error}")
                        conn.rollback()
            
            if columns_added > 0:
                logger.info(f"✅ Added {columns_added} missing columns to users table")
            else:
                logger.info("✅ All required columns already exist in users table")
                
            # Create indexes for new columns if they don't exist
            indexes_to_create = [
                ('ix_users_email_verification_token', 'email_verification_token'),
                ('ix_users_password_reset_token', 'password_reset_token'), 
                ('ix_users_stripe_customer_id', 'stripe_customer_id'),
                ('ix_users_email_username', 'email, username'),  # Composite index for login queries  
                ('ix_users_tier_status', 'tier, subscription_status'),  # Index for subscription queries
            ]
            
            for index_name, column_name in indexes_to_create:
                try:
                    conn.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} ON users ({column_name})
                    """))
                    conn.commit()
                except Exception as idx_error:
                    logger.warning(f"Could not create index {index_name}: {idx_error}")
                    conn.rollback()
            
            logger.info("✅ Database column and index check complete")
            
    except Exception as e:
        logger.error(f"❌ Error ensuring database columns: {e}")
        # Don't crash the app, just log the error
        pass

def _fix_existing_social_inbox_schemas(conn):
    """
    Fix existing social inbox tables that have schema mismatches
    Drop and recreate tables with wrong data types
    """
    try:
        logger.info("🔧 Checking for social inbox schema mismatches...")
        
        # Check if any social inbox tables exist and drop them all to recreate with correct schema  
        # Drop in dependency order: child tables first, then parent tables
        tables_to_check = ['interaction_responses', 'social_interactions', 'response_templates', 'social_platform_connections']
        
        for table_name in tables_to_check:
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = :table_name
            """), {"table_name": table_name}).fetchone()
            
            if result:
                logger.info(f"Dropping existing {table_name} table to recreate with correct schema...")
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                conn.commit()
                logger.info(f"✅ Dropped {table_name}")
                
    except Exception as e:
        logger.warning(f"Error checking existing schemas: {e}")
        # Continue anyway - the table creation will handle it