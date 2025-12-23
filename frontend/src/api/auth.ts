import axios from 'axios';

const API_URL = window.location.origin;

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export const login = async (username: string, password: string): Promise<string> => {
  const response = await axios.post<LoginResponse>(`${API_URL}/api/auth/login`, {
    username,
    password
  });
  return response.data.access_token;
};

export const logout = async (token: string): Promise<void> => {
  await axios.post(`${API_URL}/api/auth/logout`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  });
};

export const verifyToken = async (token: string): Promise<boolean> => {
  try {
    await axios.get(`${API_URL}/api/auth/verify`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return true;
  } catch {
    return false;
  }
};

export const saveToken = (token: string) => {
  localStorage.setItem('auth_token', token);
};

export const getToken = (): string | null => {
  return localStorage.getItem('auth_token');
};

export const removeToken = () => {
  localStorage.removeItem('auth_token');
};

