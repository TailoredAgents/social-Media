#!/usr/bin/env python3
"""
Fix Alembic migration chain issues
"""
import os
import re

def fix_migration_chain():
    """Fix migration chain references"""
    
    migrations_dir = "alembic/versions"
    
    # Expected migration chain
    migration_chain = {
        "001_initial_migration": None,
        "002_add_auth_fields": "001_initial_migration", 
        "003_enhanced_content_metadata": "002_add_auth_fields",
        "004_add_notifications_table": "003_enhanced_content_metadata",
        "005_add_milestones_table": "004_add_notifications_table",
        "006_fix_metadata_column_names": "005_add_milestones_table",
        "007_add_external_post_id": "006_fix_metadata_column_names",
        "008": "007_add_external_post_id",
        "008a_add_social_platform_connections": "008",
        "009": "008a_add_social_platform_connections",
        "010": "009",
        "011": "010",
        "012_add_multi_tenant_schema": "011",
        "013": "012_add_multi_tenant_schema",
        "014": "013"
    }
    
    files = os.listdir(migrations_dir)
    
    for filename in files:
        if not filename.endswith('.py') or filename.startswith('__'):
            continue
            
        filepath = os.path.join(migrations_dir, filename)
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Extract current revision
        revision_match = re.search(r"revision = ['\"]([^'\"]+)['\"]", content)
        if not revision_match:
            continue
            
        revision = revision_match.group(1)
        
        if revision in migration_chain:
            expected_down_revision = migration_chain[revision]
            
            if expected_down_revision is None:
                # First migration
                new_content = re.sub(
                    r"down_revision = ['\"][^'\"]*['\"]",
                    "down_revision = None",
                    content
                )
            else:
                new_content = re.sub(
                    r"down_revision = ['\"][^'\"]*['\"]",
                    f"down_revision = '{expected_down_revision}'",
                    content
                )
            
            if new_content != content:
                print(f"Fixing {filename}: {revision} -> {expected_down_revision}")
                with open(filepath, 'w') as f:
                    f.write(new_content)

if __name__ == "__main__":
    fix_migration_chain()
    print("Migration chain fixed!")