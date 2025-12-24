"""Device session management"""
from datetime import datetime
from typing import Dict, List, Optional
from backend.models import DeviceSession, DeviceInfo
from backend.storage.database import storage
from backend.database.models import Device


class SessionManager:
    """Manages active device sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, DeviceSession] = {}
    
    async def register_device(self, device_info: DeviceInfo) -> DeviceSession:
        """Register a new device or update existing"""
        
        # Check if device exists in database
        db_device = await storage.get_device(device_info.id)
        
        if db_device:
            # Update existing device
            await storage.update_device(
                device_info.id,
                name=device_info.name,
                imei=device_info.imei,
                model=device_info.model,
                manufacturer=device_info.manufacturer,
                android_version=device_info.android_version,
                sdk=device_info.sdk
            )
        else:
            # Device should be pre-registered with token
            # If not found, create it (for backward compatibility)
            from backend.devices.registration import generate_device_token
            await storage.create_device(
                device_id=device_info.id,
                name=device_info.name,
                token=generate_device_token(),
                imei=device_info.imei,
                model=device_info.model,
                manufacturer=device_info.manufacturer,
                android_version=device_info.android_version,
                sdk=device_info.sdk
            )
        
        # Create or update in-memory session
        now = datetime.utcnow()
        
        if device_info.id in self.sessions:
            session = self.sessions[device_info.id]
            session.last_activity = now
            session.is_online = True
            session.device_name = device_info.name
        else:
            session = DeviceSession(
                device_id=device_info.id,
                device_name=device_info.name,
                imei=device_info.imei,
                model=device_info.model,
                manufacturer=device_info.manufacturer,
                android_version=device_info.android_version,
                connected_at=now,
                last_activity=now
            )
            self.sessions[device_info.id] = session
        
        # Log event
        await storage.log_device_event(device_info.id, "connected", device_info.dict())
        
        return session
    
    def disconnect_device(self, device_id: str):
        """Mark device as disconnected"""
        if device_id in self.sessions:
            self.sessions[device_id].is_online = False
    
    def get_device(self, device_id: str) -> Optional[DeviceSession]:
        """Get device session"""
        return self.sessions.get(device_id)
    
    def get_all_devices(self) -> List[DeviceSession]:
        """Get all device sessions"""
        return list(self.sessions.values())
    
    def get_online_devices(self) -> List[DeviceSession]:
        """Get only online devices"""
        return [s for s in self.sessions.values() if s.is_online]
    
    async def update_device_data(self, device_id: str, data: Dict):
        """Update device session data"""
        if device_id in self.sessions:
            session = self.sessions[device_id]
            session.last_activity = datetime.utcnow()
            
            # Update specific fields
            if "battery_level" in data:
                session.battery_level = data["battery_level"]
            if "location" in data:
                session.location = data["location"]
            if "current_camera" in data:
                session.current_camera = data["current_camera"]
    
    async def save_snapshot(self, device_id: str, data_type: str, data: Dict):
        """Save data snapshot"""
        if data_type == "location":
            await storage.save_location(
                device_id,
                data.get("lat"),
                data.get("lon"),
                data.get("accuracy"),
                data.get("timestamp", int(datetime.utcnow().timestamp() * 1000))
            )
        
        await storage.log_device_event(device_id, f"{data_type}_update", data)


# Global session manager
session_manager = SessionManager()

