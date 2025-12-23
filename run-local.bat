@echo off
REM Batch script to run the monitoring system locally

echo 🚀 Starting Kelya Virus locally...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH!
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo 📥 Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Create data directories
echo 📁 Creating data directories...
if not exist "monitoring-data\devices" mkdir monitoring-data\devices
if not exist "monitoring-data\admins" mkdir monitoring-data\admins

REM Set environment variables for local development
set DATA_DIR=%CD%\monitoring-data
set SERVER_HOST=127.0.0.1
set SERVER_PORT=5000
set DEBUG=True
set ADMIN_USERNAME=admin
set ADMIN_PASSWORD_HASH=$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7qUXx9wH4u
set JWT_SECRET=local-dev-secret-key-change-in-production

REM Run the server
echo.
echo ✅ Starting FastAPI server...
echo 📍 Server will be available at: http://127.0.0.1:5000
echo 📚 API docs: http://127.0.0.1:5000/docs
echo 🔑 Login: admin / admin123
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn backend.main:app --host 127.0.0.1 --port 5000 --reload

pause

