#!/usr/bin/env python3
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

# Set PYTHONPATH environment variable
os.environ['PYTHONPATH'] = os.getcwd()

# Now start the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )