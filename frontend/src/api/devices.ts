import axios from 'axios';
import { DeviceInfo, Command } from '../types/device';

const API_URL = window.location.origin;

const getHeaders = (token: string) => ({
  headers: { Authorization: `Bearer ${token}` }
});

export const getDevices = async (token: string): Promise<DeviceInfo[]> => {
  const response = await axios.get<DeviceInfo[]>(`${API_URL}/api/devices`, getHeaders(token));
  return response.data;
};

export const getDevice = async (token: string, deviceId: string): Promise<DeviceInfo> => {
  const response = await axios.get<DeviceInfo>(`${API_URL}/api/devices/${deviceId}`, getHeaders(token));
  return response.data;
};

export const sendCommand = async (token: string, deviceId: string, command: Command): Promise<void> => {
  await axios.post(`${API_URL}/api/devices/${deviceId}/command`, command, getHeaders(token));
};

export const getCameraFrame = async (token: string, deviceId: string, camera: string): Promise<string> => {
  const response = await axios.get(`${API_URL}/api/devices/${deviceId}/camera/${camera}`, {
    ...getHeaders(token),
    responseType: 'blob'
  });
  return URL.createObjectURL(response.data);
};

export const getLocationHistory = async (token: string, deviceId: string): Promise<any> => {
  const response = await axios.get(`${API_URL}/api/devices/${deviceId}/location`, getHeaders(token));
  return response.data;
};

