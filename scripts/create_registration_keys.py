#!/usr/bin/env python3
"""
Create initial registration keys for new user signups
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import getpass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

def create_registration_keys():
    """Create registration keys using admin credentials"""
    
    try:
        # Import after path setup
        from backend.db.database import get_db
        from backend.db.models import User
        from backend.db.admin_models import AdminUser, RegistrationKey
        from backend.auth.jwt_handler import jwt_handler
        from sqlalchemy.orm import Session
        import uuid
        import secrets
        import string
        
        print("🔑 Creating Registration Keys for Lily AI")
        print("=" * 50)
        
        # Authenticate admin user first
        print("Admin authentication required:")
        admin_email = input("Enter admin email: ").strip()
        if not admin_email:
            print("❌ Admin email is required")
            return False
            
        admin_password = getpass.getpass("Enter admin password: ")
        if not admin_password:
            print("❌ Admin password is required")
            return False
        
        # Create database session
        db = next(get_db())
        
        try:
            # Verify admin user
            admin_user = db.query(User).filter(User.email == admin_email).first()
            if not admin_user:
                print("❌ Admin user not found")
                return False
                
            if not jwt_handler.verify_password(admin_password, admin_user.hashed_password):
                print("❌ Invalid admin password")
                return False
                
            if not admin_user.is_superuser:
                print("❌ User is not a super admin")
                return False
            
            print(f"✅ Admin authenticated: {admin_user.username}")
            print()
            
            # Get registration key parameters
            print("Registration Key Configuration:")
            
            description = input("Enter description (e.g., 'Initial launch keys'): ").strip() or "Initial registration keys"
            
            # Max uses
            while True:
                try:
                    max_uses_input = input("Enter max uses per key (default: 10): ").strip()
                    max_uses = int(max_uses_input) if max_uses_input else 10
                    if max_uses > 0:
                        break
                    else:
                        print("❌ Max uses must be greater than 0")
                except ValueError:
                    print("❌ Please enter a valid number")
            
            # Number of keys to create
            while True:
                try:
                    num_keys_input = input("Enter number of keys to create (default: 3): ").strip()
                    num_keys = int(num_keys_input) if num_keys_input else 3
                    if num_keys > 0:
                        break
                    else:
                        print("❌ Number of keys must be greater than 0")
                except ValueError:
                    print("❌ Please enter a valid number")
            
            # Expiry date
            while True:
                try:
                    expiry_input = input("Enter expiry date (YYYY-MM-DD) or days from now (default: 90 days): ").strip()
                    if not expiry_input:
                        expires_at = datetime.utcnow() + timedelta(days=90)
                        break
                    elif expiry_input.isdigit():
                        days = int(expiry_input)
                        expires_at = datetime.utcnow() + timedelta(days=days)
                        break
                    else:
                        expires_at = datetime.strptime(expiry_input, "%Y-%m-%d")
                        break
                except ValueError:
                    print("❌ Please enter a valid date (YYYY-MM-DD) or number of days")
            
            # Email domain restriction (optional)
            allowed_domains = input("Enter allowed email domains (comma-separated, optional): ").strip()
            allowed_domains_list = [d.strip() for d in allowed_domains.split(",")] if allowed_domains else None
            
            print()
            print("📋 Registration Key Summary:")
            print(f"   Description: {description}")
            print(f"   Number of keys: {num_keys}")
            print(f"   Max uses per key: {max_uses}")
            print(f"   Expires at: {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"   Allowed domains: {allowed_domains_list or 'Any'}")
            print()
            
            confirm = input("Create these registration keys? (yes/no): ")
            if confirm.lower() != "yes":
                print("❌ Cancelled")
                return False
            
            # Create registration keys
            created_keys = []
            
            for i in range(num_keys):
                # Generate secure random key
                key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
                
                registration_key = RegistrationKey(
                    id=str(uuid.uuid4()),
                    key=key,
                    description=f"{description} - Key {i+1}",
                    max_uses=max_uses,
                    current_uses=0,
                    expires_at=expires_at,
                    allowed_domains=allowed_domains_list,
                    is_active=True,
                    created_by_id=admin_user.id
                )
                
                db.add(registration_key)
                created_keys.append((key, registration_key.id))
            
            db.commit()
            
            print("✅ Registration keys created successfully!")
            print()
            print("🔑 Generated Registration Keys:")
            print("=" * 80)
            
            for i, (key, key_id) in enumerate(created_keys, 1):
                print(f"Key {i}:")
                print(f"   ID: {key_id}")
                print(f"   Key: {key}")
                print(f"   Uses: 0/{max_uses}")
                print(f"   Expires: {expires_at.strftime('%Y-%m-%d')}")
                print()
            
            print("📝 Usage Instructions:")
            print("   - Share these keys with users who need to register")
            print("   - Users will enter the key during signup")
            print("   - Each key can be used up to the max uses limit")
            print("   - Keys automatically expire on the specified date")
            print("   - Track key usage through the admin dashboard")
            print()
            
            # Save to file option
            save_to_file = input("Save keys to file? (yes/no): ")
            if save_to_file.lower() == "yes":
                filename = f"registration_keys_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                
                with open(filename, 'w') as f:
                    f.write(f"Lily AI - Registration Keys\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Created by: {admin_user.email}\n")
                    f.write(f"Description: {description}\n")
                    f.write(f"Max uses per key: {max_uses}\n")
                    f.write(f"Expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
                    f.write(f"Allowed domains: {allowed_domains_list or 'Any'}\n")
                    f.write(f"\n")
                    f.write("Registration Keys:\n")
                    f.write("=" * 50 + "\n")
                    
                    for i, (key, key_id) in enumerate(created_keys, 1):
                        f.write(f"Key {i}: {key}\n")
                        f.write(f"ID: {key_id}\n\n")
                
                print(f"✅ Keys saved to: {filename}")
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error creating registration keys: {e}")
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
    print("🚀 Lily AI - Registration Key Creation Script")
    print()
    
    # Check environment
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "production":
        print("⚠️  PRODUCTION ENVIRONMENT DETECTED")
        confirm = input("Are you sure you want to create registration keys in production? (yes/no): ")
        if confirm.lower() != "yes":
            print("❌ Cancelled")
            sys.exit(1)
    
    success = create_registration_keys()
    if success:
        print("🎉 Registration keys created successfully!")
        sys.exit(0)
    else:
        print("💥 Failed to create registration keys")
        sys.exit(1)