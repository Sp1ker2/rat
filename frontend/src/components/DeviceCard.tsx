import React from 'react';
import { DeviceInfo } from '../types/device';
import '../styles/DeviceCard.css';

interface DeviceCardProps {
  device: DeviceInfo;
  onClick: () => void;
}

export const DeviceCard: React.FC<DeviceCardProps> = ({ device, onClick }) => {
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

  return (
    <div 
      className={`device-card ${device.is_online ? 'online' : 'offline'}`}
      onClick={onClick}
    >
      <div className="device-header">
        <h3>{device.name}</h3>
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

