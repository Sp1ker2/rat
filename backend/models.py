"""Data models for the monitoring system"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class DeviceInfo(BaseModel):
    """Device information"""
    id: str
    name: str
    imei: Optional[str] = None
    model: str
    manufacturer: str
    android_version: str
    sdk: int


class DeviceSession(BaseModel):
    """Device session data"""
    device_id: str
    device_name: str
    imei: Optional[str] = None
    model: str
    manufacturer: str
    android_version: str
    connected_at: datetime
    last_activity: datetime
    current_camera: str = "back"
    location: Optional[Dict[str, Any]] = None
    battery_level: Optional[int] = None
    is_online: bool = True


class CameraFrame(BaseModel):
    """Camera frame data"""
    camera: str  # "front" or "back"
    data: str  # Base64 encoded image
    width: int
    height: int
    timestamp: int


class LocationUpdate(BaseModel):
    """Location update data"""
    lat: float
    lon: float
    accuracy: Optional[float] = None
    timestamp: int


class DeviceCommand(BaseModel):
    """Command to send to device"""
    command: str
    data: Dict[str, Any] = {}


class AdminToken(BaseModel):
    """Admin authentication token"""
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Login request"""
    username: str
    password: str

