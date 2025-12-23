import React from 'react';
import { DeviceInfo } from '../../types/device';
import '../../styles/SystemInfo.css';

interface SystemInfoProps {
  device: DeviceInfo;
}

export const SystemInfo: React.FC<SystemInfoProps> = ({ device }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="system-info">
      <div className="info-section">
        <h3>Device Information</h3>
        <div className="info-grid">
          <div className="info-card">
            <div className="info-card-label">Device Name</div>
            <div className="info-card-value">{device.name}</div>
          </div>
          <div className="info-card">
            <div className="info-card-label">Device ID</div>
            <div className="info-card-value">{device.id}</div>
          </div>
          <div className="info-card">
            <div className="info-card-label">Manufacturer</div>
            <div className="info-card-value">{device.manufacturer}</div>
          </div>
          <div className="info-card">
            <div className="info-card-label">Model</div>
            <div className="info-card-value">{device.model}</div>
          </div>
          <div className="info-card">
            <div className="info-card-label">Android Version</div>
            <div className="info-card-value">{device.android_version}</div>
          </div>
          {device.imei && (
            <div className="info-card">
              <div className="info-card-label">IMEI</div>
              <div className="info-card-value">{device.imei}</div>
            </div>
          )}
        </div>
      </div>

      <div className="info-section">
        <h3>Status</h3>
        <div className="info-grid">
          <div className="info-card">
            <div className="info-card-label">Connection Status</div>
            <div className={`info-card-value ${device.is_online ? 'online' : 'offline'}`}>
              {device.is_online ? 'Online' : 'Offline'}
            </div>
          </div>
          <div className="info-card">
            <div className="info-card-label">Connected At</div>
            <div className="info-card-value">{formatDate(device.connected_at)}</div>
          </div>
          <div className="info-card">
            <div className="info-card-label">Last Activity</div>
            <div className="info-card-value">{formatDate(device.last_activity)}</div>
          </div>
          {device.battery_level !== undefined && (
            <div className="info-card">
              <div className="info-card-label">Battery Level</div>
              <div className="info-card-value">
                <div className="battery-indicator">
                  <div 
                    className="battery-fill" 
                    style={{ width: `${device.battery_level}%` }}
                  ></div>
                  <span className="battery-text">{device.battery_level}%</span>
                </div>
              </div>
            </div>
          )}
          <div className="info-card">
            <div className="info-card-label">Current Camera</div>
            <div className="info-card-value">{device.current_camera}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

