import React, { useState } from 'react';
import { DeviceInfo } from '../types/device';
import { renameDevice } from '../api/devices';
import { getToken } from '../api/auth';
import '../styles/DeviceCard.css';

interface DeviceCardProps {
  device: DeviceInfo;
  onClick: () => void;
  onRename?: (deviceId: string, newName: string) => void;
}

export const DeviceCard: React.FC<DeviceCardProps> = ({ device, onClick, onRename }) => {
  const [isRenaming, setIsRenaming] = useState(false);
  const [newName, setNewName] = useState(device.name);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getTimeSince = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  const handleRename = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!newName.trim()) return;
    
    const token = getToken();
    if (!token) return;
    
    try {
      await renameDevice(token, device.id, newName.trim());
      if (onRename) {
        onRename(device.id, newName.trim());
      }
      setIsRenaming(false);
    } catch (error) {
      console.error('Error renaming device:', error);
      alert('Failed to rename device');
    }
  };

  return (
    <div 
      className={`device-card ${device.is_online ? 'online' : 'offline'}`}
      onClick={onClick}
    >
      <div className="device-header">
        {isRenaming ? (
          <div className="device-name-edit">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onClick={(e) => e.stopPropagation()}
              className="device-name-input"
              autoFocus
            />
            <button
              onClick={handleRename}
              className="device-name-save"
              title="Save"
            >
              ✓
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsRenaming(false);
                setNewName(device.name);
              }}
              className="device-name-cancel"
              title="Cancel"
            >
              ✕
            </button>
          </div>
        ) : (
          <div className="device-name-container">
            <h3>{device.name}</h3>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsRenaming(true);
                setNewName(device.name);
              }}
              className="device-rename-btn"
              title="Rename device"
            >
              ✏️
            </button>
          </div>
        )}
        <span className={`status-badge ${device.is_online ? 'online' : 'offline'}`}>
          {device.is_online ? 'Online' : 'Offline'}
        </span>
      </div>

      <div className="device-info">
        <div className="info-row">
          <span className="info-label">Model:</span>
          <span className="info-value">{device.manufacturer} {device.model}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Android:</span>
          <span className="info-value">{device.android_version}</span>
        </div>
        {device.battery_level !== undefined && (
          <div className="info-row">
            <span className="info-label">Battery:</span>
            <span className="info-value">{device.battery_level}%</span>
          </div>
        )}
        <div className="info-row">
          <span className="info-label">Last seen:</span>
          <span className="info-value">{getTimeSince(device.last_activity)}</span>
        </div>
      </div>
    </div>
  );
};

