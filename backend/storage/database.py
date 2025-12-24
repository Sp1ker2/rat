"""Database storage operations"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
import uuid

from backend.database.models import Device, CameraFrame, LocationHistory, DeviceEvent
from backend.database import AsyncSessionLocal


class DatabaseStorage:
    """Handles database-based storage for device data"""
    
    async def create_device(self, device_id: str, name: str, token: str, **kwargs) -> Device:
        """Create a new device"""
        async with AsyncSessionLocal() as session:
            device = Device(
                id=uuid.UUID(device_id) if isinstance(device_id, str) else device_id,
                name=name,
                token=token,
                imei=kwargs.get("imei"),
                model=kwargs.get("model"),
                manufacturer=kwargs.get("manufacturer"),
                android_version=kwargs.get("android_version"),
                sdk=kwargs.get("sdk"),
                created_at=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                is_active=True
            )
            session.add(device)
            await session.commit()
            await session.refresh(device)
            
            # Log device creation
            print(f"[DB_CREATE_DEVICE] Created device in database: {name} (ID: {device_id})")
            print(f"[DB_CREATE_DEVICE] Model: {kwargs.get('manufacturer', 'N/A')} {kwargs.get('model', 'N/A')}")
            print(f"[DB_CREATE_DEVICE] Android: {kwargs.get('android_version', 'N/A')} (SDK: {kwargs.get('sdk', 'N/A')})")
            print(f"[DB_CREATE_DEVICE] IMEI: {kwargs.get('imei', 'N/A')}, Token: {token[:16]}...")
            
            return device
    
    async def get_device(self, device_id: str) -> Optional[Device]:
        """Get device by ID"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Device).where(Device.id == uuid.UUID(device_id) if isinstance(device_id, str) else device_id)
            )
            return result.scalar_one_or_none()
    
    async def get_device_by_token(self, token: str) -> Optional[Device]:
        """Get device by token"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Device).where(Device.token == token)
            )
            return result.scalar_one_or_none()
    
    async def update_device(self, device_id: str, **kwargs) -> Optional[Device]:
        """Update device information"""
        async with AsyncSessionLocal() as session:
            # Получаем устройство в той же сессии
            result = await session.execute(
                select(Device).where(Device.id == uuid.UUID(device_id) if isinstance(device_id, str) else device_id)
            )
            device = result.scalar_one_or_none()
            
            if not device:
                print(f"[DB_UPDATE_DEVICE] Device not found: {device_id}")
                return None
            
            updated_fields = []
            for key, value in kwargs.items():
                if hasattr(device, key) and value is not None:
                    old_value = getattr(device, key)
                    setattr(device, key, value)
                    if old_value != value:
                        updated_fields.append(f"{key}: {old_value} -> {value}")
            
            device.last_seen = datetime.utcnow()
            await session.commit()
            await session.refresh(device)
            
            # Log update
            if updated_fields:
                print(f"[DB_UPDATE_DEVICE] Updated device in database: {device.name} (ID: {device_id})")
                print(f"[DB_UPDATE_DEVICE] Updated fields: {', '.join(updated_fields)}")
            
            return device
    
    async def list_devices(self) -> List[Device]:
        """List all devices"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Device))
            return list(result.scalars().all())
    
    async def save_camera_frame(
        self, 
        device_id: str, 
        camera: str, 
        frame_data: bytes, 
        width: int,
        height: int,
        timestamp: int
    ) -> CameraFrame:
        """Save camera frame"""
        async with AsyncSessionLocal() as session:
            frame_size = len(frame_data)
            frame = CameraFrame(
                id=uuid.uuid4(),
                device_id=uuid.UUID(device_id) if isinstance(device_id, str) else device_id,
                camera=camera,
                frame_data=frame_data,
                width=width,
                height=height,
                timestamp=timestamp,
                created_at=datetime.utcnow()
            )
            session.add(frame)
            await session.commit()
            await session.refresh(frame)
            
            # Log frame save
            print(f"[DB_SAVE_FRAME] Saved camera frame to database: Device {device_id}, Camera: {camera}")
            print(f"[DB_SAVE_FRAME] Frame size: {frame_size} bytes, Resolution: {width}x{height}")
            print(f"[DB_SAVE_FRAME] Timestamp: {timestamp}, Frame ID: {frame.id}")
            
            return frame
    
    async def get_latest_frame(self, device_id: str, camera: str) -> Optional[CameraFrame]:
        """Get the latest camera frame"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CameraFrame)
                .where(
                    CameraFrame.device_id == (uuid.UUID(device_id) if isinstance(device_id, str) else device_id),
                    CameraFrame.camera == camera
                )
                .order_by(desc(CameraFrame.timestamp))
                .limit(1)
            )
            return result.scalar_one_or_none()
    
    async def get_frame_history(
        self, 
        device_id: str, 
        camera: str, 
        limit: int = 100,
        offset: int = 0
    ) -> List[CameraFrame]:
        """Get camera frame history"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CameraFrame)
                .where(
                    CameraFrame.device_id == (uuid.UUID(device_id) if isinstance(device_id, str) else device_id),
                    CameraFrame.camera == camera
                )
                .order_by(desc(CameraFrame.timestamp))
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
    
    async def save_location(
        self, 
        device_id: str, 
        lat: float, 
        lon: float, 
        accuracy: Optional[float],
        timestamp: int
    ) -> LocationHistory:
        """Save location update"""
        async with AsyncSessionLocal() as session:
            location = LocationHistory(
                id=uuid.uuid4(),
                device_id=uuid.UUID(device_id) if isinstance(device_id, str) else device_id,
                lat=lat,
                lon=lon,
                accuracy=accuracy,
                timestamp=timestamp,
                created_at=datetime.utcnow()
            )
            session.add(location)
            await session.commit()
            await session.refresh(location)
            
            # Log location save
            accuracy_str = f"{accuracy:.1f}m" if accuracy else "N/A"
            print(f"[DB_SAVE_LOCATION] Saved location to database: Device {device_id}")
            print(f"[DB_SAVE_LOCATION] Coordinates: {lat:.6f}, {lon:.6f}, Accuracy: {accuracy_str}")
            print(f"[DB_SAVE_LOCATION] Timestamp: {timestamp}, Location ID: {location.id}")
            
            return location
    
    async def get_location_history(
        self, 
        device_id: str, 
        limit: int = 100,
        offset: int = 0
    ) -> List[LocationHistory]:
        """Get location history"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(LocationHistory)
                .where(
                    LocationHistory.device_id == (uuid.UUID(device_id) if isinstance(device_id, str) else device_id)
                )
                .order_by(desc(LocationHistory.timestamp))
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
    
    async def log_device_event(
        self, 
        device_id: str, 
        event_type: str, 
        event_data: Optional[Dict] = None,
        timestamp: Optional[int] = None
    ) -> DeviceEvent:
        """Log device event"""
        async with AsyncSessionLocal() as session:
            event_timestamp = timestamp or int(datetime.utcnow().timestamp() * 1000)
            event = DeviceEvent(
                id=uuid.uuid4(),
                device_id=uuid.UUID(device_id) if isinstance(device_id, str) else device_id,
                event_type=event_type,
                event_data=event_data or {},
                timestamp=event_timestamp,
                created_at=datetime.utcnow()
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)
            
            # Log event save
            event_data_str = f", Data: {event_data}" if event_data else ""
            print(f"[DB_LOG_EVENT] Saved event to database: Device {device_id}, Type: {event_type}{event_data_str}")
            print(f"[DB_LOG_EVENT] Timestamp: {event_timestamp}, Event ID: {event.id}")
            
            return event
    
    async def get_device_events(
        self,
        device_id: str,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DeviceEvent]:
        """Get device events"""
        async with AsyncSessionLocal() as session:
            query = select(DeviceEvent).where(
                DeviceEvent.device_id == (uuid.UUID(device_id) if isinstance(device_id, str) else device_id)
            )
            
            if event_type:
                query = query.where(DeviceEvent.event_type == event_type)
            
            result = await session.execute(
                query
                .order_by(desc(DeviceEvent.timestamp))
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
    
    async def cleanup_old_frames(self, device_id: str, camera: str, keep: int = 10):
        """Keep only the N most recent frames (optional cleanup)"""
        # For now, we keep all frames in database
        # Can be implemented later with scheduled cleanup job
        pass


# Global storage instance
storage = DatabaseStorage()


