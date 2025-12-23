# Quick start command
if (-not (Test-Path "venv")) { python -m venv venv }
& .\venv\Scripts\Activate.ps1
pip install -q -r requirements.txt
New-Item -ItemType Directory -Force -Path "monitoring-data\devices", "monitoring-data\admins" | Out-Null
$env:DATA_DIR = "$PWD\monitoring-data"; $env:SERVER_HOST = "127.0.0.1"; $env:DEBUG = "True"
Write-Host "🚀 Server: http://127.0.0.1:5000/docs | Login: admin/admin123" -ForegroundColor Green
uvicorn backend.main:app --host 127.0.0.1 --port 5000 --reload

