"""Device API endpoints"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from backend.models import DeviceSession, DeviceCommand, DeviceRegistration, DeviceRegistrationResponse, DeviceTokenResponse, RenameDeviceRequest
from backend.devices.manager import session_manager
from backend.websocket.handler import ws_manager
from backend.storage.database import storage
from backend.devices.registration import register_device_manually, get_device_by_token, regenerate_device_token
from backend.auth.router import get_current_admin
from backend.config import SERVER_HOST, SERVER_PORT

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=List[DeviceSession])
async def get_devices(_: str = Depends(get_current_admin)):
    """Get all devices"""
    # Get devices from both session manager (online) and database (all)
    db_devices = await storage.list_devices()
    session_devices = session_manager.get_all_devices()
    
    # Create a map of session devices by ID
    session_map = {s.device_id: s for s in session_devices}
    
    # Combine: use session data if available, otherwise create from DB
    result = []
    for db_device in db_devices:
        device_id = str(db_device.id)
        if device_id in session_map:
            result.append(session_map[device_id])
        else:
            # Create DeviceSession from DB device
            from backend.models import DeviceSession
            from datetime import datetime
            result.append(DeviceSession(
                device_id=device_id,
                device_name=db_device.name,
                imei=db_device.imei,
                model=db_device.model or "Unknown",
                manufacturer=db_device.manufacturer or "Unknown",
                android_version=db_device.android_version or "Unknown",
                connected_at=db_device.created_at,
                last_activity=db_device.last_seen,
                is_online=False
            ))
    
    return result


@router.get("/{device_id}", response_model=DeviceSession)
async def get_device(device_id: str, _: str = Depends(get_current_admin)):
    """Get device details"""
    # Try to get from session first, then from database
    device = session_manager.get_device(device_id)
    if not device:
        # Get from database
        db_device = await storage.get_device(device_id)
        if not db_device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Create DeviceSession from DB device
        from backend.models import DeviceSession
        from datetime import datetime
        device = DeviceSession(
            device_id=str(db_device.id),
            device_name=db_device.name,
            imei=db_device.imei,
            model=db_device.model or "Unknown",
            manufacturer=db_device.manufacturer or "Unknown",
            android_version=db_device.android_version or "Unknown",
            connected_at=db_device.created_at,
            last_activity=db_device.last_seen,
            is_online=False
        )
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
    frame = await storage.get_latest_frame(device_id, camera)
    if not frame:
        raise HTTPException(status_code=404, detail="No frame available")
    
    from fastapi.responses import Response
    return Response(content=frame.frame_data, media_type="image/jpeg")


@router.get("/{device_id}/camera/{camera}/history")
async def get_camera_history(
    device_id: str,
    camera: str,
    limit: int = Query(100, ge=1, le=1000, description="Number of frames to retrieve"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    _: str = Depends(get_current_admin)
):
    """Get camera frame history"""
    frames = await storage.get_frame_history(device_id, camera, limit, offset)
    
    return {
        "device_id": device_id,
        "camera": camera,
        "total": len(frames),
        "limit": limit,
        "offset": offset,
        "frames": [
            {
                "id": str(f.id),
                "width": f.width,
                "height": f.height,
                "timestamp": f.timestamp,
                "created_at": f.created_at.isoformat()
            }
            for f in frames
        ]
    }


@router.get("/{device_id}/location")
async def get_location_history(
    device_id: str,
    limit: int = 100,
    _: str = Depends(get_current_admin)
):
    """Get location history"""
    history = await storage.get_location_history(device_id, limit)
    return {
        "device_id": device_id,
        "history": [
            {
                "id": str(h.id),
                "lat": h.lat,
                "lon": h.lon,
                "accuracy": h.accuracy,
                "timestamp": h.timestamp,
                "created_at": h.created_at.isoformat()
            }
            for h in history
        ]
    }


@router.post("/register", response_model=DeviceRegistrationResponse)
async def register_device(
    registration: DeviceRegistration,
    _: str = Depends(get_current_admin)
):
    """Manually register a new device with a name"""
    device = await register_device_manually(
        name=registration.name,
        imei=registration.imei,
        model=registration.model,
        manufacturer=registration.manufacturer,
        android_version=registration.android_version,
        sdk=registration.sdk
    )
    
    return DeviceRegistrationResponse(
        device_id=str(device.id),
        name=device.name,
        token=device.token
    )


@router.get("/{device_id}/token", response_model=DeviceTokenResponse)
async def get_device_token(
    device_id: str,
    _: str = Depends(get_current_admin)
):
    """Get device registration token"""
    device = await storage.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    server_url = f"wss://kelyastream.duckdns.org" if SERVER_HOST == "0.0.0.0" else f"ws://{SERVER_HOST}:{SERVER_PORT}"
    connection_url = f"{server_url}/ws/device?token={device.token}"
    
    return DeviceTokenResponse(
        device_id=str(device.id),
        token=device.token,
        connection_url=connection_url
    )




@router.post("/{device_id}/regenerate-token", response_model=DeviceTokenResponse)
async def regenerate_token(
    device_id: str,
    _: str = Depends(get_current_admin)
):
    """Regenerate device registration token"""
    try:
        new_token = await regenerate_device_token(device_id)
        device = await storage.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        server_url = f"wss://kelyastream.duckdns.org" if SERVER_HOST == "0.0.0.0" else f"ws://{SERVER_HOST}:{SERVER_PORT}"
        connection_url = f"{server_url}/ws/device?token={new_token}"
        
        return DeviceTokenResponse(
            device_id=str(device.id),
            token=new_token,
            connection_url=connection_url
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{device_id}/rename")
async def rename_device(
    device_id: str,
    request: RenameDeviceRequest,
    _: str = Depends(get_current_admin)
):
    """Rename a device"""
    # Update in database
    device = await storage.update_device(device_id, name=request.name)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Update in session if online
    if device_id in session_manager.sessions:
        session_manager.sessions[device_id].device_name = request.name
    
    # Log event
    await storage.log_device_event(device_id, "renamed", {"new_name": request.name})
    
    return {
        "device_id": device_id,
        "name": request.name,
        "message": "Device renamed successfully"
    }

