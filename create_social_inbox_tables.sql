-- SQL script to create social inbox tables
-- Run this on the production database if migrations haven't been applied

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

-- Create inbox_settings table (from migration 020)
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

-- Add trigger to update last_updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for tables with updated_at columns
CREATE TRIGGER update_social_interactions_updated_at BEFORE UPDATE ON social_interactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_response_templates_updated_at BEFORE UPDATE ON response_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_base_updated_at BEFORE UPDATE ON knowledge_base_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_inbox_settings_updated_at BEFORE UPDATE ON inbox_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();