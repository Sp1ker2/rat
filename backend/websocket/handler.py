"""WebSocket connection handler"""
import json
import asyncio
from datetime import datetime
from typing import Dict, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from backend.models import DeviceInfo, CameraFrame, LocationUpdate, DeviceCommand
from backend.devices.manager import session_manager
from backend.storage.database import storage
from backend.devices.registration import get_device_by_token
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
        
        # Detailed logging
        print(f"[DEVICE_CONNECT] Device connected: {device_info.name} (ID: {device_info.id})")
        print(f"[DEVICE_CONNECT] Model: {device_info.manufacturer} {device_info.model}")
        print(f"[DEVICE_CONNECT] Android: {device_info.android_version} (SDK: {device_info.sdk})")
        print(f"[DEVICE_CONNECT] IMEI: {device_info.imei or 'N/A'}")
        print(f"[DEVICE_CONNECT] Total connected devices: {len(self.device_connections)}")
        
        return conn
    
    async def disconnect_device(self, device_id: str):
        """Disconnect a device"""
        if device_id in self.device_connections:
            device_name = self.device_connections[device_id].device_name
            del self.device_connections[device_id]
            session_manager.disconnect_device(device_id)
            
            # Notify admins
            await self.broadcast_to_admins({
                "type": "device_disconnected",
                "device_id": device_id
            })
            
            await storage.log_device_event(device_id, "disconnected")
            print(f"[DEVICE_DISCONNECT] Device disconnected: {device_name} (ID: {device_id})")
            print(f"[DEVICE_DISCONNECT] Total connected devices: {len(self.device_connections)}")
    
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
        else:
            # Log unknown message types
            device_name = "Unknown"
            if device_id in self.device_connections:
                device_name = self.device_connections[device_id].device_name
            print(f"[UNKNOWN_MESSAGE] Received unknown message type '{msg_type}' from {device_name} (ID: {device_id})")
            print(f"[UNKNOWN_MESSAGE] Message keys: {list(message.keys())}")
    
    async def _handle_camera_frame(self, device_id: str, message: Dict):
        """Handle camera frame from device"""
        try:
            frame = CameraFrame(**message)
            
            # Decode and save frame
            try:
                frame_bytes = base64.b64decode(frame.data)
                frame_size = len(frame_bytes)
            except Exception as decode_error:
                print(f"[CAMERA_FRAME_ERROR] Failed to decode Base64 for device {device_id}: {decode_error}")
                print(f"[CAMERA_FRAME_ERROR] Base64 data length: {len(frame.data)}")
                raise
            
            # Save to database
            saved_frame = await storage.save_camera_frame(
                device_id, 
                frame.camera, 
                frame_bytes,
                frame.width,
                frame.height,
                frame.timestamp
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
            
            # Log successful save
            device_name = "Unknown"
            if device_id in self.device_connections:
                device_name = self.device_connections[device_id].device_name
            print(f"[CAMERA_FRAME] Saved frame from {device_name} (ID: {device_id})")
            print(f"[CAMERA_FRAME] Camera: {frame.camera}, Size: {frame_size} bytes, Resolution: {frame.width}x{frame.height}")
            print(f"[CAMERA_FRAME] Timestamp: {frame.timestamp}, Frame ID: {saved_frame.id}")
            
        except Exception as e:
            import traceback
            print(f"[CAMERA_FRAME_ERROR] Error handling camera frame from device {device_id}: {e}")
            print(f"[CAMERA_FRAME_ERROR] Traceback: {traceback.format_exc()}")
            print(f"[CAMERA_FRAME_ERROR] Message keys: {list(message.keys())}")
    
    async def _handle_location_update(self, device_id: str, message: Dict):
        """Handle location update from device"""
        try:
            location = LocationUpdate(**message)
            
            # Save location
            saved_location = await storage.save_location(
                device_id,
                location.lat,
                location.lon,
                location.accuracy,
                location.timestamp
            )
            
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
            
            # Log successful save
            device_name = "Unknown"
            if device_id in self.device_connections:
                device_name = self.device_connections[device_id].device_name
            accuracy_str = f"{location.accuracy:.1f}m" if location.accuracy else "N/A"
            print(f"[LOCATION_UPDATE] Saved location from {device_name} (ID: {device_id})")
            print(f"[LOCATION_UPDATE] Coordinates: {location.lat:.6f}, {location.lon:.6f}, Accuracy: {accuracy_str}")
            print(f"[LOCATION_UPDATE] Timestamp: {location.timestamp}, Location ID: {saved_location.id}")
            
        except Exception as e:
            import traceback
            print(f"[LOCATION_UPDATE_ERROR] Error handling location update from device {device_id}: {e}")
            print(f"[LOCATION_UPDATE_ERROR] Traceback: {traceback.format_exc()}")
            print(f"[LOCATION_UPDATE_ERROR] Message: {message}")
    
    async def _handle_system_info(self, device_id: str, message: Dict):
        """Handle system info from device"""
        try:
            system_info = message.get("data", {})
            
            # Update session
            await session_manager.update_device_data(device_id, {
                "battery_level": system_info.get("battery_level")
            })
            
            # Save to log
            saved_event = await storage.log_device_event(device_id, "system_info", system_info)
            
            # Broadcast to admins
            await self.broadcast_to_admins({
                "type": "device_update",
                "device_id": device_id,
                "data": system_info
            })
            
            # Log successful save
            device_name = "Unknown"
            if device_id in self.device_connections:
                device_name = self.device_connections[device_id].device_name
            battery = system_info.get("battery_level", "N/A")
            is_charging = system_info.get("is_charging", False)
            memory = system_info.get("memory_usage", "N/A")
            storage_usage = system_info.get("storage_usage", "N/A")
            print(f"[SYSTEM_INFO] Saved system info from {device_name} (ID: {device_id})")
            print(f"[SYSTEM_INFO] Battery: {battery}% {'(charging)' if is_charging else '(not charging)'}")
            print(f"[SYSTEM_INFO] Memory usage: {memory}, Storage usage: {storage_usage}")
            print(f"[SYSTEM_INFO] Timestamp: {system_info.get('timestamp', 'N/A')}, Event ID: {saved_event.id}")
            
        except Exception as e:
            import traceback
            print(f"[SYSTEM_INFO_ERROR] Error handling system info from device {device_id}: {e}")
            print(f"[SYSTEM_INFO_ERROR] Traceback: {traceback.format_exc()}")
            print(f"[SYSTEM_INFO_ERROR] Message: {message}")
    
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

