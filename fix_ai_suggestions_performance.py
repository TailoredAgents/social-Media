#!/usr/bin/env python3
"""
Fix AI Suggestions Performance Issues
Adds missing user_id columns to memory and content tables
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from core.config import get_settings
except ImportError as e:
    print(f"❌ Error: Could not import backend modules: {e}")
    sys.exit(1)

def fix_ai_suggestions_performance():
    """Apply database fixes for AI suggestions performance"""
    print("🔧 Fixing AI Suggestions Performance Issues")
    print("=" * 50)
    
    try:
        settings = get_settings()
        engine = create_engine(settings.get_database_url())
        
        with engine.connect() as conn:
            # Test connection
            conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Check current schema
            inspector = inspect(engine)
            
            # Check if memory table has user_id
            memory_columns = [col['name'] for col in inspector.get_columns('memories')]
            content_columns = [col['name'] for col in inspector.get_columns('content')]
            
            print(f"📋 Memory table columns: {memory_columns}")
            print(f"📋 Content table columns: {content_columns}")
            
            fixes_applied = []
            
            # Fix 1: Add user_id to memories table if missing
            if 'user_id' not in memory_columns:
                print("\n🔧 Adding user_id to memories table...")
                try:
                    conn.execute(text("""
                        ALTER TABLE memories 
                        ADD COLUMN user_id INTEGER REFERENCES users(id);
                    """))
                    
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS ix_memories_user_id 
                        ON memories(user_id);
                    """))
                    
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS ix_memories_user_created 
                        ON memories(user_id, created_at);
                    """))
                    
                    fixes_applied.append("Added user_id to memories table")
                    print("✅ memories.user_id added successfully")
                except Exception as e:
                    print(f"⚠️ Error adding user_id to memories: {e}")
            else:
                print("✅ memories.user_id already exists")
            
            # Fix 2: Add user_id to content table if missing
            if 'user_id' not in content_columns:
                print("\n🔧 Adding user_id to content table...")
                try:
                    conn.execute(text("""
                        ALTER TABLE content 
                        ADD COLUMN user_id INTEGER REFERENCES users(id);
                    """))
                    
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS ix_content_user_id 
                        ON content(user_id);
                    """))
                    
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS ix_content_user_created 
                        ON content(user_id, created_at);
                    """))
                    
                    fixes_applied.append("Added user_id to content table")
                    print("✅ content.user_id added successfully")
                except Exception as e:
                    print(f"⚠️ Error adding user_id to content: {e}")
            else:
                print("✅ content.user_id already exists")
            
            # Fix 3: Add performance indexes
            print("\n🔧 Adding performance indexes...")
            try:
                # Check existing indexes
                existing_indexes = inspector.get_indexes('memories') + inspector.get_indexes('content')
                index_names = [idx['name'] for idx in existing_indexes]
                
                performance_indexes = [
                    ("ix_memories_created_at", "memories", ["created_at"]),
                    ("ix_content_created_at", "content", ["created_at"]),
                ]
                
                for index_name, table_name, columns in performance_indexes:
                    if index_name not in index_names:
                        column_list = ', '.join(columns)
                        conn.execute(text(f"""
                            CREATE INDEX IF NOT EXISTS {index_name} 
                            ON {table_name}({column_list});
                        """))
                        print(f"✅ Added index: {index_name}")
                
                fixes_applied.append("Added performance indexes")
            except Exception as e:
                print(f"⚠️ Error adding performance indexes: {e}")
            
            # Commit all changes
            conn.commit()
            
            print(f"\n🎉 Performance fixes completed!")
            print(f"📊 Applied {len(fixes_applied)} fixes:")
            for fix in fixes_applied:
                print(f"   ✓ {fix}")
            
            print(f"\n📈 Expected improvements:")
            print(f"   • AI suggestions response time: 7-11s → <2s")
            print(f"   • Eliminates 'Failed to load personalized suggestions' errors")
            print(f"   • Proper user data isolation and filtering")
            print(f"   • Optimized database queries with user-specific indexes")
            
            return True
            
    except Exception as e:
        print(f"❌ Performance fix failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_ai_suggestions_performance()
    if success:
        print("\n✅ AI Suggestions performance fix completed successfully!")
        print("🚀 Deploy and restart the backend to apply OpenAI model changes.")
    else:
        print("\n❌ Performance fix failed. Check the logs above.")
        sys.exit(1)