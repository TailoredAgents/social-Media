-- Initialize database for AI Social Media Agent
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Set timezone to UTC
SET timezone = 'UTC';

-- Create application database if it doesn't exist
-- (This file runs after the database is already created by POSTGRES_DB)

-- Log initialization
SELECT 'AI Social Media Agent database initialized with pgvector extension' as status;