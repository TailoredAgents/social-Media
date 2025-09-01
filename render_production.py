#!/usr/bin/env python3
"""
Production entry point for Render deployment
Runs FastAPI with uvicorn in production mode
"""
import os
import sys
import uvicorn
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def main():
    """Main entry point for Render production deployment"""
    print("🚀 Starting AI Social Media Content Agent in production mode...")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Backend path added: {backend_path}")
    
    # Get port from environment (Render sets this)
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting server on {host}:{port}")
    
    # Run uvicorn with production settings
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        workers=1,  # Single worker for free tier
        log_level="info",
        access_log=True,
        reload=False,  # No reload in production
        loop="uvloop" if os.name != "nt" else "asyncio"
    )

if __name__ == "__main__":
    main()