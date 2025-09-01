#!/usr/bin/env python3
"""
Comprehensive backend diagnostic script for Render deployment
Checks all dependencies, imports, and configuration
"""
import sys
import os
import importlib
import subprocess

def check_python_version():
    """Check Python version"""
    print(f"🐍 Python version: {sys.version}")
    return True

def check_critical_packages():
    """Check if all critical packages are installed"""
    critical_packages = [
        "sqlalchemy",
        "structlog", 
        "psycopg2",
        "passlib",
        "fastapi",
        "uvicorn",
        "pydantic",
        "requests"
    ]
    
    print("\n📦 Checking critical packages...")
    missing_packages = []
    
    for package in critical_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError as e:
            print(f"❌ {package} - {e}")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def check_backend_imports():
    """Check if backend modules can be imported"""
    print("\n🔧 Checking backend imports...")
    
    # Add backend to path
    backend_path = os.path.join(os.getcwd(), "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    imports_to_check = [
        ("backend.core.env_validator_simple", "validate_environment"),
        ("backend.core.audit_logger", "AuditTrackingMiddleware"),
        ("backend.db.models", "User"),
        ("backend.api.auth", "router"),
        ("backend.api.admin", "router"),
        ("app", "app")
    ]
    
    failed_imports = []
    
    for module_name, item_name in imports_to_check:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, item_name):
                print(f"✅ {module_name}.{item_name}")
            else:
                print(f"⚠️  {module_name} imported but missing {item_name}")
                failed_imports.append(f"{module_name}.{item_name}")
        except ImportError as e:
            print(f"❌ {module_name} - {e}")
            failed_imports.append(module_name)
    
    return len(failed_imports) == 0, failed_imports

def check_environment_variables():
    """Check critical environment variables"""
    print("\n🔧 Checking environment variables...")
    
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY"
    ]
    
    optional_vars = [
        "CORS_ORIGINS",
        "ALLOWED_ORIGINS"
    ]
    
    missing_required = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var} = {value[:20]}...")
        else:
            print(f"❌ {var} - NOT SET")
            missing_required.append(var)
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var} = {value}")
        else:
            print(f"⚠️  {var} - not set (optional)")
    
    return len(missing_required) == 0, missing_required

def test_fastapi_app():
    """Test if FastAPI app can be created"""
    print("\n🚀 Testing FastAPI app creation...")
    
    try:
        # Set required environment variables if not set
        if not os.getenv("SECRET_KEY"):
            os.environ["SECRET_KEY"] = "test-secret-key-for-diagnosis"
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite:///test.db"
        
        from app import app
        print(f"✅ FastAPI app created successfully")
        print(f"✅ App title: {app.title}")
        
        # Count routes
        routes = [route for route in app.routes if hasattr(route, 'path')]
        print(f"✅ Total routes: {len(routes)}")
        
        # Look for API routes
        api_routes = [route for route in routes if '/api/' in str(route.path)]
        print(f"✅ API routes: {len(api_routes)}")
        
        if len(api_routes) > 0:
            print("✅ Sample API routes:")
            for route in api_routes[:5]:  # Show first 5
                print(f"   - {route.path}")
        
        return True, None
        
    except Exception as e:
        print(f"❌ FastAPI app creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

def install_missing_packages(packages):
    """Install missing packages"""
    if not packages:
        return True
    
    print(f"\n📥 Installing missing packages: {packages}")
    
    for package in packages:
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "--force-reinstall", "--no-cache-dir", package
            ])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def main():
    """Run comprehensive diagnosis"""
    print("🔍 BACKEND DIAGNOSTIC REPORT")
    print("=" * 60)
    
    # Check Python version
    check_python_version()
    
    # Check packages
    packages_ok, missing_packages = check_critical_packages()
    
    # Try to install missing packages
    if not packages_ok:
        print(f"\n🔧 Attempting to install missing packages...")
        if install_missing_packages(missing_packages):
            print("✅ Missing packages installed, re-checking...")
            packages_ok, _ = check_critical_packages()
    
    # Check environment variables
    env_ok, missing_env = check_environment_variables()
    
    # Check backend imports
    imports_ok, failed_imports = check_backend_imports()
    
    # Test FastAPI app
    app_ok, app_error = test_fastapi_app()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    print(f"✅ Packages: {'OK' if packages_ok else 'FAILED'}")
    print(f"✅ Environment: {'OK' if env_ok else 'FAILED'}")
    print(f"✅ Imports: {'OK' if imports_ok else 'FAILED'}")
    print(f"✅ FastAPI App: {'OK' if app_ok else 'FAILED'}")
    
    if not packages_ok:
        print(f"\n❌ Missing packages: {missing_packages}")
    
    if not env_ok:
        print(f"\n❌ Missing environment variables: {missing_env}")
    
    if not imports_ok:
        print(f"\n❌ Failed imports: {failed_imports}")
    
    if not app_ok:
        print(f"\n❌ App error: {app_error}")
    
    overall_ok = packages_ok and env_ok and imports_ok and app_ok
    
    print(f"\n🎯 OVERALL STATUS: {'✅ READY TO START' if overall_ok else '❌ NEEDS FIXES'}")
    
    if overall_ok:
        print("\n🚀 Backend should start successfully with: python app.py")
    else:
        print("\n🔧 Fix the issues above before starting the backend")
    
    return 0 if overall_ok else 1

if __name__ == "__main__":
    sys.exit(main())