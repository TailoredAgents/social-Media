#!/usr/bin/env python3
"""
Force install critical dependencies for Render deployment
This script ensures all required packages are installed before app starts
"""
import subprocess
import sys
import os

def install_package(package):
    """Install a single package with force reinstall"""
    try:
        print(f"Installing {package}...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--force-reinstall", "--no-cache-dir", package
        ])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    """Install all critical dependencies"""
    critical_packages = [
        "sqlalchemy==2.0.36",
        "structlog==25.4.0", 
        "psycopg2-binary==2.9.10",
        "passlib[bcrypt]==1.7.4",
        "fastapi==0.115.6",
        "uvicorn[standard]==0.32.1",
        "python-dotenv==1.1.1",
        "pydantic==2.11.7",
        "pydantic-settings==2.10.1",
        "requests==2.32.3",
        "python-jose[cryptography]==3.3.0"
    ]
    
    print("🔧 Installing critical production dependencies...")
    print("=" * 60)
    
    success_count = 0
    for package in critical_packages:
        if install_package(package):
            success_count += 1
    
    print("=" * 60)
    print(f"Installation complete: {success_count}/{len(critical_packages)} packages installed")
    
    if success_count == len(critical_packages):
        print("✅ All critical dependencies installed successfully!")
        return 0
    else:
        print("❌ Some dependencies failed to install")
        return 1

if __name__ == "__main__":
    sys.exit(main())