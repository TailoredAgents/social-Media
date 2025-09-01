#!/usr/bin/env python3
"""
Script to create the initial super admin account for the Lily AI Social Media platform.
Run this script once during initial setup.
"""
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime, timezone
import getpass

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.admin_models import AdminUser, AdminRole
from backend.auth.admin_auth import AdminAuth
from backend.core.config import settings

# Initialize admin auth
admin_auth = AdminAuth()

def create_super_admin():
    """Create the super admin account"""
    
    # Get database URL from settings
    database_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Create database engine
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    print("\n" + "="*60)
    print("LILY AI SOCIAL MEDIA - SUPER ADMIN CREATION")
    print("="*60)
    
    # Get admin details
    print("\nPlease enter the super admin details:")
    username = input("Username (default: superadmin): ").strip() or "superadmin"
    email = input("Email address: ").strip()
    
    if not email:
        print("Error: Email address is required")
        return False
    
    # Get password securely
    while True:
        password = getpass.getpass("Password (min 8 characters): ")
        if len(password) < 8:
            print("Password must be at least 8 characters long")
            continue
        
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match")
            continue
        break
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if super admin already exists
        existing_admin = db.query(AdminUser).filter(
            AdminUser.role == AdminRole.SUPER_ADMIN
        ).first()
        
        if existing_admin:
            print(f"\nWarning: A super admin already exists (username: {existing_admin.username})")
            response = input("Do you want to create another super admin? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Aborted.")
                return False
        
        # Check if username or email already exists
        existing_user = db.query(AdminUser).filter(
            (AdminUser.username == username) | (AdminUser.email == email)
        ).first()
        
        if existing_user:
            print(f"\nError: Admin with username '{username}' or email '{email}' already exists")
            return False
        
        # Create the super admin
        super_admin = AdminUser(
            username=username,
            email=email,
            hashed_password=admin_auth.hash_password(password),
            role=AdminRole.SUPER_ADMIN,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            last_login=None
        )
        
        db.add(super_admin)
        db.commit()
        
        print("\n" + "="*60)
        print("SUCCESS: Super Admin created successfully!")
        print("="*60)
        print(f"\nUsername: {username}")
        print(f"Email: {email}")
        print(f"Role: SUPER_ADMIN")
        print(f"\nYou can now log in at: {settings.app_url}/admin")
        print("\nIMPORTANT: Keep these credentials secure!")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\nError creating super admin: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = create_super_admin()
    sys.exit(0 if success else 1)