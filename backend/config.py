"""Configuration settings for the monitoring system"""
import os
from pathlib import Path

# Server settings
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")  # 127.0.0.1 for local, 0.0.0.0 for production
SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Data storage
# Use local directory for development, /root/monitoring-data for production
DATA_DIR = Path(os.getenv("DATA_DIR", "./monitoring-data"))
DEVICES_DIR = DATA_DIR / "devices"
ADMINS_DIR = DATA_DIR / "admins"

# Create directories
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEVICES_DIR.mkdir(parents=True, exist_ok=True)
ADMINS_DIR.mkdir(parents=True, exist_ok=True)

# Admin authentication
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "$2b$12$jycyShq4mYuKYm9B4AeeH.x/TCHtLo6a6RN19vt7.Y/N.FcddbHxq")  # "admin123"

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60 * 24  # 24 hours

# WebSocket settings
WS_PING_INTERVAL = 30  # seconds
WS_TIMEOUT = 60  # seconds

# Device settings
MAX_FRAME_SIZE = 5 * 1024 * 1024  # 5MB
CAMERA_FPS_LIMIT = 10
LOCATION_UPDATE_INTERVAL = 10  # seconds

