import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup } from 'react-leaflet';
import { getLocationHistory } from '../../api/devices';
import { getToken } from '../../api/auth';
import { DeviceInfo, Location } from '../../types/device';
import 'leaflet/dist/leaflet.css';
import '../../styles/LocationMap.css';

// Fix for default marker icons in react-leaflet
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

interface LocationMapProps {
  deviceId: string;
  device: DeviceInfo;
}

export const LocationMap: React.FC<LocationMapProps> = ({ deviceId, device }) => {
  const [history, setHistory] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadHistory = async () => {
      const token = getToken();
      if (!token) return;

      try {
        const data = await getLocationHistory(token, deviceId);
        setHistory(data.history || []);
      } catch (error) {
        console.error('Error loading location history:', error);
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
    const interval = setInterval(loadHistory, 10000); // Refresh every 10 seconds

    return () => clearInterval(interval);
  }, [deviceId]);

  if (loading) {
    return <div className="loading">Loading map...</div>;
  }

  const currentLocation = device.location || (history.length > 0 ? history[history.length - 1] : null);

  if (!currentLocation) {
    return (
      <div className="no-location">
        <p>No location data available</p>
      </div>
    );
  }

  const center: [number, number] = [currentLocation.lat, currentLocation.lon];
  const historyPath: [number, number][] = history.map(h => [h.lat, h.lon]);

  return (
    <div className="location-map">
      <div className="map-container">
        <MapContainer 
          center={center} 
          zoom={13} 
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />

          {/* Current location marker */}
          <Marker position={center}>
            <Popup>
              <strong>Current Location</strong><br />
              Lat: {currentLocation.lat.toFixed(6)}<br />
              Lon: {currentLocation.lon.toFixed(6)}<br />
              {currentLocation.accuracy && `Accuracy: ${currentLocation.accuracy.toFixed(2)}m`}
            </Popup>
          </Marker>

          {/* Location history trail */}
          {historyPath.length > 1 && (
            <Polyline 
              positions={historyPath} 
              color="#667eea"
              weight={3}
              opacity={0.7}
            />
          )}
        </MapContainer>
      </div>

      <div className="location-info-panel">
        <h3>Location Details</h3>
        <div className="location-details">
          <div className="detail-row">
            <span className="detail-label">Latitude:</span>
            <span className="detail-value">{currentLocation.lat.toFixed(6)}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Longitude:</span>
            <span className="detail-value">{currentLocation.lon.toFixed(6)}</span>
          </div>
          {currentLocation.accuracy && (
            <div className="detail-row">
              <span className="detail-label">Accuracy:</span>
              <span className="detail-value">{currentLocation.accuracy.toFixed(2)} m</span>
            </div>
          )}
          <div className="detail-row">
            <span className="detail-label">History Points:</span>
            <span className="detail-value">{history.length}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Last Update:</span>
            <span className="detail-value">
              {new Date(currentLocation.timestamp).toLocaleString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

