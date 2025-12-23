export interface DeviceInfo {
  id: string;
  name: string;
  model: string;
  manufacturer: string;
  android_version: string;
  imei?: string;
  connected_at: string;
  last_activity: string;
  current_camera: string;
  location?: Location;
  battery_level?: number;
  is_online: boolean;
}

export interface Location {
  lat: number;
  lon: number;
  accuracy?: number;
  timestamp: number;
}

export interface CameraFrame {
  camera: string;
  width: number;
  height: number;
  timestamp: number;
}

export interface Command {
  command: string;
  data: Record<string, any>;
}

