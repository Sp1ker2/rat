# Android Monitoring Client

Android application for remote device monitoring.

## Features

- **Camera Streaming**: Real-time camera feed (front/back)
- **Location Tracking**: Continuous GPS location updates
- **System Monitoring**: Battery, memory, storage information
- **Background Service**: Runs as foreground service
- **WebSocket Communication**: Low-latency connection to server

## Setup

### Prerequisites

- Android Studio Arctic Fox or later
- Android SDK 24+ (Android 7.0+)
- Device with camera and GPS

### Installation

1. Open `android-monitoring` folder in Android Studio
2. Update `SERVER_URL` in `MonitoringService.kt`:
   ```kotlin
   const val SERVER_URL = "wss://your-domain.com/ws/device"
   ```
3. Build and install on device

### Permissions

The app requires:
- **CAMERA**: For camera streaming
- **ACCESS_FINE_LOCATION**: For GPS tracking
- **ACCESS_COARSE_LOCATION**: For network-based location
- **INTERNET**: For server connection
- **FOREGROUND_SERVICE**: For background monitoring
- **READ_PHONE_STATE**: For device IMEI (optional)

## Usage

1. Launch app
2. Grant required permissions
3. Tap "Start Monitoring"
4. App will run in background with notification
5. View device on admin panel at `https://your-domain.com`

## Architecture

```
com.monitoring/
├── MainActivity.kt              # Main activity
├── service/
│   ├── MonitoringService.kt    # Foreground service
│   └── WebSocketClient.kt      # WebSocket handler
├── collectors/
│   ├── CameraCollector.kt      # Camera frames
│   ├── LocationCollector.kt    # GPS data
│   └── SystemCollector.kt      # System info
└── utils/
    └── DeviceId.kt             # Device identification
```

## Configuration

### Camera Settings
- Default FPS: 5 frames per second
- Resolution: 640x480
- Compression: JPEG 80%

### Location Updates
- Interval: 10 seconds
- Priority: High accuracy

### System Info
- Update interval: 30 seconds
- Includes: Battery, memory, storage

## Customization

### Change Camera FPS
Edit `MonitoringService.kt`:
```kotlin
private val cameraFpsLimit = 10 // Set to desired FPS
```

### Change Server URL
Edit `MonitoringService.kt`:
```kotlin
const val SERVER_URL = "wss://your-server.com/ws/device"
```

### Modify Data Collection
Edit respective collectors in `collectors/` package.

## Troubleshooting

### App crashes on start
- Check all permissions are granted
- Ensure camera is available
- Check LogCat for errors

### Cannot connect to server
- Verify SERVER_URL is correct
- Check internet connection
- Ensure server is running and accessible
- Check SSL certificate is valid

### High battery usage
- Reduce camera FPS
- Increase location update interval
- Optimize system info collection frequency

## Building Release APK

1. Create keystore:
   ```bash
   keytool -genkey -v -keystore monitoring.keystore -alias monitoring -keyalg RSA -keysize 2048 -validity 10000
   ```

2. Configure `app/build.gradle.kts`:
   ```kotlin
   signingConfigs {
       create("release") {
           storeFile = file("monitoring.keystore")
           storePassword = "your-password"
           keyAlias = "monitoring"
           keyPassword = "your-password"
       }
   }
   ```

3. Build:
   ```bash
   ./gradlew assembleRelease
   ```

## License

MIT License

