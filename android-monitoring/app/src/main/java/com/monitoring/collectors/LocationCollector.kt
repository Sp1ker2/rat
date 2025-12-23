package com.monitoring.collectors

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.os.Looper
import androidx.core.app.ActivityCompat
import com.google.android.gms.location.*

data class LocationData(
    val lat: Double,
    val lon: Double,
    val accuracy: Float?,
    val timestamp: Long
)

class LocationCollector(private val context: Context) {
    private lateinit var fusedLocationClient: FusedLocationProviderClient
    private lateinit var locationCallback: LocationCallback
    private var callback: ((LocationData) -> Unit)? = null
    private var isStarted = false
    
    fun start(onLocation: (LocationData) -> Unit) {
        callback = onLocation
        isStarted = true
        
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(context)
        
        // Check permission
        if (ActivityCompat.checkSelfPermission(
                context,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            return
        }
        
        // Get last known location first
        fusedLocationClient.lastLocation.addOnSuccessListener { location ->
            location?.let {
                sendLocation(it)
            }
        }
        
        // Setup location callback
        locationCallback = object : LocationCallback() {
            override fun onLocationResult(locationResult: LocationResult) {
                locationResult.lastLocation?.let { location ->
                    sendLocation(location)
                }
            }
        }
        
        // Create location request
        val locationRequest = LocationRequest.Builder(
            Priority.PRIORITY_HIGH_ACCURACY,
            10000 // 10 seconds
        ).apply {
            setMinUpdateIntervalMillis(5000) // 5 seconds minimum
            setMaxUpdateDelayMillis(15000) // 15 seconds maximum
        }.build()
        
        // Request location updates
        try {
            fusedLocationClient.requestLocationUpdates(
                locationRequest,
                locationCallback,
                Looper.getMainLooper()
            )
        } catch (e: SecurityException) {
            e.printStackTrace()
        }
    }
    
    fun stop() {
        isStarted = false
        if (::fusedLocationClient.isInitialized) {
            fusedLocationClient.removeLocationUpdates(locationCallback)
        }
        callback = null
    }
    
    fun getCurrentLocation(onLocation: (LocationData?) -> Unit) {
        if (ActivityCompat.checkSelfPermission(
                context,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            onLocation(null)
            return
        }
        
        fusedLocationClient.lastLocation.addOnSuccessListener { location ->
            if (location != null) {
                onLocation(createLocationData(location))
            } else {
                onLocation(null)
            }
        }
    }
    
    private fun sendLocation(location: Location) {
        if (!isStarted) return
        
        val locationData = createLocationData(location)
        callback?.invoke(locationData)
    }
    
    private fun createLocationData(location: Location): LocationData {
        return LocationData(
            lat = location.latitude,
            lon = location.longitude,
            accuracy = location.accuracy,
            timestamp = System.currentTimeMillis()
        )
    }
}

