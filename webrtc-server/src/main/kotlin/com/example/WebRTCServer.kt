package com.example

import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.routing.*
import io.ktor.server.websocket.*
import io.ktor.server.http.content.*
import io.ktor.http.*
import io.ktor.websocket.*
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import kotlinx.coroutines.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.encodeToString
import java.io.File
import java.util.concurrent.atomic.AtomicInteger

@Serializable
data class MediaFrame(
    val type: String, // "video" or "audio"
    val data: String, // Base64 encoded
    val timestamp: Long = System.currentTimeMillis(),
    val width: Int? = null,
    val height: Int? = null
)

@Serializable
data class StreamMessage(
    val action: String, // "offer", "answer", "ice-candidate", "media-frame"
    val data: String? = null,
    val frame: MediaFrame? = null
)

class WebRTCServer {
    val activeConnections = mutableMapOf<String, DefaultWebSocketServerSession>()
    private val connectionCounter = AtomicInteger(0)
    private val json = Json { ignoreUnknownKeys = true }
    private val httpClient = HttpClient(CIO)
    
    suspend fun handleWebSocket(session: DefaultWebSocketServerSession) {
        val connectionId = "conn_${connectionCounter.incrementAndGet()}"
        activeConnections[connectionId] = session
        
        println("✅ WebSocket подключен: $connectionId")
        
        try {
            // Отправка приветственного сообщения
            session.send(Frame.Text("""{"type":"connected","connectionId":"$connectionId"}"""))
            
            // Создание директории для сохранения медиа
            val mediaDir = File("/tmp/webrtc_media")
            mediaDir.mkdirs()
            
            for (frame in session.incoming) {
                when (frame) {
                    is Frame.Text -> {
                        val text = frame.readText()
                        println("📨 Получено: ${text.take(100)}...")
                        
                        try {
                            val message = json.decodeFromString<StreamMessage>(text)
                            
                            when (message.action) {
                                "media-frame" -> {
                                    message.frame?.let { frame ->
                                        handleMediaFrame(connectionId, frame)
                                    }
                                }
                                "offer" -> {
                                    println("📹 WebRTC Offer получен")
                                    // Здесь можно обработать SDP offer
                                }
                                "answer" -> {
                                    println("📹 WebRTC Answer получен")
                                }
                            }
                        } catch (e: Exception) {
                            println("❌ Ошибка обработки сообщения: ${e.message}")
                        }
                    }
                    is Frame.Binary -> {
                        // Обработка бинарных данных (видео/аудио)
                        val data = frame.readBytes()
                        handleBinaryData(connectionId, data)
                    }
                    else -> {}
                }
            }
        } catch (e: Exception) {
            println("❌ Ошибка WebSocket: ${e.message}")
        } finally {
            activeConnections.remove(connectionId)
            println("🔌 WebSocket отключен: $connectionId")
        }
    }
    
    private suspend fun handleMediaFrame(connectionId: String, frame: MediaFrame) {
        // Сохранение кадра в файл
        val frameFile = File("/tmp/webrtc_media/${connectionId}_${frame.timestamp}.${if (frame.type == "video") "jpg" else "raw"}")
        
        try {
            val data = java.util.Base64.getDecoder().decode(frame.data)
            frameFile.writeBytes(data)
            
            // Отправка в Python для обработки
            sendToPython(connectionId, frame)
            
            println("💾 Кадр сохранен: ${frameFile.name} (${data.size} bytes)")
        } catch (e: Exception) {
            println("❌ Ошибка сохранения кадра: ${e.message}")
        }
    }
    
    private suspend fun handleBinaryData(connectionId: String, data: ByteArray) {
        val timestamp = System.currentTimeMillis()
        val frameFile = File("/tmp/webrtc_media/${connectionId}_${timestamp}.bin")
        frameFile.writeBytes(data)
        
        // Отправка в Python
        sendToPython(connectionId, data)
        
        println("💾 Бинарные данные сохранены: ${frameFile.name} (${data.size} bytes)")
    }
    
    private suspend fun sendToPython(connectionId: String, frame: MediaFrame) {
        try {
            val pythonUrl = "http://127.0.0.1:5000/api/process-frame"
            val requestBody = """{"frame":${json.encodeToString(frame)}}"""
            
            val response: HttpResponse = httpClient.post(pythonUrl) {
                contentType(ContentType.Application.Json)
                setBody(requestBody)
            }
            
            if (response.status.value in 200..299) {
                println("✅ Кадр отправлен в Python: $connectionId")
            } else {
                println("⚠️ Python вернул код: ${response.status.value}")
            }
        } catch (e: Exception) {
            println("❌ Ошибка отправки в Python: ${e.message}")
        }
    }
    
    private suspend fun sendToPython(connectionId: String, data: ByteArray) {
        try {
            println("📤 Отправка бинарных данных в Python: $connectionId (${data.size} bytes)")
        } catch (e: Exception) {
            println("❌ Ошибка отправки в Python: ${e.message}")
        }
    }
}

fun main() {
    val server = WebRTCServer()
    
    embeddedServer(Netty, port = 8080, host = "0.0.0.0") {
        install(WebSockets) {
            pingPeriod = java.time.Duration.ofSeconds(15)
            timeout = java.time.Duration.ofSeconds(15)
            maxFrameSize = Long.MAX_VALUE
            masking = false
        }
        
        routing {
            // WebSocket endpoint
            webSocket("/ws") {
                server.handleWebSocket(this)
            }
            
            // Статические файлы (HTML интерфейс)
            staticResources("/", "static")
            
            // API endpoint
            get("/api/status") {
                call.respondText("""{"status":"ok","connections":${server.activeConnections.size}}""", ContentType.Application.Json)
            }
        }
    }.start(wait = true)
}

