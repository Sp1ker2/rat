package com.monitoring

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.monitoring.service.MonitoringService
import com.monitoring.utils.DeviceIdManager

class MainActivity : AppCompatActivity() {
    
    private lateinit var btnStart: Button
    private lateinit var btnStop: Button
    private lateinit var tvDeviceId: TextView
    private lateinit var tvDeviceName: TextView
    private lateinit var tvStatus: TextView
    
    private var isServiceRunning = false
    
    companion object {
        private const val REQUEST_CODE_PERMISSIONS = 10
        private val REQUIRED_PERMISSIONS = arrayOf(
            Manifest.permission.CAMERA,
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION
        )
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Initialize views
        btnStart = findViewById(R.id.btnStart)
        btnStop = findViewById(R.id.btnStop)
        tvDeviceId = findViewById(R.id.tvDeviceId)
        tvDeviceName = findViewById(R.id.tvDeviceName)
        tvStatus = findViewById(R.id.tvStatus)
        
        // Display device info
        val deviceId = DeviceIdManager.getDeviceId(this)
        val deviceName = DeviceIdManager.getDeviceName(this)
        
        tvDeviceId.text = "ID: $deviceId"
        tvDeviceName.text = "Name: $deviceName"
        
        // Buttons
        btnStart.setOnClickListener { startMonitoring() }
        btnStop.setOnClickListener { stopMonitoring() }
        
        updateUI()
        
        // Check permissions
        if (!allPermissionsGranted()) {
            ActivityCompat.requestPermissions(
                this, REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS
            )
        }
    }
    
    private fun startMonitoring() {
        if (!allPermissionsGranted()) {
            Toast.makeText(this, "Permissions required", Toast.LENGTH_SHORT).show()
            return
        }
        
        MonitoringService.start(this)
        isServiceRunning = true
        updateUI()
        
        Toast.makeText(this, "Monitoring started", Toast.LENGTH_SHORT).show()
    }
    
    private fun stopMonitoring() {
        MonitoringService.stop(this)
        isServiceRunning = false
        updateUI()
        
        Toast.makeText(this, "Monitoring stopped", Toast.LENGTH_SHORT).show()
    }
    
    private fun updateUI() {
        if (isServiceRunning) {
            btnStart.isEnabled = false
            btnStop.isEnabled = true
            tvStatus.text = "Status: Running"
            tvStatus.setTextColor(ContextCompat.getColor(this, android.R.color.holo_green_dark))
        } else {
            btnStart.isEnabled = true
            btnStop.isEnabled = false
            tvStatus.text = "Status: Stopped"
            tvStatus.setTextColor(ContextCompat.getColor(this, android.R.color.holo_red_dark))
        }
    }
    
    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(baseContext, it) == PackageManager.PERMISSION_GRANTED
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<String>, grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_CODE_PERMISSIONS) {
            if (allPermissionsGranted()) {
                Toast.makeText(this, "Permissions granted", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "Permissions denied", Toast.LENGTH_SHORT).show()
            }
        }
    }
}

