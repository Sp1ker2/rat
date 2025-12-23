package com.example.webrtcstream

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageFormat
import android.graphics.Rect
import android.graphics.YuvImage
import android.os.Bundle
import android.util.Base64
import android.util.Log
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.gson.Gson
import kotlinx.coroutines.*
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {
    
    // UI элементы
    private lateinit var previewView: PreviewView
    private lateinit var btnStart: Button
    private lateinit var btnStop: Button
    private lateinit var tvStatus: TextView
    private lateinit var tvFrameCount: TextView
    
    // Camera
    private var imageAnalyzer: ImageAnalysis? = null
    private lateinit var cameraExecutor: ExecutorService
    
    // Streaming
    private var isStreaming = false
    private val serverUrl = "https://kelyastream.duckdns.org"
    private val httpClient = OkHttpClient()
    private val gson = Gson()
    
    private var frameCount = 0
    private var lastFrameTime = 0L
    private val frameInterval = 100L // Отправлять кадр каждые 100мс (10 FPS)
    
    companion object {
        private const val REQUEST_CODE_PERMISSIONS = 10
        private val REQUIRED_PERMISSIONS = arrayOf(Manifest.permission.CAMERA)
        private const val TAG = "WebRTCStream"
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Инициализация UI
        previewView = findViewById(R.id.previewView)
        btnStart = findViewById(R.id.btnStart)
        btnStop = findViewById(R.id.btnStop)
        tvStatus = findViewById(R.id.tvStatus)
        tvFrameCount = findViewById(R.id.tvFrameCount)
        
        // Кнопки
        btnStart.setOnClickListener { startStreaming() }
        btnStop.setOnClickListener { stopStreaming() }
        btnStop.isEnabled = false
        
        // Camera executor
        cameraExecutor = Executors.newSingleThreadExecutor()
        
        // Проверка разрешений
        if (allPermissionsGranted()) {
            startCamera()
        } else {
            ActivityCompat.requestPermissions(
                this, REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS
            )
        }
        
        // Проверка подключения к серверу
        checkServerConnection()
    }
    
    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        
        cameraProviderFuture.addListener({
            val cameraProvider = cameraProviderFuture.get()
            
            // Preview
            val preview = Preview.Builder()
                .build()
                .also {
                    it.setSurfaceProvider(previewView.surfaceProvider)
                }
            
            // Image analyzer для захвата кадров
            imageAnalyzer = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
                .also {
                    it.setAnalyzer(cameraExecutor, FrameAnalyzer())
                }
            
            // Выбрать заднюю камеру
            val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
            
            try {
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    this, cameraSelector, preview, imageAnalyzer
                )
            } catch (exc: Exception) {
                Log.e(TAG, "Camera binding failed", exc)
            }
            
        }, ContextCompat.getMainExecutor(this))
    }
    
    private fun startStreaming() {
        isStreaming = true
        frameCount = 0
        btnStart.isEnabled = false
        btnStop.isEnabled = true
        updateStatus("Стрим запущен")
        Toast.makeText(this, "Стрим начат", Toast.LENGTH_SHORT).show()
    }
    
    private fun stopStreaming() {
        isStreaming = false
        btnStart.isEnabled = true
        btnStop.isEnabled = false
        updateStatus("Стрим остановлен")
        Toast.makeText(this, "Стрим остановлен", Toast.LENGTH_SHORT).show()
    }
    
    private fun checkServerConnection() {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val request = Request.Builder()
                    .url("$serverUrl/api/stats")
                    .build()
                
                httpClient.newCall(request).execute().use { response ->
                    withContext(Dispatchers.Main) {
                        if (response.isSuccessful) {
                            updateStatus("Сервер доступен")
                        } else {
                            updateStatus("Сервер недоступен: ${response.code}")
                        }
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    updateStatus("Ошибка подключения: ${e.message}")
                }
            }
        }
    }
    
    private fun sendFrame(bitmap: Bitmap) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                // Конвертация Bitmap в JPEG
                val outputStream = ByteArrayOutputStream()
                bitmap.compress(Bitmap.CompressFormat.JPEG, 80, outputStream)
                val imageBytes = outputStream.toByteArray()
                
                // Конвертация в Base64
                val base64String = Base64.encodeToString(imageBytes, Base64.NO_WRAP)
                
                // Создание JSON
                val frameData = mapOf(
                    "frame" to mapOf(
                        "type" to "video",
                        "data" to base64String,
                        "width" to bitmap.width,
                        "height" to bitmap.height,
                        "timestamp" to System.currentTimeMillis()
                    )
                )
                
                val json = gson.toJson(frameData)
                val body = json.toRequestBody("application/json".toMediaType())
                
                // Отправка на сервер
                val request = Request.Builder()
                    .url("$serverUrl/api/process-frame")
                    .post(body)
                    .build()
                
                httpClient.newCall(request).execute().use { response ->
                    if (response.isSuccessful) {
                        frameCount++
                        withContext(Dispatchers.Main) {
                            updateFrameCount()
                        }
                        Log.d(TAG, "Frame sent successfully: $frameCount")
                    } else {
                        Log.e(TAG, "Failed to send frame: ${response.code}")
                    }
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "Error sending frame", e)
            }
        }
    }
    
    private fun updateStatus(status: String) {
        runOnUiThread {
            tvStatus.text = "Статус: $status"
        }
    }
    
    private fun updateFrameCount() {
        tvFrameCount.text = "Кадров: $frameCount"
    }
    
    // Анализатор кадров
    private inner class FrameAnalyzer : ImageAnalysis.Analyzer {
        override fun analyze(image: ImageProxy) {
            val currentTime = System.currentTimeMillis()
            
            // Отправлять кадры только если стрим активен и прошел интервал
            if (isStreaming && (currentTime - lastFrameTime) >= frameInterval) {
                lastFrameTime = currentTime
                
                // Конвертация ImageProxy в Bitmap
                val bitmap = imageProxyToBitmap(image)
                
                if (bitmap != null) {
                    // Уменьшить разрешение для экономии трафика
                    val scaledBitmap = Bitmap.createScaledBitmap(
                        bitmap, 
                        640,  // ширина
                        480,  // высота
                        true
                    )
                    
                    sendFrame(scaledBitmap)
                    
                    // Освободить память
                    if (scaledBitmap != bitmap) {
                        bitmap.recycle()
                    }
                }
            }
            
            image.close()
        }
        
        private fun imageProxyToBitmap(image: ImageProxy): Bitmap? {
            val planes = image.planes
            val yBuffer = planes[0].buffer
            val uBuffer = planes[1].buffer
            val vBuffer = planes[2].buffer
            
            val ySize = yBuffer.remaining()
            val uSize = uBuffer.remaining()
            val vSize = vBuffer.remaining()
            
            val nv21 = ByteArray(ySize + uSize + vSize)
            
            yBuffer.get(nv21, 0, ySize)
            vBuffer.get(nv21, ySize, vSize)
            uBuffer.get(nv21, ySize + vSize, uSize)
            
            val yuvImage = YuvImage(nv21, ImageFormat.NV21, image.width, image.height, null)
            val out = ByteArrayOutputStream()
            yuvImage.compressToJpeg(Rect(0, 0, image.width, image.height), 80, out)
            val imageBytes = out.toByteArray()
            
            return BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.size)
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
                startCamera()
            } else {
                Toast.makeText(this, "Разрешения не предоставлены", Toast.LENGTH_SHORT).show()
                finish()
            }
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
    }
}

