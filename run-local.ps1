# PowerShell script to run the monitoring system locally

Write-Host "🚀 Starting Kelya Virus locally..." -ForegroundColor Green

# Check if Python is installed
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python is not installed or not in PATH!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install/upgrade dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

# Create data directories
Write-Host "📁 Creating data directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "monitoring-data\devices" | Out-Null
New-Item -ItemType Directory -Force -Path "monitoring-data\admins" | Out-Null

# Set environment variables for local development
$env:DATA_DIR = "$PWD\monitoring-data"
$env:SERVER_HOST = "127.0.0.1"
$env:SERVER_PORT = "5000"
$env:DEBUG = "True"
$env:ADMIN_USERNAME = "admin"
$env:ADMIN_PASSWORD_HASH = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7qUXx9wH4u'  # "admin123"
$env:JWT_SECRET = "local-dev-secret-key-change-in-production"

# Run the server
Write-Host "`n✅ Starting FastAPI server..." -ForegroundColor Green
Write-Host "📍 Server will be available at: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "📚 API docs: http://127.0.0.1:5000/docs" -ForegroundColor Cyan
Write-Host "🔑 Login: admin / admin123" -ForegroundColor Yellow
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Gray

uvicorn backend.main:app --host 127.0.0.1 --port 5000 --reload

