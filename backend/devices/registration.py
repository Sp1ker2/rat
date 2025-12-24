"""Device registration with token generation"""
import secrets
import uuid
from typing import Optional

from backend.storage.database import storage
from backend.database.models import Device


def generate_device_token() -> str:
    """Generate a secure random token for device registration"""
    return secrets.token_urlsafe(32)


async def register_device_manually(name: str, **kwargs) -> Device:
    """Register a device manually with a generated token"""
    device_id = str(uuid.uuid4())
    token = generate_device_token()
    
    device = await storage.create_device(
        device_id=device_id,
        name=name,
        token=token,
        **kwargs
    )
    
    return device


async def get_device_by_token(token: str) -> Optional[Device]:
    """Get device by registration token"""
    return await storage.get_device_by_token(token)


async def regenerate_device_token(device_id: str) -> str:
    """Regenerate token for a device"""
    new_token = generate_device_token()
    device = await storage.update_device(device_id, token=new_token)
    if device:
        return new_token
    raise ValueError(f"Device {device_id} not found")

