#!/bin/bash
set -e  # Exit on any error

echo "🚀 Starting AI Social Media Content Agent (Production)"
echo "=================================================="

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if database is available
check_database() {
    log "🔍 Checking database connectivity..."
    
    python -c "
import sys
import os
sys.path.insert(0, '.')
from backend.db.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
"
}

# Function to run database migrations
run_migrations() {
    log "🔄 Running database migrations..."
    
    # Run migrations with timeout protection
    timeout 300 python run_migrations.py || {
        log "❌ Migration failed or timed out after 5 minutes"
        exit 1
    }
    
    log "✅ Database migrations completed"
}

# Function to verify critical tables exist
verify_tables() {
    log "🔍 Verifying critical database tables..."
    
    python -c "
import sys
sys.path.insert(0, '.')
from backend.db.database import engine
from sqlalchemy import text

critical_tables = ['users', 'user_settings', 'content_logs', 'notifications', 'refresh_token_blacklist']
missing_tables = []

try:
    with engine.connect() as conn:
        for table in critical_tables:
            try:
                conn.execute(text(f'SELECT 1 FROM {table} LIMIT 1'))
            except Exception:
                missing_tables.append(table)
    
    if missing_tables:
        print(f'❌ Missing critical tables: {missing_tables}')
        sys.exit(1)
    else:
        print('✅ All critical tables exist')
        
except Exception as e:
    print(f'❌ Table verification failed: {e}')
    sys.exit(1)
"
}

# Function to start the application
start_app() {
    log "🎯 Starting FastAPI application..."
    exec python app.py
}

# Main execution flow
main() {
    log "Starting production deployment sequence..."
    
    # Step 1: Check database connectivity
    check_database
    
    # Step 2: Run database migrations
    run_migrations
    
    # Step 3: Force fix social inbox schema
    log "🔧 Fixing social inbox schema..."
    python force_schema_fix.py || log "⚠️ Schema fix had issues but continuing..."
    
    # Step 3.5: Ensure user_settings table exists
    log "🔧 Ensuring user_settings table exists..."
    python fix_user_settings_table.py || log "⚠️ User settings table fix had issues but continuing..."
    
    # Step 4: Verify critical tables exist
    verify_tables
    
    # Step 5: Start the application
    start_app
}

# Handle signals gracefully
trap 'log "🛑 Received termination signal, shutting down..."; exit 0' SIGTERM SIGINT

# Execute main function
main "$@"