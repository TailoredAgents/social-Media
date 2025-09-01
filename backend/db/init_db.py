"""
Database initialization utilities
"""
from sqlalchemy import create_engine
from backend.db.database import Base
from backend.db.models import *  # Import all models
from backend.core.config import get_settings

def create_tables():
    """Create all database tables"""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def drop_tables():
    """Drop all database tables (use with caution!)"""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print("🗑️ Database tables dropped")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        drop_tables()
    else:
        create_tables()