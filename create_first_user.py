#!/usr/bin/env python3
"""
Script to create first user account with automatic registration key generation
Run this after creating the admin account
"""
import os
import sys
import secrets
from datetime import datetime, timedelta
from enum import Enum

# Check for required packages
try:
    from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
    from sqlalchemy.orm import sessionmaker, declarative_base
    from passlib.context import CryptContext
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install: pip install sqlalchemy passlib[bcrypt] psycopg2-binary")
    sys.exit(1)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    tier = Column(String, default="base")
    auth_provider = Column(String, default="local")
    registration_key_id = Column(String, ForeignKey("registration_keys.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String, nullable=True)
    two_factor_backup_codes = Column(Text, nullable=True)

class RegistrationKey(Base):
    __tablename__ = "registration_keys"
    
    id = Column(String, primary_key=True, default=lambda: secrets.token_urlsafe(16))
    key = Column(String, unique=True, nullable=False)
    description = Column(String)
    max_uses = Column(Integer, default=1)
    current_uses = Column(Integer, default=0)
    expires_at = Column(DateTime)
    email_domain_restriction = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, nullable=True)

def create_first_user():
    """Create the first user with an auto-generated registration key"""
    
    # Get database URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL environment variable not set!")
        print("Please set it to your PostgreSQL connection string")
        sys.exit(1)
    
    # Fix URL for SQLAlchemy if needed
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://")
    
    print(f"📊 Connecting to database...")
    
    # Create engine and session
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Initialize password context
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Get user details
    print("\n👤 Enter details for the first user account:")
    email = input("Email: ").strip()
    username = input("Username: ").strip()
    full_name = input("Full Name: ").strip()
    password = input("Password: ").strip()
    
    if not email or not username or not password:
        print("❌ Email, username, and password are required!")
        sys.exit(1)
    
    # Start database session
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            print(f"❌ User with email '{email}' or username '{username}' already exists!")
            sys.exit(1)
        
        # Create registration key
        print("\n🔑 Creating registration key...")
        registration_key = secrets.token_urlsafe(32)
        
        new_key = RegistrationKey(
            key=registration_key,
            description=f"Auto-generated key for first user: {email}",
            max_uses=1,
            expires_at=datetime.utcnow() + timedelta(hours=1),  # Expires in 1 hour
            is_active=True
        )
        
        db.add(new_key)
        db.flush()  # Get the ID without committing
        
        # Create user
        print("👤 Creating user account...")
        hashed_password = pwd_context.hash(password)
        
        new_user = User(
            email=email,
            username=username,
            full_name=full_name or username,
            hashed_password=hashed_password,
            is_active=True,
            tier="premium",  # Give first user premium tier
            auth_provider="local",
            registration_key_id=new_key.id
        )
        
        db.add(new_user)
        
        # Mark registration key as used
        new_key.current_uses = 1
        
        # Commit everything
        db.commit()
        
        print("\n✅ First user created successfully!")
        print(f"📧 Email: {email}")
        print(f"👤 Username: {username}")
        print(f"🎯 Tier: premium")
        print(f"🔑 Registration Key Used: {registration_key[:8]}...")
        print("\n🚀 You can now login at /login with these credentials")
        
        # Also create API key for the user
        print("\n🔐 Would you like to generate an API key for this user? (y/n): ", end="")
        if input().lower() == 'y':
            api_key = secrets.token_urlsafe(32)
            api_secret = secrets.token_urlsafe(48)
            
            # You would need to create an api_keys table for this
            # For now, just display them
            print(f"\n🔑 API Key: {api_key}")
            print(f"🔐 API Secret: {api_secret}")
            print("\n⚠️  Save these credentials securely - they won't be shown again!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error creating user: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AI Social Media Agent - First User Setup")
    print("=" * 60)
    
    # Check if admin exists first
    print("\n⚠️  Note: This script assumes you've already created an admin account")
    print("   using create_admin_simple.py")
    print("\n   This creates a REGULAR USER account for using the platform")
    
    print("\n📝 Continue? (y/n): ", end="")
    if input().lower() != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    create_first_user()