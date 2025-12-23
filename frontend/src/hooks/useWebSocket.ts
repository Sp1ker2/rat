import { useEffect, useRef, useState, useCallback } from 'react';
import { DeviceInfo } from '../types/device';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export const useWebSocket = (token: string | null) => {
  const ws = useRef<WebSocket | null>(null);
  const [devices, setDevices] = useState<DeviceInfo[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/admin?token=${token}`;

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.current.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);

        switch (data.type) {
          case 'device_list':
            setDevices(data.devices || []);
            break;
          case 'device_connected':
            setDevices(prev => [...prev, data.device]);
            break;
          case 'device_disconnected':
            setDevices(prev => prev.filter(d => d.id !== data.device_id));
            break;
          case 'device_update':
            setDevices(prev => prev.map(d =>
              d.id === data.device_id ? { ...d, ...data.data } : d
            ));
            break;
        }
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };

    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.current?.close();
    };
  }, [token]);

  const sendCommand = useCallback((deviceId: string, command: string, data: any = {}) => {
    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify({
        type: 'command',
        device_id: deviceId,
        command,
        data
      }));
    }
  }, [isConnected]);

  return { devices, isConnected, sendCommand };
};

