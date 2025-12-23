package com.monitoring.utils

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.telephony.TelephonyManager
import androidx.core.app.ActivityCompat
import java.util.*

object DeviceIdManager {
    private const val PREFS_NAME = "device_prefs"
    private const val KEY_DEVICE_ID = "device_id"
    private const val KEY_DEVICE_NAME = "device_name"
    
    fun getDeviceId(context: Context): String {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        var deviceId = prefs.getString(KEY_DEVICE_ID, null)
        
        if (deviceId == null) {
            // Generate new UUID
            deviceId = UUID.randomUUID().toString()
            prefs.edit().putString(KEY_DEVICE_ID, deviceId).apply()
        }
        
        return deviceId
    }
    
    fun getDeviceName(context: Context): String {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        var name = prefs.getString(KEY_DEVICE_NAME, null)
        
        if (name == null) {
            // Auto-generate name from device info
            name = "${Build.MANUFACTURER} ${Build.MODEL}".trim()
            if (name.isBlank()) {
                name = "Android Device"
            }
            prefs.edit().putString(KEY_DEVICE_NAME, name).apply()
        }
        
        return name
    }
    
    fun setDeviceName(context: Context, name: String) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_DEVICE_NAME, name)
            .apply()
    }
    
    fun getIMEI(context: Context): String? {
        if (ActivityCompat.checkSelfPermission(
                context,
                Manifest.permission.READ_PHONE_STATE
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            return null
        }
        
        return try {
            val telephonyManager = context.getSystemService(Context.TELEPHONY_SERVICE) as? TelephonyManager
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                telephonyManager?.imei
            } else {
                @Suppress("DEPRECATION")
                telephonyManager?.deviceId
            }
        } catch (e: Exception) {
            null
        }
    }
    
    fun getDeviceInfo(context: Context): Map<String, Any> {
        return mapOf(
            "id" to getDeviceId(context),
            "name" to getDeviceName(context),
            "imei" to (getIMEI(context) ?: ""),
            "model" to Build.MODEL,
            "manufacturer" to Build.MANUFACTURER,
            "android_version" to Build.VERSION.RELEASE,
            "sdk" to Build.VERSION.SDK_INT
        )
    }
}

