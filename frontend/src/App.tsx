import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Login } from './components/Login';
import { Dashboard } from './components/Dashboard';
import { DeviceDetail } from './components/DeviceDetail';
import { getToken, verifyToken, removeToken } from './api/auth';
import { useWebSocket } from './hooks/useWebSocket';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);

  const { devices } = useWebSocket(token);

  useEffect(() => {
    const checkAuth = async () => {
      const savedToken = getToken();
      
      if (savedToken) {
        const valid = await verifyToken(savedToken);
        if (valid) {
          setIsAuthenticated(true);
          setToken(savedToken);
        } else {
          removeToken();
          setIsAuthenticated(false);
        }
      }
      
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const handleLogin = () => {
    const savedToken = getToken();
    if (savedToken) {
      setToken(savedToken);
      setIsAuthenticated(true);
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setToken(null);
  };

  if (isLoading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Loading...</div>;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to="/" /> : <Login onLogin={handleLogin} />
          }
        />
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <Dashboard devices={devices} onLogout={handleLogout} />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="/device/:deviceId"
          element={
            isAuthenticated ? (
              <DeviceDetail />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

