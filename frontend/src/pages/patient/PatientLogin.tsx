// 病人登入頁面
import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { patientApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layout } from '../../components/Layout';
import './Auth.css';

export const PatientLogin: React.FC = () => {
  const [nationalId, setNationalId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login, user, userType } = useAuth();

  useEffect(() => {
    // 如果已登入，重定向到相應的首頁
    if (user && userType === 'patient') {
      navigate('/patient/home', { replace: true });
    } else if (user && userType === 'provider') {
      navigate('/provider/sessions', { replace: true });
    }
  }, [user, userType, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await patientApi.login({ national_id: nationalId.trim().toUpperCase(), password });
      login(user, 'patient');
      navigate('/patient/appointments');
    } catch (err: any) {
      // 只在開發環境顯示詳細錯誤
      if (process.env.NODE_ENV === 'development') {
        console.error('登入錯誤:', err);
        console.error('錯誤詳情:', err.response?.data);
      }
      const errorDetail = err.response?.data?.detail;
      if (errorDetail) {
        setError(typeof errorDetail === 'string' ? errorDetail : '登入失敗，請檢查帳號密碼');
      } else {
        setError('登入失敗，請檢查帳號密碼是否正確');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="auth-container">
        <div className="auth-card">
          <h2>病人登入</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>身分證字號</label>
              <input
                type="text"
                value={nationalId}
                onChange={(e) => setNationalId(e.target.value)}
                required
                placeholder="請輸入身分證字號"
              />
            </div>
            <div className="form-group">
              <label>密碼</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="請輸入密碼"
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '登入中...' : '登入'}
            </button>
          </form>
          <p className="auth-link">
            還沒有帳號？ <Link to="/patient/register">病人註冊</Link>
          </p>
          <p className="auth-link">
            其實我是醫師？ <Link to="/provider/login">前往醫師登入</Link>
          </p>
        </div>
      </div>
    </Layout>
  );
};

