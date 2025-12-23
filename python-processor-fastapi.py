import asyncio
import base64
import time
import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json

app = FastAPI(title="WebRTC Stream Server")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные переменные
current_frame = None
frame_count = 0
start_time = time.time()
connected_clients: List[WebSocket] = []

# Pydantic модели
class MediaFrame(BaseModel):
    type: str = "video"
    data: str
    width: int = 1280
    height: int = 720
    timestamp: Optional[float] = None

class ProcessFrameRequest(BaseModel):
    frame: MediaFrame

class WebRTCStreamRequest(BaseModel):
    frame: MediaFrame

def process_video_frame(frame_base64: str, width: int, height: int) -> tuple[bool, str]:
    """Обработка видео кадра"""
    global current_frame, frame_count
    
    try:
        # Валидация Base64
        if not frame_base64 or frame_base64 == "string":
            return False, "Invalid Base64 data: empty or placeholder value"
        
        # Декодирование Base64
        try:
            frame_data = base64.b64decode(frame_base64, validate=True)
        except Exception as e:
            return False, f"Base64 decode error: {str(e)}"
        
        if len(frame_data) == 0:
            return False, "Empty frame data after Base64 decode"
        
        # Декодирование изображения
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return False, "Failed to decode image from frame data"
        
        # Обновляем текущий кадр
        current_frame = frame
        frame_count += 1
        
        return True, "Frame processed successfully"
    except Exception as e:
        error_msg = f"Error processing frame: {str(e)}"
        print(error_msg)
        return False, error_msg

@app.get("/", response_class=HTMLResponse)
async def index():
    """Главная страница"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebRTC Stream Server</title>
        <meta charset="utf-8">
        <style>
            body {
                margin: 0;
                padding: 20px;
                background: #1a1a1a;
                color: white;
                font-family: Arial, sans-serif;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            h1 {
                text-align: center;
                color: #00ff88;
            }
            .video-container {
                background: #000;
                border-radius: 10px;
                overflow: hidden;
                margin: 20px 0;
                box-shadow: 0 0 20px rgba(0,255,136,0.3);
                min-height: 400px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            #videoStream {
                width: 100%;
                display: none;
            }
            .placeholder {
                text-align: center;
                padding: 40px;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .stat-card {
                background: #2a2a2a;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }
            .stat-value {
                font-size: 2em;
                color: #00ff88;
                font-weight: bold;
            }
            .info {
                background: #2a2a2a;
                padding: 20px;
                border-radius: 10px;
                margin-top: 20px;
            }
            .endpoint {
                background: #1a1a1a;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>WebRTC Stream Server (FastAPI)</h1>
            <div class="video-container">
                <img id="videoStream" alt="Video Stream">
                <div class="placeholder" id="placeholder">
                    <h2>Ожидание потока...</h2>
                    <p>Отправьте видео кадры на сервер для начала трансляции</p>
                </div>
            </div>
            <div class="stats">
                <div class="stat-card">
                    <h3>Кадров обработано</h3>
                    <div class="stat-value" id="frames">0</div>
                </div>
                <div class="stat-card">
                    <h3>FPS</h3>
                    <div class="stat-value" id="fps">0</div>
                </div>
                <div class="stat-card">
                    <h3>Время работы</h3>
                    <div class="stat-value" id="uptime">0s</div>
                </div>
                <div class="stat-card">
                    <h3>Статус</h3>
                    <div class="stat-value" id="status">Готов</div>
                </div>
            </div>
            
            <div class="info">
                <h2>API Endpoints</h2>
                <div class="endpoint">POST /api/process-frame - Прием кадров от Kotlin</div>
                <div class="endpoint">POST /api/webrtc/stream - Прием WebRTC потока</div>
                <div class="endpoint">GET /api/stream - MJPEG поток</div>
                <div class="endpoint">GET /api/stats - Статистика</div>
                <div class="endpoint">WS /ws - WebSocket для реального времени</div>
            </div>
        </div>
        
        <script>
            let hasFrames = false;
            const videoStream = document.getElementById('videoStream');
            const placeholder = document.getElementById('placeholder');
            
            async function updateStats() {
                try {
                    const response = await fetch('/api/stats');
                    const data = await response.json();
                    
                    document.getElementById('frames').textContent = data.frames_processed;
                    document.getElementById('fps').textContent = data.fps;
                    document.getElementById('uptime').textContent = Math.round(data.uptime) + 's';
                    document.getElementById('status').textContent = data.status;
                    
                    // Показать поток если есть кадры
                    if (data.frames_processed > 0 && !hasFrames) {
                        hasFrames = true;
                        videoStream.src = '/api/stream?' + new Date().getTime();
                        videoStream.style.display = 'block';
                        placeholder.style.display = 'none';
                    }
                } catch (err) {
                    console.error('Ошибка загрузки статистики:', err);
                }
            }
            
            setInterval(updateStats, 1000);
            updateStats();
        </script>
    </body>
    </html>
    """

@app.post("/api/process-frame")
async def process_frame(request: ProcessFrameRequest):
    """
    Обработка кадра от Kotlin клиента
    
    Требуется Base64-закодированное изображение в формате JPEG или PNG.
    
    Пример корректного Base64 (1x1 красный пиксель JPEG):
    /9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCfABmX/9k=
    """
    try:
        frame = request.frame
        
        success, message = process_video_frame(frame.data, frame.width, frame.height)
        
        if success:
            # Уведомить WebSocket клиентов
            await broadcast_frame_notification()
            
            return {
                "status": "success",
                "frame_count": frame_count,
                "message": message
            }
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"API error: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/webrtc/stream")
async def webrtc_stream(request: WebRTCStreamRequest):
    """
    API endpoint для приема WebRTC потока через HTTP
    
    Принимает видео кадры в формате Base64.
    """
    try:
        frame = request.frame
        
        if frame.type == 'video':
            success, message = process_video_frame(frame.data, frame.width, frame.height)
            
            if success:
                await broadcast_frame_notification()
                
                return {
                    "status": "success",
                    "frame_count": frame_count,
                    "message": message
                }
            else:
                raise HTTPException(status_code=400, detail=message)
        
        raise HTTPException(status_code=400, detail="Invalid frame type")
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"WebRTC API error: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/stream")
async def video_stream():
    """MJPEG видео поток"""
    async def generate():
        global current_frame
        
        while True:
            if current_frame is not None:
                # Кодирование кадра в JPEG
                ret, buffer = cv2.imencode('.jpg', current_frame, 
                                         [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + 
                           frame_bytes + b'\r\n')
            
            await asyncio.sleep(0.1)  # 10 FPS
    
    return StreamingResponse(
        generate(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )

@app.get("/api/stats")
async def get_stats():
    """Статистика обработки"""
    global frame_count, start_time
    
    elapsed = time.time() - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    
    return {
        'frames_processed': frame_count,
        'fps': round(fps, 2),
        'uptime': round(elapsed, 2),
        'status': 'running',
        'connected_clients': len(connected_clients)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint для реального времени"""
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to WebRTC server"
        })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "media_frame":
                frame_data = message.get("data", {})
                
                success, msg = process_video_frame(
                    frame_data.get("data", ""),
                    frame_data.get("width", 1280),
                    frame_data.get("height", 720)
                )
                
                if success:
                    await websocket.send_json({
                        "type": "frame_received",
                        "status": "success",
                        "frame_count": frame_count,
                        "message": msg
                    })
                    
                    # Транслировать другим клиентам
                    await broadcast_frame_notification(exclude=websocket)
                else:
                    await websocket.send_json({
                        "type": "frame_received",
                        "status": "error",
                        "message": msg
                    })
                    
    except WebSocketDisconnect:
        print(f"WebSocket отключен")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def broadcast_frame_notification(exclude: Optional[WebSocket] = None):
    """Отправка уведомления о новом кадре всем подключенным клиентам"""
    message = {
        "type": "new_frame",
        "frame_count": frame_count,
        "timestamp": time.time()
    }
    
    disconnected = []
    for client in connected_clients:
        if client != exclude:
            try:
                await client.send_json(message)
            except:
                disconnected.append(client)
    
    # Удалить отключенных клиентов
    for client in disconnected:
        if client in connected_clients:
            connected_clients.remove(client)

@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("WebRTC Stream Server (FastAPI) запущен!")
    print("=" * 60)
    print(f"Видео поток: http://0.0.0.0:5000/api/stream")
    print(f"Статистика: http://0.0.0.0:5000/api/stats")
    print(f"WebSocket: ws://0.0.0.0:5000/ws")
    print(f"Внешний доступ: http://185.115.33.46:5000")
    print(f"HTTPS: https://kelyastream.duckdns.org")
    print("")
    print("API Endpoints:")
    print("  POST /api/process-frame - Прием кадров от Kotlin")
    print("  POST /api/webrtc/stream - Прием WebRTC потока")
    print("  GET  /api/stream - MJPEG поток")
    print("  GET  /api/stats - Статистика")
    print("  WS   /ws - WebSocket для реального времени")
    print("=" * 60)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info",
        access_log=True
    )

