#!/usr/bin/env python3
"""
Database Schema Validator
Ensures all tables exist and have correct columns
"""

import os
import sys
import logging
from typing import Dict, List, Any
from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.exc import SQLAlchemyError

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from core.config import get_settings
    from db.models import Base, User, UserSetting, ContentLog, SocialPlatformConnection
except ImportError as e:
    print(f"Error: Could not import backend modules: {e}")
    sys.exit(1)

class DatabaseValidator:
    def __init__(self):
        self.logger = self.setup_logging()
        self.issues = []
        self.fixes_applied = []
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def validate_and_fix_schema(self):
        """Main validation and fix process"""
        print("🗄️  Database Schema Validation & Auto-Fix")
        print("=" * 50)
        
        try:
            settings = get_settings()
            engine = create_engine(settings.database_url)
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print("✅ Database connection successful")
            
            # Get current schema
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            print(f"📋 Found {len(existing_tables)} existing tables")
            
            # Define expected schema
            expected_schema = self.get_expected_schema()
            
            # Validate and fix each table
            for table_name, expected_table in expected_schema.items():
                self.validate_table(engine, inspector, table_name, expected_table, existing_tables)
            
            # Apply fixes if any were needed
            if self.fixes_applied:
                print(f"\n🔧 Applied {len(self.fixes_applied)} fixes:")
                for fix in self.fixes_applied:
                    print(f"   ✓ {fix}")
            
            # Report issues that need manual intervention
            if self.issues:
                print(f"\n⚠️  Found {len(self.issues)} issues requiring manual attention:")
                for issue in self.issues:
                    print(f"   ❌ {issue}")
            
            if not self.issues and not self.fixes_applied:
                print("\n🎉 Database schema is perfect!")
            
            return len(self.issues) == 0
            
        except Exception as e:
            print(f"❌ Database validation failed: {e}")
            return False
    
    def get_expected_schema(self) -> Dict[str, Dict]:
        """Define expected database schema"""
        return {
            'users': {
                'columns': [
                    ('id', 'INTEGER', True),  # (name, type, required)
                    ('email', 'VARCHAR', True),
                    ('hashed_password', 'VARCHAR', True),
                    ('is_active', 'BOOLEAN', True),
                    ('is_superuser', 'BOOLEAN', False),
                    ('created_at', 'TIMESTAMP', False),
                    ('updated_at', 'TIMESTAMP', False)
                ],
                'indexes': ['ix_users_email'],
                'constraints': ['users_pkey']
            },
            'user_settings': {
                'columns': [
                    ('id', 'INTEGER', True),
                    ('user_id', 'INTEGER', True),
                    ('brand_name', 'VARCHAR', False),
                    ('brand_voice', 'VARCHAR', False),
                    ('primary_color', 'VARCHAR', False),
                    ('content_frequency', 'INTEGER', False),
                    ('preferred_platforms', 'JSON', False),
                    ('posting_times', 'JSON', False),
                    ('creativity_level', 'FLOAT', False),
                    ('enable_images', 'BOOLEAN', False),
                    ('enable_repurposing', 'BOOLEAN', False),
                    ('enable_autonomous_mode', 'BOOLEAN', False),
                    ('timezone', 'VARCHAR', False),
                    ('auto_response_enabled', 'BOOLEAN', False),
                    ('created_at', 'TIMESTAMP', False)
                ],
                'foreign_keys': [('user_id', 'users', 'id')]
            },
            'content_logs': {
                'columns': [
                    ('id', 'INTEGER', True),
                    ('user_id', 'INTEGER', True),
                    ('content', 'TEXT', True),
                    ('content_type', 'VARCHAR', False),
                    ('platform', 'VARCHAR', False),
                    ('status', 'VARCHAR', False),
                    ('created_at', 'TIMESTAMP', False),
                    ('scheduled_for', 'TIMESTAMP', False)
                ],
                'foreign_keys': [('user_id', 'users', 'id')]
            },
            'social_platform_connections': {
                'columns': [
                    ('id', 'INTEGER', True),
                    ('user_id', 'INTEGER', True),
                    ('platform', 'VARCHAR', True),
                    ('platform_user_id', 'VARCHAR', True),
                    ('platform_username', 'VARCHAR', True),
                    ('is_active', 'BOOLEAN', False),
                    ('connection_status', 'VARCHAR', False),
                    ('connected_at', 'TIMESTAMP', False)
                ],
                'foreign_keys': [('user_id', 'users', 'id')]
            },
            'notifications': {
                'columns': [
                    ('id', 'INTEGER', True),
                    ('user_id', 'INTEGER', True),
                    ('title', 'VARCHAR', True),
                    ('message', 'TEXT', False),
                    ('notification_type', 'VARCHAR', False),
                    ('is_read', 'BOOLEAN', False),
                    ('created_at', 'TIMESTAMP', False)
                ],
                'foreign_keys': [('user_id', 'users', 'id')]
            }
        }
    
    def validate_table(self, engine, inspector, table_name, expected_table, existing_tables):
        """Validate a specific table"""
        print(f"\n📊 Validating table: {table_name}")
        
        # Check if table exists
        if table_name not in existing_tables:
            print(f"   ❌ Table {table_name} does not exist")
            if self.create_missing_table(engine, table_name):
                self.fixes_applied.append(f"Created table {table_name}")
            else:
                self.issues.append(f"Could not create table {table_name}")
            return
        
        print(f"   ✅ Table {table_name} exists")
        
        # Get current columns
        current_columns = inspector.get_columns(table_name)
        current_column_names = {col['name'].lower() for col in current_columns}
        
        # Check required columns
        missing_columns = []
        for col_name, col_type, required in expected_table['columns']:
            if col_name.lower() not in current_column_names:
                if required:
                    missing_columns.append((col_name, col_type, required))
                    print(f"   ❌ Missing required column: {col_name}")
                else:
                    print(f"   ⚠️  Missing optional column: {col_name}")
        
        # Try to add missing columns
        if missing_columns:
            for col_name, col_type, required in missing_columns:
                if self.add_missing_column(engine, table_name, col_name, col_type, required):
                    self.fixes_applied.append(f"Added column {table_name}.{col_name}")
                else:
                    self.issues.append(f"Could not add column {table_name}.{col_name}")
        
        # Check foreign keys
        if 'foreign_keys' in expected_table:
            current_fks = inspector.get_foreign_keys(table_name)
            current_fk_columns = {fk['constrained_columns'][0] for fk in current_fks if fk['constrained_columns']}
            
            for fk_col, ref_table, ref_col in expected_table['foreign_keys']:
                if fk_col not in current_fk_columns:
                    print(f"   ⚠️  Missing foreign key: {fk_col} -> {ref_table}.{ref_col}")
        
        if not missing_columns:
            print(f"   ✅ All required columns present")
    
    def create_missing_table(self, engine, table_name):
        """Create a missing table"""
        try:
            print(f"   🔧 Attempting to create table {table_name}...")
            
            # Use SQLAlchemy models to create tables
            if table_name == 'user_settings':
                UserSetting.__table__.create(engine, checkfirst=True)
                return True
            elif table_name == 'social_platform_connections':
                SocialPlatformConnection.__table__.create(engine, checkfirst=True)  
                return True
            # Add other tables as needed
            else:
                # Fallback: create all missing tables
                Base.metadata.create_all(engine, checkfirst=True)
                return True
                
        except Exception as e:
            print(f"   ❌ Failed to create table {table_name}: {e}")
            return False
    
    def add_missing_column(self, engine, table_name, col_name, col_type, required):
        """Add a missing column to existing table"""
        try:
            print(f"   🔧 Adding column {col_name} to {table_name}...")
            
            # Map generic types to PostgreSQL types
            pg_type_mapping = {
                'INTEGER': 'INTEGER',
                'VARCHAR': 'VARCHAR',
                'TEXT': 'TEXT',
                'BOOLEAN': 'BOOLEAN',
                'TIMESTAMP': 'TIMESTAMP WITH TIME ZONE',
                'JSON': 'JSON',
                'FLOAT': 'FLOAT'
            }
            
            pg_type = pg_type_mapping.get(col_type, 'VARCHAR')
            nullable = "NULL" if not required else "NOT NULL DEFAULT ''"
            
            # Special handling for specific columns
            if col_name == 'is_active' and col_type == 'BOOLEAN':
                nullable = "NOT NULL DEFAULT true"
            elif col_name == 'enable_autonomous_mode' and col_type == 'BOOLEAN':
                nullable = "NOT NULL DEFAULT false"
            elif col_name == 'created_at' and col_type == 'TIMESTAMP':
                nullable = "DEFAULT now()"
            
            sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {pg_type} {nullable};"
            
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to add column {col_name}: {e}")
            return False
    
    def generate_fix_script(self):
        """Generate SQL script for manual fixes"""
        if not self.issues:
            return None
        
        script_content = f"""-- Database Fix Script
-- Generated on {datetime.now().isoformat()}
-- 
-- Run this script on your database to fix remaining issues:

"""
        
        for issue in self.issues:
            script_content += f"-- TODO: {issue}\n"
        
        script_file = "database_fixes.sql"
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        return script_file

def main():
    """Run database validation"""
    validator = DatabaseValidator()
    success = validator.validate_and_fix_schema()
    
    if not success:
        print("\n🔧 Database validation completed with issues.")
        script_file = validator.generate_fix_script()
        if script_file:
            print(f"📄 Manual fix script generated: {script_file}")
    else:
        print("\n✅ Database validation completed successfully!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())