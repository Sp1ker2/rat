"""File storage operations"""
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import aiofiles
import aiofiles.os

from backend.config import DEVICES_DIR


class FileStorage:
    """Handles file-based storage for device data"""
    
    def __init__(self):
        self.devices_dir = DEVICES_DIR
    
    async def create_device_folder(self, device_id: str) -> Path:
        """Create folder structure for a new device"""
        device_dir = self.devices_dir / device_id
        
        # Create directories
        await aiofiles.os.makedirs(device_dir, exist_ok=True)
        await aiofiles.os.makedirs(device_dir / "cameras" / "front", exist_ok=True)
        await aiofiles.os.makedirs(device_dir / "cameras" / "back", exist_ok=True)
        await aiofiles.os.makedirs(device_dir / "location", exist_ok=True)
        await aiofiles.os.makedirs(device_dir / "messages", exist_ok=True)
        await aiofiles.os.makedirs(device_dir / "calls", exist_ok=True)
        await aiofiles.os.makedirs(device_dir / "logs", exist_ok=True)
        
        return device_dir
    
    async def save_device_info(self, device_id: str, info: Dict[str, Any]):
        """Save device metadata"""
        device_dir = self.devices_dir / device_id
        info_file = device_dir / "info.json"
        
        async with aiofiles.open(info_file, 'w') as f:
            await f.write(json.dumps(info, indent=2, default=str))
    
    async def load_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Load device metadata"""
        info_file = self.devices_dir / device_id / "info.json"
        
        try:
            async with aiofiles.open(info_file, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except FileNotFoundError:
            return None
    
    async def save_camera_frame(self, device_id: str, camera: str, frame_data: bytes, timestamp: int):
        """Save camera frame as JPEG"""
        device_dir = self.devices_dir / device_id
        frame_file = device_dir / "cameras" / camera / f"frame_{timestamp}.jpg"
        
        async with aiofiles.open(frame_file, 'wb') as f:
            await f.write(frame_data)
        
        # Keep only last 10 frames per camera
        await self._cleanup_old_frames(device_dir / "cameras" / camera, keep=10)
    
    async def get_latest_frame(self, device_id: str, camera: str) -> Optional[bytes]:
        """Get the latest camera frame"""
        camera_dir = self.devices_dir / device_id / "cameras" / camera
        
        try:
            frames = sorted(camera_dir.glob("frame_*.jpg"), reverse=True)
            if frames:
                async with aiofiles.open(frames[0], 'rb') as f:
                    return await f.read()
        except FileNotFoundError:
            pass
        
        return None
    
    async def save_location(self, device_id: str, location: Dict[str, Any]):
        """Append location to history"""
        location_file = self.devices_dir / device_id / "location" / "history.jsonl"
        
        async with aiofiles.open(location_file, 'a') as f:
            await f.write(json.dumps(location, default=str) + '\n')
    
    async def get_location_history(self, device_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get location history"""
        location_file = self.devices_dir / device_id / "location" / "history.jsonl"
        
        try:
            history = []
            async with aiofiles.open(location_file, 'r') as f:
                async for line in f:
                    if line.strip():
                        history.append(json.loads(line))
            
            return history[-limit:]  # Return last N entries
        except FileNotFoundError:
            return []
    
    async def log_device_event(self, device_id: str, event: str, data: Optional[Dict] = None):
        """Log device event"""
        log_file = self.devices_dir / device_id / "logs" / "device.log"
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "data": data or {}
        }
        
        async with aiofiles.open(log_file, 'a') as f:
            await f.write(json.dumps(log_entry, default=str) + '\n')
    
    async def _cleanup_old_frames(self, camera_dir: Path, keep: int):
        """Keep only the N most recent frames"""
        try:
            frames = sorted(camera_dir.glob("frame_*.jpg"), reverse=True)
            for old_frame in frames[keep:]:
                await aiofiles.os.remove(old_frame)
        except Exception as e:
            print(f"Error cleaning up frames: {e}")
    
    def list_devices(self) -> List[str]:
        """List all device IDs"""
        try:
            return [d.name for d in self.devices_dir.iterdir() if d.is_dir()]
        except FileNotFoundError:
            return []


# Global storage instance
storage = FileStorage()

