import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DeviceInfo } from '../types/device';
import { DeviceCard } from './DeviceCard';
import { removeToken, logout, getToken } from '../api/auth';
import '../styles/Dashboard.css';

interface DashboardProps {
  devices: DeviceInfo[];
  onLogout: () => void;
  onDeviceUpdate?: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ devices, onLogout, onDeviceUpdate }) => {
  const navigate = useNavigate();
  const [localDevices, setLocalDevices] = useState(devices);

  React.useEffect(() => {
    setLocalDevices(devices);
  }, [devices]);

  const handleDeviceRename = (deviceId: string, newName: string) => {
    setLocalDevices(prevDevices =>
      prevDevices.map(device =>
        device.id === deviceId ? { ...device, name: newName } : device
      )
    );
    if (onDeviceUpdate) {
      onDeviceUpdate();
    }
  };

  const handleLogout = async () => {
    const token = getToken();
    if (token) {
      try {
        await logout(token);
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    removeToken();
    onLogout();
  };

  const handleDeviceClick = (deviceId: string) => {
    navigate(`/device/${deviceId}`);
  };

  const onlineDevices = localDevices.filter(d => d.is_online);
  const offlineDevices = localDevices.filter(d => !d.is_online);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Kelya Virus</h1>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </header>

      <div className="dashboard-stats">
        <div className="stat-card">
          <div className="stat-value">{localDevices.length}</div>
          <div className="stat-label">Total Devices</div>
        </div>
        <div className="stat-card online">
          <div className="stat-value">{onlineDevices.length}</div>
          <div className="stat-label">Online</div>
        </div>
        <div className="stat-card offline">
          <div className="stat-value">{offlineDevices.length}</div>
          <div className="stat-label">Offline</div>
        </div>
      </div>

      {onlineDevices.length > 0 && (
        <div className="devices-section">
          <h2>Online Devices</h2>
          <div className="device-grid">
            {onlineDevices.map(device => (
              <DeviceCard 
                key={device.id} 
                device={device} 
                onClick={() => handleDeviceClick(device.id)}
                onRename={handleDeviceRename}
              />
            ))}
          </div>
        </div>
      )}

      {offlineDevices.length > 0 && (
        <div className="devices-section">
          <h2>Offline Devices</h2>
          <div className="device-grid">
            {offlineDevices.map(device => (
              <DeviceCard 
                key={device.id} 
                device={device} 
                onClick={() => handleDeviceClick(device.id)}
                onRename={handleDeviceRename}
              />
            ))}
          </div>
        </div>
      )}

      {localDevices.length === 0 && (
        <div className="no-devices">
          <h2>No devices connected</h2>
          <p>Waiting for devices to connect...</p>
        </div>
      )}
    </div>
  );
};

