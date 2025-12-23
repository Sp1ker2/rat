"""WebSocket connection handler"""
import json
import asyncio
from datetime import datetime
from typing import Dict, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from backend.models import DeviceInfo, CameraFrame, LocationUpdate, DeviceCommand
from backend.devices.manager import session_manager
from backend.storage.files import storage
import base64


class DeviceConnection:
    """Represents a connected device"""
    def __init__(self, device_id: str, device_name: str, websocket: WebSocket):
        self.device_id = device_id
        self.device_name = device_name
        self.websocket = websocket
        self.last_seen = datetime.utcnow()
        self.data = {}


class WebSocketManager:
    """Manages WebSocket connections for devices and admins"""
    
    def __init__(self):
        self.device_connections: Dict[str, DeviceConnection] = {}
        self.admin_connections: Set[WebSocket] = set()
    
    async def connect_device(self, device_info: DeviceInfo, websocket: WebSocket):
        """Connect a device"""
        await websocket.accept()
        
        # Register device session
        session = await session_manager.register_device(device_info)
        
        # Store connection
        conn = DeviceConnection(device_info.id, device_info.name, websocket)
        self.device_connections[device_info.id] = conn
        
        # Notify admins
        await self.broadcast_to_admins({
            "type": "device_connected",
            "device": session.dict()
        })
        
        print(f"Device connected: {device_info.name} ({device_info.id})")
        
        return conn
    
    async def disconnect_device(self, device_id: str):
        """Disconnect a device"""
        if device_id in self.device_connections:
            del self.device_connections[device_id]
            session_manager.disconnect_device(device_id)
            
            # Notify admins
            await self.broadcast_to_admins({
                "type": "device_disconnected",
                "device_id": device_id
            })
            
            await storage.log_device_event(device_id, "disconnected")
            print(f"Device disconnected: {device_id}")
    
    async def connect_admin(self, websocket: WebSocket):
        """Connect an admin"""
        await websocket.accept()
        self.admin_connections.add(websocket)
        
        # Send current device list
        devices = session_manager.get_all_devices()
        await websocket.send_json({
            "type": "device_list",
            "devices": [d.dict() for d in devices]
        })
        
        print(f"Admin connected. Total admins: {len(self.admin_connections)}")
    
    async def disconnect_admin(self, websocket: WebSocket):
        """Disconnect an admin"""
        self.admin_connections.discard(websocket)
        print(f"Admin disconnected. Total admins: {len(self.admin_connections)}")
    
    async def handle_device_message(self, device_id: str, message: Dict):
        """Handle message from device"""
        msg_type = message.get("type")
        
        if msg_type == "camera_frame":
            await self._handle_camera_frame(device_id, message)
        elif msg_type == "location_update":
            await self._handle_location_update(device_id, message)
        elif msg_type == "system_info":
            await self._handle_system_info(device_id, message)
        elif msg_type == "ping":
            # Update last seen
            if device_id in self.device_connections:
                self.device_connections[device_id].last_seen = datetime.utcnow()
    
    async def _handle_camera_frame(self, device_id: str, message: Dict):
        """Handle camera frame from device"""
        try:
            frame = CameraFrame(**message)
            
            # Decode and save frame
            frame_bytes = base64.b64decode(frame.data)
            await storage.save_camera_frame(
                device_id, frame.camera, frame_bytes, frame.timestamp
            )
            
            # Update session
            await session_manager.update_device_data(device_id, {
                "current_camera": frame.camera
            })
            
            # Broadcast to admins (send only metadata, not full frame for performance)
            await self.broadcast_to_admins({
                "type": "camera_frame",
                "device_id": device_id,
                "camera": frame.camera,
                "timestamp": frame.timestamp,
                "width": frame.width,
                "height": frame.height
            })
            
        except Exception as e:
            print(f"Error handling camera frame: {e}")
    
    async def _handle_location_update(self, device_id: str, message: Dict):
        """Handle location update from device"""
        try:
            location = LocationUpdate(**message)
            
            # Save location
            await storage.save_location(device_id, location.dict())
            
            # Update session
            await session_manager.update_device_data(device_id, {
                "location": location.dict()
            })
            
            # Broadcast to admins
            await self.broadcast_to_admins({
                "type": "location_update",
                "device_id": device_id,
                "location": location.dict()
            })
            
        except Exception as e:
            print(f"Error handling location update: {e}")
    
    async def _handle_system_info(self, device_id: str, message: Dict):
        """Handle system info from device"""
        try:
            system_info = message.get("data", {})
            
            # Update session
            await session_manager.update_device_data(device_id, {
                "battery_level": system_info.get("battery_level")
            })
            
            # Save to log
            await storage.log_device_event(device_id, "system_info", system_info)
            
            # Broadcast to admins
            await self.broadcast_to_admins({
                "type": "device_update",
                "device_id": device_id,
                "data": system_info
            })
            
        except Exception as e:
            print(f"Error handling system info: {e}")
    
    async def send_command(self, device_id: str, command: DeviceCommand) -> bool:
        """Send command to device"""
        if device_id not in self.device_connections:
            return False
        
        try:
            conn = self.device_connections[device_id]
            await conn.websocket.send_json({
                "type": "command",
                "command": command.command,
                "data": command.data
            })
            
            await storage.log_device_event(device_id, "command_sent", command.dict())
            return True
        except Exception as e:
            print(f"Error sending command to device {device_id}: {e}")
            return False
    
    async def broadcast_to_admins(self, message: Dict, exclude: Optional[WebSocket] = None):
        """Broadcast message to all connected admins"""
        disconnected = []
        
        for admin_ws in self.admin_connections:
            if admin_ws != exclude:
                try:
                    await admin_ws.send_json(message)
                except Exception:
                    disconnected.append(admin_ws)
        
        # Remove disconnected admins
        for ws in disconnected:
            self.admin_connections.discard(ws)
    
    def get_device_connection(self, device_id: str) -> Optional[DeviceConnection]:
        """Get device connection"""
        return self.device_connections.get(device_id)
    
    def get_active_devices(self) -> Dict[str, DeviceConnection]:
        """Get all active device connections"""
        return self.device_connections.copy()


# Global WebSocket manager
ws_manager = WebSocketManager()

