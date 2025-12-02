// 共用佈局組件
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Layout.css';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, userType, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  // 根據登入狀態決定 logo 連結
  const getLogoLink = () => {
    if (user && userType === 'patient') {
      return '/patient/home';
    } else if (user && userType === 'provider') {
      return '/provider/sessions';
    }
    return '/';
  };

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <Link to={getLogoLink()} className="logo">
            <h1>診所數位化系統</h1>
          </Link>
          <nav className="nav">
            {user ? (
              <>
                {userType === 'patient' ? (
                  <>
                    <Link to="/patient/home">首頁</Link>
                    <Link to="/patient/appointments">我的掛號</Link>
                    <Link to="/patient/history">就診記錄</Link>
                    <Link to="/patient/payments">繳費記錄</Link>
                  </>
                ) : (
                  <>
                    <Link to="/provider/sessions">門診時段</Link>
                  </>
                )}
                <span className="user-name">{user.name}</span>
                <button onClick={handleLogout} className="logout-btn">
                  登出
                </button>
              </>
            ) : (
              <>
                <Link to="/patient/login">病人登入</Link>
                <Link to="/provider/login">醫師登入</Link>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="main-content">{children}</main>
      <footer className="footer">
        <p>&copy; 2025 診所數位化系統</p>
      </footer>
    </div>
  );
};

