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

// 從 localStorage 恢復登入狀態的輔助函數
const restoreAuthState = (): {
  user: Patient | Provider | null;
  userType: 'patient' | 'provider' | null;
} => {
  try {
    const savedUser = localStorage.getItem('user');
    const savedUserType = localStorage.getItem('userType');
    const loginTime = localStorage.getItem('loginTime');
    
    if (savedUser && savedUserType && loginTime) {
      const loginTimestamp = parseInt(loginTime, 10);
      const now = Date.now();
      const sevenDays = 7 * 24 * 60 * 60 * 1000; // 7天的毫秒數
      
      // 檢查是否在7天內
      if (now - loginTimestamp < sevenDays) {
        const parsedUser = JSON.parse(savedUser);
        return {
          user: parsedUser,
          userType: savedUserType as 'patient' | 'provider',
        };
      } else {
        // 過期，清除登入狀態
        localStorage.removeItem('user');
        localStorage.removeItem('userType');
        localStorage.removeItem('loginTime');
      }
    }
  } catch (error) {
    // 如果解析失敗，清除可能損壞的數據
    console.error('恢復登入狀態時發生錯誤:', error);
    localStorage.removeItem('user');
    localStorage.removeItem('userType');
    localStorage.removeItem('loginTime');
  }
  
  return { user: null, userType: null };
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  // 在初始化時就從 localStorage 恢復狀態，避免閃爍
  const restoredState = restoreAuthState();
  const [user, setUser] = useState<Patient | Provider | null>(restoredState.user);
  const [userType, setUserType] = useState<'patient' | 'provider' | null>(restoredState.userType);

  useEffect(() => {
    // 確保在組件掛載時再次檢查並恢復狀態（以防萬一）
    const state = restoreAuthState();
    if (state.user && state.userType) {
      setUser(state.user);
      setUserType(state.userType);
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
    localStorage.removeItem('loginTime');
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

