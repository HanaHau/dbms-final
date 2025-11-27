// 首頁
import React from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../components/Layout';
import './Home.css';

export const Home: React.FC = () => {
  return (
    <Layout>
      <div className="home">
        <div className="hero">
          <h1>歡迎使用診所數位化系統</h1>
          <p>提供完整的病人端和醫師端功能</p>
        </div>
        <div className="features">
          <div className="feature-card">
            <h2>病人端</h2>
            <ul>
              <li>線上掛號</li>
              <li>查詢就診記錄</li>
              <li>查看處方箋</li>
              <li>線上繳費</li>
            </ul>
            <div className="actions">
              <Link to="/patient/login" className="btn btn-primary">
                病人登入
              </Link>
              <Link to="/patient/register" className="btn btn-secondary">
                病人註冊
              </Link>
            </div>
          </div>
          <div className="feature-card">
            <h2>醫師端</h2>
            <ul>
              <li>門診時段管理</li>
              <li>預約管理</li>
              <li>就診記錄</li>
              <li>診斷與處方</li>
            </ul>
            <div className="actions">
              <Link to="/provider/login" className="btn btn-primary">
                醫師登入
              </Link>
              <Link to="/provider/register" className="btn btn-secondary">
                醫師註冊
              </Link>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

