package com.monitoring.collectors

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageFormat
import android.graphics.Rect
import android.graphics.YuvImage
import android.util.Base64
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat
import androidx.lifecycle.LifecycleOwner
import java.io.ByteArrayOutputStream
import java.util.concurrent.Executors

data class CameraFrame(
    val camera: String,
    val data: String,
    val width: Int,
    val height: Int,
    val timestamp: Long
)

class CameraCollector(private val context: Context) {
    private var currentCamera: CameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
    private var imageAnalyzer: ImageAnalysis? = null
    private var cameraProvider: ProcessCameraProvider? = null
    private val executor = Executors.newSingleThreadExecutor()
    private var callback: ((CameraFrame) -> Unit)? = null
    private var isStarted = false
    
    fun start(lifecycleOwner: LifecycleOwner, onFrame: (CameraFrame) -> Unit) {
        callback = onFrame
        isStarted = true
        startCamera(lifecycleOwner)
    }
    
    fun stop() {
        isStarted = false
        cameraProvider?.unbindAll()
        callback = null
    }
    
    fun switchCamera(type: String, lifecycleOwner: LifecycleOwner) {
        currentCamera = when (type.lowercase()) {
            "front" -> CameraSelector.DEFAULT_FRONT_CAMERA
            "back" -> CameraSelector.DEFAULT_BACK_CAMERA
            else -> currentCamera
        }
        
        if (isStarted) {
            restartCamera(lifecycleOwner)
        }
    }
    
    private fun startCamera(lifecycleOwner: LifecycleOwner) {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(context)
        
        cameraProviderFuture.addListener({
            try {
                cameraProvider = cameraProviderFuture.get()
                bindCamera(lifecycleOwner)
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }, ContextCompat.getMainExecutor(context))
    }
    
    private fun bindCamera(lifecycleOwner: LifecycleOwner) {
        val provider = cameraProvider ?: return
        
        // Unbind previous
        provider.unbindAll()
        
        // Build image analyzer
        imageAnalyzer = ImageAnalysis.Builder()
            .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
            .build()
            .also {
                it.setAnalyzer(executor) { image ->
                    processFrame(image)
                }
            }
        
        try {
            // Bind to lifecycle
            provider.bindToLifecycle(
                lifecycleOwner,
                currentCamera,
                imageAnalyzer
            )
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    private fun restartCamera(lifecycleOwner: LifecycleOwner) {
        cameraProvider?.unbindAll()
        bindCamera(lifecycleOwner)
    }
    
    private fun processFrame(image: ImageProxy) {
        try {
            val bitmap = imageProxyToBitmap(image)
            if (bitmap != null) {
                // Resize for bandwidth optimization
                val scaledBitmap = Bitmap.createScaledBitmap(bitmap, 640, 480, true)
                
                // Compress to JPEG
                val outputStream = ByteArrayOutputStream()
                scaledBitmap.compress(Bitmap.CompressFormat.JPEG, 80, outputStream)
                val imageBytes = outputStream.toByteArray()
                
                // Encode to Base64
                val base64String = Base64.encodeToString(imageBytes, Base64.NO_WRAP)
                
                // Create frame object
                val frame = CameraFrame(
                    camera = if (currentCamera == CameraSelector.DEFAULT_FRONT_CAMERA) "front" else "back",
                    data = base64String,
                    width = scaledBitmap.width,
                    height = scaledBitmap.height,
                    timestamp = System.currentTimeMillis()
                )
                
                // Send to callback
                callback?.invoke(frame)
                
                // Clean up
                if (scaledBitmap != bitmap) {
                    bitmap.recycle()
                }
                scaledBitmap.recycle()
            }
        } catch (e: Exception) {
            e.printStackTrace()
        } finally {
            image.close()
        }
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

