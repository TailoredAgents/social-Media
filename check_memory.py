#!/usr/bin/env python3
"""
Memory diagnostic script for Render deployment
Run this to see what's using memory
"""
import sys
import psutil
import os

def get_memory_info():
    """Get current memory usage"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    print("🧠 MEMORY DIAGNOSTIC")
    print("=" * 50)
    print(f"RSS Memory: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS Memory: {memory_info.vms / 1024 / 1024:.2f} MB")
    
    # System memory
    sys_memory = psutil.virtual_memory()
    print(f"System Total: {sys_memory.total / 1024 / 1024:.2f} MB")
    print(f"System Available: {sys_memory.available / 1024 / 1024:.2f} MB")
    print(f"System Used: {sys_memory.used / 1024 / 1024:.2f} MB")
    
    return memory_info.rss / 1024 / 1024

def check_imports():
    """Check memory usage of different imports"""
    import gc
    
    print("\n📦 IMPORT MEMORY USAGE")
    print("=" * 50)
    
    base_memory = get_memory_info()
    print(f"Base Python: {base_memory:.2f} MB")
    
    # Test heavy imports
    heavy_imports = [
        ("import openai", "OpenAI SDK"),
        ("from celery import Celery", "Celery"),
        ("import sqlalchemy", "SQLAlchemy"),
        ("import numpy", "NumPy"),
    ]
    
    for import_stmt, name in heavy_imports:
        try:
            before = get_memory_info()
            exec(import_stmt)
            after = get_memory_info()
            print(f"{name}: +{after - before:.2f} MB")
        except ImportError as e:
            print(f"{name}: Not installed ({e})")
        except Exception as e:
            print(f"{name}: Error ({e})")
    
    # Test CrewAI if available
    try:
        before = get_memory_info()
        import crewai
        after = get_memory_info()
        print(f"CrewAI: +{after - before:.2f} MB")
    except ImportError:
        print("CrewAI: Not installed")
    except Exception as e:
        print(f"CrewAI: Error ({e})")

if __name__ == "__main__":
    check_imports()
    
    print("\n🎯 RECOMMENDATIONS")
    print("=" * 50)
    current_memory = get_memory_info()
    
    if current_memory > 400:
        print("❌ High memory usage detected!")
        print("- Consider upgrading to 2GB plan ($25/month)")
        print("- Or use lightweight alternatives")
    elif current_memory > 200:
        print("⚠️  Moderate memory usage")
        print("- Should work with 512MB but close to limit")
    else:
        print("✅ Low memory usage - should work fine")