# -*- coding: utf-8 -*-
"""Quick start script for local development"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    print("Starting Kelya Virus locally...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ required!")
        sys.exit(1)
    print("OK: Python " + sys.version.split()[0])
    
    # Create data directories
    data_dir = Path("monitoring-data")
    (data_dir / "devices").mkdir(parents=True, exist_ok=True)
    (data_dir / "admins").mkdir(parents=True, exist_ok=True)
    print("OK: Data directories created")
    
    # Check and install dependencies
    print("Checking dependencies...")
    try:
        import uvicorn
        from jose import JWTError
        from passlib.context import CryptContext
        print("OK: Dependencies OK")
    except ImportError as e:
        print("WARNING: Missing dependency: " + str(e))
        print("Installing dependencies from requirements.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("OK: Dependencies installed")
    
    # Set environment variables
    os.environ["DATA_DIR"] = str(data_dir.absolute())
    os.environ["SERVER_HOST"] = "127.0.0.1"
    os.environ["SERVER_PORT"] = "5000"
    os.environ["DEBUG"] = "True"
    os.environ["ADMIN_USERNAME"] = "admin"
    os.environ["ADMIN_PASSWORD_HASH"] = "$2b$12$jycyShq4mYuKYm9B4AeeH.x/TCHtLo6a6RN19vt7.Y/N.FcddbHxq"
    os.environ["JWT_SECRET"] = "local-dev-secret-key-change-in-production"
    
    print("\nOK: Starting FastAPI server...")
    print("Server: http://127.0.0.1:5000")
    print("API docs: http://127.0.0.1:5000/docs")
    print("Login: admin / admin123")
    print("\nPress Ctrl+C to stop\n")
    
    # Run uvicorn
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=5000,
        reload=True
    )

if __name__ == "__main__":
    main()
