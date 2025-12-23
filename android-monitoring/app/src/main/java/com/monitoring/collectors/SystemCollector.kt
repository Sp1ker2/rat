package com.monitoring.collectors

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Build

data class SystemInfo(
    val batteryLevel: Int,
    val isCharging: Boolean,
    val batteryTemp: Float,
    val memoryUsage: Long,
    val storageUsage: Long,
    val timestamp: Long
)

class SystemCollector(private val context: Context) {
    
    fun getSystemInfo(): SystemInfo {
        return SystemInfo(
            batteryLevel = getBatteryLevel(),
            isCharging = isCharging(),
            batteryTemp = getBatteryTemperature(),
            memoryUsage = getMemoryUsage(),
            storageUsage = getStorageUsage(),
            timestamp = System.currentTimeMillis()
        )
    }
    
    private fun getBatteryLevel(): Int {
        val batteryStatus: Intent? = IntentFilter(Intent.ACTION_BATTERY_CHANGED).let { filter ->
            context.registerReceiver(null, filter)
        }
        
        val level = batteryStatus?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = batteryStatus?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
        
        return if (level != -1 && scale != -1) {
            (level / scale.toFloat() * 100).toInt()
        } else {
            -1
        }
    }
    
    private fun isCharging(): Boolean {
        val batteryStatus: Intent? = IntentFilter(Intent.ACTION_BATTERY_CHANGED).let { filter ->
            context.registerReceiver(null, filter)
        }
        
        val status = batteryStatus?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
        return status == BatteryManager.BATTERY_STATUS_CHARGING ||
                status == BatteryManager.BATTERY_STATUS_FULL
    }
    
    private fun getBatteryTemperature(): Float {
        val batteryStatus: Intent? = IntentFilter(Intent.ACTION_BATTERY_CHANGED).let { filter ->
            context.registerReceiver(null, filter)
        }
        
        val temp = batteryStatus?.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, -1) ?: -1
        return if (temp != -1) temp / 10.0f else -1f
    }
    
    private fun getMemoryUsage(): Long {
        val runtime = Runtime.getRuntime()
        return runtime.totalMemory() - runtime.freeMemory()
    }
    
    private fun getStorageUsage(): Long {
        val dataDir = context.filesDir
        return dataDir.usableSpace
    }
}

