"""Device API endpoints"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from backend.models import DeviceSession, DeviceCommand
from backend.devices.manager import session_manager
from backend.websocket.handler import ws_manager
from backend.storage.files import storage
from backend.auth.router import get_current_admin

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=List[DeviceSession])
async def get_devices(_: str = Depends(get_current_admin)):
    """Get all devices"""
    return session_manager.get_all_devices()


@router.get("/{device_id}", response_model=DeviceSession)
async def get_device(device_id: str, _: str = Depends(get_current_admin)):
    """Get device details"""
    device = session_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("/{device_id}/command")
async def send_command(
    device_id: str, 
    command: DeviceCommand,
    _: str = Depends(get_current_admin)
):
    """Send command to device"""
    success = await ws_manager.send_command(device_id, command)
    if not success:
        raise HTTPException(status_code=404, detail="Device not connected")
    return {"status": "success", "message": "Command sent"}


@router.get("/{device_id}/camera/{camera}")
async def get_camera_frame(
    device_id: str, 
    camera: str,
    _: str = Depends(get_current_admin)
):
    """Get latest camera frame"""
    frame_data = await storage.get_latest_frame(device_id, camera)
    if not frame_data:
        raise HTTPException(status_code=404, detail="No frame available")
    
    from fastapi.responses import Response
    return Response(content=frame_data, media_type="image/jpeg")


@router.get("/{device_id}/location")
async def get_location_history(
    device_id: str,
    limit: int = 100,
    _: str = Depends(get_current_admin)
):
    """Get location history"""
    history = await storage.get_location_history(device_id, limit)
    return {"device_id": device_id, "history": history}

