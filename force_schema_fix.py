#!/usr/bin/env python3
"""
Force social inbox schema fix on production startup
This will be run automatically when the app starts in production
"""

import sys
import os
import logging

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.db.ensure_columns import ensure_social_inbox_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Force the social inbox schema fix"""
    try:
        logger.info("🚀 Force-fixing social inbox schema...")
        ensure_social_inbox_tables()
        logger.info("✅ Schema fix completed")
        return True
    except Exception as e:
        logger.error(f"❌ Schema fix failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    # Don't fail startup if this fails - just log it
    sys.exit(0)  # Always exit success to avoid breaking deployment