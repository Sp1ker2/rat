#!/usr/bin/env python3
"""
Python сервер для обработки WebRTC потока
Принимает медиа данные от Kotlin сервера и выводит их
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import json
import os
import threading
import time
from datetime import datetime
import subprocess

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Глобальные переменные
current_frame = None
frame_lock = threading.Lock()
frame_count = 0
start_time = time.time()

# Создание директории для сохранения
os.makedirs('/tmp/webrtc_processed', exist_ok=True)
os.makedirs('/tmp/webrtc_output', exist_ok=True)

def process_video_frame(frame_data, width, height):
    """Обработка видео кадра"""
    global current_frame, frame_count
    
    try:
        # Декодирование base64
        img_data = base64.b64decode(frame_data)
        nparr = np.frombuffer(img_data, np.uint8)
        
        # Декодирование JPEG
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is not None:
            # Изменение размера если нужно
            if width and height:
                img = cv2.resize(img, (width, height))
            
            # Применение эффектов (опционально)
            # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Сохранение кадра
            with frame_lock:
                current_frame = img.copy()
                frame_count += 1
            
            # Сохранение в файл (каждый 10-й кадр)
            if frame_count % 10 == 0:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"/tmp/webrtc_processed/frame_{timestamp}.jpg"
                cv2.imwrite(filename, img)
                print(f"Кадр сохранен: {filename}")
            
            return True
    except Exception as e:
        print(f"Ошибка обработки кадра: {e}")
        return False

@app.route('/api/process-frame', methods=['POST'])
def process_frame():
    """API endpoint для приема кадров от Kotlin"""
    global frame_count
    
    try:
        data = request.json
        
        if 'frame' in data:
            frame_data = data['frame']
            frame_type = frame_data.get('type', 'video')
            
            if frame_type == 'video':
                width = frame_data.get('width', 1280)
                height = frame_data.get('height', 720)
                frame_base64 = frame_data.get('data', '')
                
                if process_video_frame(frame_base64, width, height):
                    return jsonify({
                        'status': 'success',
                        'message': 'Frame processed',
                        'frame_count': frame_count
                    }), 200
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Failed to process frame'
                    }), 400
        
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
        
    except Exception as e:
        print(f"Ошибка API: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stream')
def video_stream():
    """Видео поток для вывода в браузере"""
    def generate():
        global current_frame
        
        while True:
            with frame_lock:
                if current_frame is not None:
                    # Кодирование кадра в JPEG
                    ret, buffer = cv2.imencode('.jpg', current_frame, 
                                             [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + 
                               frame_bytes + b'\r\n')
            
            time.sleep(0.1)  # 10 FPS
    
    return Response(generate(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/stats')
def get_stats():
    """Статистика обработки"""
    global frame_count, start_time
    
    elapsed = time.time() - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    
    return jsonify({
        'frames_processed': frame_count,
        'fps': round(fps, 2),
        'uptime': round(elapsed, 2),
        'status': 'running'
    })

@app.route('/api/save-video', methods=['POST'])
def save_video():
    """Сохранение видео из кадров"""
    try:
        # Здесь можно использовать FFmpeg для создания видео
        # из сохраненных кадров
        return jsonify({'status': 'success', 'message': 'Video saved'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# WebSocket события для WebRTC
@socketio.on('connect')
def handle_connect():
    """Обработка подключения WebSocket"""
    print(f"WebSocket подключен: {request.sid}")
    emit('connected', {'status': 'ok', 'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Обработка отключения WebSocket"""
    print(f"WebSocket отключен: {request.sid}")

@socketio.on('media_frame')
def handle_media_frame(data):
    """Обработка медиа кадра через WebSocket"""
    global frame_count
    
    try:
        if isinstance(data, str):
            data = json.loads(data)
        
        frame_type = data.get('type', 'video')
        
        if frame_type == 'video':
            frame_base64 = data.get('data', '')
            width = data.get('width', 1280)
            height = data.get('height', 720)
            
            if process_video_frame(frame_base64, width, height):
                # Отправить подтверждение обратно
                emit('frame_received', {
                    'status': 'success',
                    'frame_count': frame_count
                })
                
                # Транслировать кадр всем подключенным клиентам
                socketio.emit('new_frame', {
                    'frame_count': frame_count,
                    'timestamp': time.time()
                }, broadcast=True)
            else:
                emit('frame_received', {'status': 'error'})
    except Exception as e:
        print(f"Ошибка обработки WebSocket кадра: {e}")
        emit('frame_received', {'status': 'error', 'message': str(e)})

@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    """Обработка WebRTC offer (SDP)"""
    print(f"WebRTC Offer получен: {request.sid}")
    # Здесь можно обработать SDP offer для WebRTC
    emit('webrtc_answer', {'status': 'received'})

@socketio.on('webrtc_ice_candidate')
def handle_ice_candidate(data):
    """Обработка ICE candidate"""
    print(f"ICE candidate получен: {request.sid}")
    # Здесь можно обработать ICE candidate
    emit('ice_candidate_received', {'status': 'ok'})

@app.route('/api/webrtc/stream', methods=['POST'])
def webrtc_stream():
    """API endpoint для приема WebRTC потока через HTTP"""
    global frame_count
    
    try:
        data = request.json
        
        # Поддержка разных форматов данных
        if 'frame' in data:
            frame_data = data['frame']
            frame_type = frame_data.get('type', 'video')
            
            if frame_type == 'video':
                width = frame_data.get('width', 1280)
                height = frame_data.get('height', 720)
                frame_base64 = frame_data.get('data', '')
                
                if process_video_frame(frame_base64, width, height):
                    return jsonify({
                        'status': 'success',
                        'frame_count': frame_count
                    }), 200
        
        # Прямая отправка кадра
        elif 'data' in data and 'type' in data:
            if data['type'] == 'video':
                width = data.get('width', 1280)
                height = data.get('height', 720)
                frame_base64 = data.get('data', '')
                
                if process_video_frame(frame_base64, width, height):
                    return jsonify({
                        'status': 'success',
                        'frame_count': frame_count
                    }), 200
        
        return jsonify({'status': 'error', 'message': 'Invalid data format'}), 400
        
    except Exception as e:
        print(f"Ошибка WebRTC API: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/')
def index():
    """Главная страница с выводом видео"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebRTC Stream Viewer</title>
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
            <h1>WebRTC Stream Server</h1>
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
                
                <h3>WebSocket Events</h3>
                <div class="endpoint">connect - Подключение</div>
                <div class="endpoint">media_frame - Отправка кадра</div>
                <div class="endpoint">webrtc_offer - WebRTC offer</div>
                <div class="endpoint">webrtc_ice_candidate - ICE candidate</div>
            </div>
        </div>
        
        <script>
            let hasFrames = false;
            const videoStream = document.getElementById('videoStream');
            const placeholder = document.getElementById('placeholder');
            
            function updateStats() {
                fetch('/api/stats')
                    .then(r => r.json())
                    .then(data => {
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
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки статистики:', err);
                    });
            }
            
            setInterval(updateStats, 1000);
            updateStats();
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    PORT = 5000
    
    print(f"Python WebRTC сервер запускается...")
    print(f"Видео поток: http://0.0.0.0:{PORT}/api/stream")
    print(f"Статистика: http://0.0.0.0:{PORT}/api/stats")
    print(f"WebSocket: ws://0.0.0.0:{PORT}")
    print(f"Внешний доступ: http://185.115.33.46:{PORT}")
    print(f"HTTPS: https://kelyastream.duckdns.org")
    print(f"")
    print(f"API Endpoints:")
    print(f"  POST /api/process-frame - Прием кадров от Kotlin")
    print(f"  POST /api/webrtc/stream - Прием WebRTC потока")
    print(f"  GET  /api/stream - MJPEG поток")
    print(f"  GET  /api/stats - Статистика")
    print(f"")
    print(f"WebSocket Events:")
    print(f"  connect - Подключение")
    print(f"  media_frame - Отправка кадра")
    print(f"  webrtc_offer - WebRTC offer")
    print(f"  webrtc_ice_candidate - ICE candidate")
    
    try:
        socketio.run(app, host='0.0.0.0', port=PORT, debug=False, allow_unsafe_werkzeug=True)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Порт {PORT} уже занят!")
            print("Остановите другие процессы на порту 5000 или измените порт")
            print("Проверьте: lsof -i:5000")
        else:
            print(f"Ошибка запуска: {e}")
        raise


