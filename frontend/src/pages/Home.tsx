// 首頁
import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { useAuth } from '../context/AuthContext';
import './Home.css';

export const Home: React.FC = () => {
  const { user, userType } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // 如果已登入，根據用戶類型重定向到相應的首頁
    if (user && userType) {
      if (userType === 'patient') {
        navigate('/patient/home', { replace: true });
      } else if (userType === 'provider') {
        navigate('/provider/sessions', { replace: true });
      }
    }
  }, [user, userType, navigate]);

  // 如果已登入，不渲染首頁內容（會重定向）
  if (user && userType) {
    return null;
  }

  return (
    <Layout>
      <div className="home">
        <div className="hero">
          <h1>歡迎使用診所數位化系統</h1>
          <p>請選擇您的身份以進行登入</p>
          <div className="hero-actions" style={{ marginTop: '2rem', display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/patient/login" className="btn btn-primary">
              我是病人
            </Link>
            <Link to="/provider/login" className="btn btn-secondary">
              我是醫師
            </Link>
          </div>
        </div>
      </div>
    </Layout>
  );
};

