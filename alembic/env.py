from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.database import Base
from backend.db.models import *  # Import all models
from backend.core.config import get_settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_database_url():
    """Get database URL - ALWAYS POSTGRESQL, NEVER SQLITE"""
    # ALWAYS use PostgreSQL - no conditions, no fallbacks
    postgresql_url = "postgresql://socialmedia:BbsIYQtjBnhKwRL3F9kXbv1wrtsVxuTg@dpg-d2ln7eer433s739509lg-a/socialmedia_uq72?sslmode=require"
    
    # Try to get from environment or settings, but ALWAYS validate it's PostgreSQL
    try:
        settings = get_settings()
        db_url = settings.get_database_url()
        
        # Reject SQLite completely
        if "sqlite" in db_url.lower():
            print("WARNING: SQLite detected in Alembic, forcing PostgreSQL")
            return postgresql_url
            
        return db_url
    except:
        # Any error = use PostgreSQL
        print("WARNING: Could not get database URL, using PostgreSQL")
        return postgresql_url

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Override the database URL in alembic.ini
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()