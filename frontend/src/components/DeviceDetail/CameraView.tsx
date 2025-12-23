import React, { useState, useEffect, useCallback } from 'react';
import { sendCommand } from '../../api/devices';
import { getToken } from '../../api/auth';
import { DeviceInfo } from '../../types/device';
import '../../styles/CameraView.css';

interface CameraViewProps {
  deviceId: string;
  device: DeviceInfo;
}

export const CameraView: React.FC<CameraViewProps> = ({ deviceId, device }) => {
  const [activeCamera, setActiveCamera] = useState(device.current_camera || 'back');
  const [frameUrl, setFrameUrl] = useState<string>('');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchFrame = useCallback(async () => {
    const token = getToken();
    if (!token) return;

    try {
      const url = `${window.location.origin}/api/devices/${deviceId}/camera/${activeCamera}?t=${Date.now()}`;
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        setFrameUrl(imageUrl);
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error('Error fetching frame:', error);
    }
  }, [deviceId, activeCamera]);

  useEffect(() => {
    fetchFrame();
    const interval = setInterval(fetchFrame, 500); // Update 2 times per second

    return () => {
      clearInterval(interval);
      if (frameUrl) {
        URL.revokeObjectURL(frameUrl);
      }
    };
  }, [fetchFrame, frameUrl]);

  const handleSwitchCamera = async (camera: 'front' | 'back') => {
    const token = getToken();
    if (!token) return;

    try {
      await sendCommand(token, deviceId, {
        command: 'switch_camera',
        data: { camera }
      });
      setActiveCamera(camera);
    } catch (error) {
      console.error('Error switching camera:', error);
    }
  };

  return (
    <div className="camera-view">
      <div className="camera-controls">
        <button
          className={activeCamera === 'back' ? 'active' : ''}
          onClick={() => handleSwitchCamera('back')}
          disabled={!device.is_online}
        >
          Back Camera
        </button>
        <button
          className={activeCamera === 'front' ? 'active' : ''}
          onClick={() => handleSwitchCamera('front')}
          disabled={!device.is_online}
        >
          Front Camera
        </button>
      </div>

      <div className="camera-frame-container">
        {frameUrl ? (
          <img
            src={frameUrl}
            alt="Live camera feed"
            className="camera-frame"
          />
        ) : (
          <div className="no-frame">
            {device.is_online ? 'Waiting for camera frame...' : 'Device offline'}
          </div>
        )}
      </div>

      <div className="camera-info">
        <div className="info-item">
          <span className="info-label">Active Camera:</span>
          <span className="info-value">{activeCamera}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Last Update:</span>
          <span className="info-value">{lastUpdate.toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
};

