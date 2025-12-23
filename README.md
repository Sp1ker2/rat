# Remote Android Monitoring System

A complete remote monitoring solution for Android devices with real-time camera streaming, GPS tracking, and system information monitoring.

## Architecture

- **Backend**: FastAPI (Python) with WebSocket support
- **Frontend**: React with TypeScript
- **Android Client**: Kotlin with CameraX and Location Services
- **Deployment**: Docker + Ansible

## Features

### Android Device Monitoring
- ✅ Real-time camera streaming (front/back)
- ✅ GPS location tracking with history
- ✅ System information (battery, memory, storage)
- ✅ Background service for continuous monitoring
- ✅ WebSocket communication for low latency

### Admin Web Panel
- ✅ Responsive dashboard with device cards
- ✅ Real-time device status updates
- ✅ Interactive map with location history
- ✅ Camera switching and live view
- ✅ JWT authentication
- ✅ WebSocket real-time updates

## Quick Start

### 1. Deploy to Server (Recommended)

```bash
# Run deployment via Docker-based Ansible
powershell -ExecutionPolicy Bypass -File deploy.ps1
```

### 2. Local Development

#### Backend
```bash
cd backend
pip install -r ../requirements.txt
python -m uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

#### Android Client
Open `android-monitoring` in Android Studio and run on device.

## Configuration

### Backend Environment Variables
- `ADMIN_USERNAME`: Admin username (default: admin)
- `ADMIN_PASSWORD_HASH`: Bcrypt password hash (default: admin123)
- `JWT_SECRET`: Secret key for JWT tokens
- `DATA_DIR`: Data storage directory

### Android Client
Update server URL in `MonitoringService.kt`:
```kotlin
const val SERVER_URL = "wss://your-domain.com/ws/device"
```

## Default Credentials

- **Username**: admin
- **Password**: admin123

⚠️ **Change these in production!**

## Server Requirements

- Ubuntu 22.04+ or similar
- Docker & Docker Compose
- Nginx with SSL certificate
- Ports: 80 (HTTP), 443 (HTTPS), 5000 (app)

## File Structure

```
.
├── backend/                 # FastAPI backend
│   ├── auth/               # Authentication
│   ├── devices/            # Device management
│   ├── websocket/          # WebSocket handlers
│   ├── storage/            # File storage
│   └── main.py             # Entry point
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── api/            # API clients
│   │   ├── hooks/          # Custom hooks
│   │   └── types/          # TypeScript types
│   └── public/
├── android-monitoring/     # Android client
│   └── app/src/main/java/com/monitoring/
│       ├── collectors/     # Data collectors
│       ├── service/        # Background service
│       └── utils/          # Utilities
├── ansible/                # Deployment automation
│   ├── deploy.yml          # Main playbook
│   └── inventory.yml       # Server inventory
├── Dockerfile              # Multi-stage build
├── docker-compose.yml      # Container orchestration
└── deploy.ps1              # Windows deployment script
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Admin login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/verify` - Verify token

### Devices
- `GET /api/devices` - List all devices
- `GET /api/devices/{id}` - Get device details
- `POST /api/devices/{id}/command` - Send command
- `GET /api/devices/{id}/camera/{camera}` - Get camera frame
- `GET /api/devices/{id}/location` - Get location history

### WebSocket
- `WS /ws/device` - Device connection
- `WS /ws/admin` - Admin connection

## WebSocket Protocol

### Device → Server
```json
{
  "type": "register",
  "device_info": {
    "id": "uuid",
    "name": "Device Name",
    "model": "...",
    "manufacturer": "...",
    "android_version": "..."
  }
}

{
  "type": "camera_frame",
  "camera": "back",
  "data": "base64...",
  "width": 640,
  "height": 480,
  "timestamp": 1234567890
}

{
  "type": "location_update",
  "lat": 55.779376,
  "lon": 37.589386,
  "accuracy": 10.5,
  "timestamp": 1234567890
}
```

### Server → Device
```json
{
  "type": "command",
  "command": "switch_camera",
  "data": { "camera": "front" }
}
```

## Security

- HTTPS with Let's Encrypt SSL
- JWT-based authentication
- WebSocket token verification
- Password hashing with bcrypt
- CORS configuration
- Environment variable secrets

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs monitoring-system

# Restart container
docker restart monitoring-system
```

### Android app can't connect
1. Check SERVER_URL in MonitoringService.kt
2. Ensure device has internet connection
3. Verify SSL certificate is valid
4. Check firewall rules on server

### Admin panel shows no devices
1. Verify Android app is running
2. Check WebSocket connection in browser console
3. Ensure backend is running: `docker ps`

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open a GitHub issue.

