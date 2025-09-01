#!/usr/bin/env python3
"""
Create super admin user for production deployment
"""
import sys
import os
import getpass
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

def create_super_admin():
    """Create super admin user interactively"""
    
    try:
        # Import after path setup
        from backend.db.database import get_db, engine
        from backend.db.models import User
        from backend.db.admin_models import AdminUser
        from backend.db.multi_tenant_models import Organization, Role, UserOrganizationRole
        from backend.auth.jwt_handler import jwt_handler
        from sqlalchemy.orm import Session
        import uuid
        
        print("🔐 Creating Super Admin User for Lily AI")
        print("=" * 50)
        
        # Get admin details interactively
        email = input("Enter admin email: ").strip()
        if not email:
            print("❌ Email is required")
            return False
            
        username = input("Enter admin username: ").strip()
        if not username:
            print("❌ Username is required")
            return False
            
        full_name = input("Enter admin full name: ").strip() or username
        
        # Get password securely
        while True:
            password = getpass.getpass("Enter admin password: ")
            password_confirm = getpass.getpass("Confirm admin password: ")
            
            if password != password_confirm:
                print("❌ Passwords don't match. Try again.")
                continue
                
            if len(password) < 8:
                print("❌ Password must be at least 8 characters.")
                continue
                
            break
        
        # Create database session
        db = next(get_db())
        
        try:
            # Check if admin already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                print(f"❌ User with email {email} already exists")
                return False
                
            existing_username = db.query(User).filter(User.username == username).first()
            if existing_username:
                print(f"❌ User with username {username} already exists")
                return False
            
            # Hash password
            hashed_password = jwt_handler.hash_password(password)
            
            # Create super admin user
            super_admin = User(
                email=email,
                username=username,
                full_name=full_name,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True,  # This is the key field for super admin
                tier="enterprise",
                auth_provider="local"
            )
            
            db.add(super_admin)
            db.commit()
            db.refresh(super_admin)
            
            print(f"✅ Super admin user created with ID: {super_admin.id}")
            
            # Create admin record
            admin_user = AdminUser(
                user_id=super_admin.id,
                role="super_admin",
                is_active=True,
                created_by_id=super_admin.id  # Self-created
            )
            
            db.add(admin_user)
            
            # Create personal organization for admin
            admin_org = Organization(
                id=str(uuid.uuid4()),
                name=f"{full_name}'s Admin Organization",
                slug=f"{username}-admin-org",
                description="Super admin personal organization",
                plan_type="enterprise",
                max_users=100,
                max_teams=20,
                max_social_accounts=50,
                owner_id=super_admin.id
            )
            
            db.add(admin_org)
            db.flush()
            
            # Set as default organization
            super_admin.default_organization_id = admin_org.id
            
            # Assign super admin role if it exists
            super_admin_role = db.query(Role).filter(Role.name == 'super_admin').first()
            if super_admin_role:
                user_org_role = UserOrganizationRole(
                    id=str(uuid.uuid4()),
                    user_id=super_admin.id,
                    organization_id=admin_org.id,
                    role_id=super_admin_role.id,
                    assigned_by_id=super_admin.id,
                    is_active=True
                )
                db.add(user_org_role)
            
            db.commit()
            
            print("✅ Admin organization created")
            print("✅ Super admin setup complete!")
            print()
            print("📝 Super Admin Details:")
            print(f"   Email: {email}")
            print(f"   Username: {username}")
            print(f"   User ID: {super_admin.id}")
            print(f"   Organization ID: {admin_org.id}")
            print()
            print("🔑 You can now use these credentials to:")
            print("   - Access admin API endpoints")
            print("   - Create registration keys")
            print("   - Manage users and organizations")
            print("   - Access production admin dashboard")
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error creating super admin: {e}")
            return False
        finally:
            db.close()
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root and all dependencies are installed.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Lily AI - Super Admin Creation Script")
    print()
    
    # Check environment
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "production":
        print("⚠️  PRODUCTION ENVIRONMENT DETECTED")
        confirm = input("Are you sure you want to create super admin in production? (yes/no): ")
        if confirm.lower() != "yes":
            print("❌ Cancelled")
            sys.exit(1)
    
    success = create_super_admin()
    if success:
        print("🎉 Super admin created successfully!")
        sys.exit(0)
    else:
        print("💥 Failed to create super admin")
        sys.exit(1)