import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getDevice, renameDevice } from '../../api/devices';
import { getToken } from '../../api/auth';
import { DeviceInfo } from '../../types/device';
import { CameraView } from './CameraView';
import { LocationMap } from './LocationMap';
import { SystemInfo } from './SystemInfo';
import '../../styles/DeviceDetail.css';

export const DeviceDetail: React.FC = () => {
  const { deviceId } = useParams<{ deviceId: string }>();
  const navigate = useNavigate();
  const [device, setDevice] = useState<DeviceInfo | null>(null);
  const [activeTab, setActiveTab] = useState('camera');
  const [loading, setLoading] = useState(true);
  const [isRenaming, setIsRenaming] = useState(false);
  const [newName, setNewName] = useState('');

  useEffect(() => {
    const loadDevice = async () => {
      const token = getToken();
      if (!token || !deviceId) {
        navigate('/');
        return;
      }

      try {
        const deviceData = await getDevice(token, deviceId);
        setDevice(deviceData);
      } catch (error) {
        console.error('Error loading device:', error);
        navigate('/');
      } finally {
        setLoading(false);
      }
    };

    loadDevice();
    const interval = setInterval(loadDevice, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, [deviceId, navigate]);

  if (loading) {
    return <div className="loading">Loading device...</div>;
  }

  if (!device) {
    return <div className="error">Device not found</div>;
  }

  return (
    <div className="device-detail">
      <header className="device-detail-header">
        <button onClick={() => navigate('/')} className="back-btn">
          ← Back
        </button>
        <div className="device-title">
          {isRenaming ? (
            <div className="rename-container">
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="rename-input"
                placeholder="Enter new name"
                autoFocus
              />
              <button
                onClick={async () => {
                  const token = getToken();
                  if (!token || !deviceId || !newName.trim()) return;
                  
                  try {
                    await renameDevice(token, deviceId, newName.trim());
                    setDevice({ ...device, name: newName.trim() });
                    setIsRenaming(false);
                    setNewName('');
                  } catch (error) {
                    console.error('Error renaming device:', error);
                    alert('Failed to rename device');
                  }
                }}
                className="rename-save-btn"
              >
                Save
              </button>
              <button
                onClick={() => {
                  setIsRenaming(false);
                  setNewName('');
                }}
                className="rename-cancel-btn"
              >
                Cancel
              </button>
            </div>
          ) : (
            <div className="device-name-container">
              <h1>{device.name}</h1>
              <button
                onClick={() => {
                  setNewName(device.name);
                  setIsRenaming(true);
                }}
                className="rename-btn"
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
      </header>

      <div className="device-tabs">
        <button
          className={activeTab === 'camera' ? 'active' : ''}
          onClick={() => setActiveTab('camera')}
        >
          Camera
        </button>
        <button
          className={activeTab === 'location' ? 'active' : ''}
          onClick={() => setActiveTab('location')}
        >
          Location
        </button>
        <button
          className={activeTab === 'system' ? 'active' : ''}
          onClick={() => setActiveTab('system')}
        >
          System Info
        </button>
      </div>

      <div className="device-content">
        {activeTab === 'camera' && deviceId && (
          <CameraView deviceId={deviceId} device={device} />
        )}
        {activeTab === 'location' && deviceId && (
          <LocationMap deviceId={deviceId} device={device} />
        )}
        {activeTab === 'system' && (
          <SystemInfo device={device} />
        )}
      </div>
    </div>
  );
};

