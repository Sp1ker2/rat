# Build for Python FastAPI + pre-built React frontend

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy frontend build (or create empty dir if not exists)
COPY frontend/build/ ./frontend/build/

# Create data directories
RUN mkdir -p /root/monitoring-data/devices /root/monitoring-data/admins

# Expose port
EXPOSE 5000

# Environment variables
ENV DATA_DIR=/root/monitoring-data
ENV ADMIN_USERNAME=admin
ENV ADMIN_PASSWORD_HASH=\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7qUXx9wH4u
ENV JWT_SECRET=your-secret-key-change-in-production

# Run application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "5000"]
