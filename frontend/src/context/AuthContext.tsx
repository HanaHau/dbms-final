// 認證上下文
import React, { createContext, useContext, useState, useEffect } from 'react';
import type { Patient, Provider } from '../types';

interface AuthContextType {
  user: Patient | Provider | null;
  userType: 'patient' | 'provider' | null;
  login: (user: Patient | Provider, type: 'patient' | 'provider') => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<Patient | Provider | null>(null);
  const [userType, setUserType] = useState<'patient' | 'provider' | null>(null);

  useEffect(() => {
    // 從 localStorage 恢復登入狀態（7天過期）
    const savedUser = localStorage.getItem('user');
    const savedUserType = localStorage.getItem('userType');
    const loginTime = localStorage.getItem('loginTime');
    
    if (savedUser && savedUserType && loginTime) {
      const loginTimestamp = parseInt(loginTime, 10);
      const now = Date.now();
      const sevenDays = 7 * 24 * 60 * 60 * 1000; // 7天的毫秒數
      
      // 檢查是否在7天內
      if (now - loginTimestamp < sevenDays) {
        setUser(JSON.parse(savedUser));
        setUserType(savedUserType as 'patient' | 'provider');
      } else {
        // 過期，清除登入狀態
        localStorage.removeItem('user');
        localStorage.removeItem('userType');
        localStorage.removeItem('loginTime');
      }
    }
  }, []);

  const login = (userData: Patient | Provider, type: 'patient' | 'provider') => {
    setUser(userData);
    setUserType(type);
    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem('userType', type);
    localStorage.setItem('loginTime', Date.now().toString());
  };

  const logout = () => {
    setUser(null);
    setUserType(null);
    localStorage.removeItem('user');
    localStorage.removeItem('userType');
  };

  return (
    <AuthContext.Provider value={{ user, userType, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

