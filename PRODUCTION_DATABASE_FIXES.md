# Production Database Fixes - AI Suggestions Performance

## 🚨 CRITICAL: AI Suggestions 7-11s Response Time Fix

The changes have been committed and pushed to production. Now you need to apply the database schema fixes.

## ✅ What Was Fixed in Code (Already Live)
- ✅ Updated OpenAI model: `gpt-4o-mini` → `gpt-5-mini`
- ✅ Updated database models with user_id relationships
- ✅ Added performance indexes to models

## 🔧 Database Changes Needed (Run on Production Server)

### Option 1: Run the automated fix script (RECOMMENDED)
```bash
# On your production server (Render, etc.)
cd /path/to/your/app
python fix_ai_suggestions_performance.py
```

### Option 2: Manual SQL commands (if script fails)
Connect to your production PostgreSQL database and run:

```sql
-- Add user_id to memories table
ALTER TABLE memories ADD COLUMN user_id INTEGER REFERENCES users(id);
CREATE INDEX IF NOT EXISTS ix_memories_user_id ON memories(user_id);
CREATE INDEX IF NOT EXISTS ix_memories_user_created ON memories(user_id, created_at);

-- Add user_id to content table  
ALTER TABLE content ADD COLUMN user_id INTEGER REFERENCES users(id);
CREATE INDEX IF NOT EXISTS ix_content_user_id ON content(user_id);
CREATE INDEX IF NOT EXISTS ix_content_user_created ON content(user_id, created_at);

-- Add performance indexes
CREATE INDEX IF NOT EXISTS ix_memories_created_at ON memories(created_at);
CREATE INDEX IF NOT EXISTS ix_content_created_at ON content(created_at);
```

## 🚀 After Database Changes

1. **Restart your backend service** (the code changes are already deployed)
2. **Test AI suggestions** - should load in <2 seconds instead of 7-11s
3. **Verify no more "Failed to load personalized suggestions" errors**

## 📊 Expected Results

- **Response Time**: 7-11 seconds → <2 seconds
- **Error Rate**: Eliminates "Failed to load personalized suggestions" 
- **User Experience**: Proper user-specific suggestions instead of generic fallbacks
- **Database Performance**: Efficient user-filtered queries instead of full table scans

## 🔍 Verification Commands

After applying the fixes, verify they worked:

```sql
-- Check that user_id columns exist
\d memories
\d content

-- Check indexes were created
\di *user*
```

## ⚠️ Important Notes

- The user_id columns will initially be NULL for existing data
- This is fine - the AI suggestions code handles NULL user_id gracefully
- New memories and content will automatically get proper user_id values
- The performance improvement happens immediately due to the indexes

## 🆘 If Something Goes Wrong

If the database changes cause issues, you can rollback:

```sql
-- Rollback (only if needed)
DROP INDEX IF EXISTS ix_memories_user_created;
DROP INDEX IF EXISTS ix_content_user_created;
DROP INDEX IF EXISTS ix_memories_user_id;
DROP INDEX IF EXISTS ix_content_user_id;
DROP INDEX IF EXISTS ix_memories_created_at;
DROP INDEX IF EXISTS ix_content_created_at;
ALTER TABLE memories DROP COLUMN user_id;
ALTER TABLE content DROP COLUMN user_id;
```

But the rollback shouldn't be necessary - these changes are purely additive and safe.