"""SQLAlchemy database models"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, BigInteger, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, BYTEA, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.database import Base


class Device(Base):
    """Device model"""
    __tablename__ = "devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    imei = Column(String(32), nullable=True)
    model = Column(String(255), nullable=True)
    manufacturer = Column(String(255), nullable=True)
    android_version = Column(String(50), nullable=True)
    sdk = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    camera_frames = relationship("CameraFrame", back_populates="device", cascade="all, delete-orphan")
    location_history = relationship("LocationHistory", back_populates="device", cascade="all, delete-orphan")
    device_events = relationship("DeviceEvent", back_populates="device", cascade="all, delete-orphan")


class CameraFrame(Base):
    """Camera frame model"""
    __tablename__ = "camera_frames"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    camera = Column(String(10), nullable=False)  # "front" or "back"
    frame_data = Column(BYTEA, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    timestamp = Column(BigInteger, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship
    device = relationship("Device", back_populates="camera_frames")


class LocationHistory(Base):
    """Location history model"""
    __tablename__ = "location_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True)
    timestamp = Column(BigInteger, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship
    device = relationship("Device", back_populates="location_history")


class DeviceEvent(Base):
    """Device event model"""
    __tablename__ = "device_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSONB, nullable=True)
    timestamp = Column(BigInteger, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship
    device = relationship("Device", back_populates="device_events")


