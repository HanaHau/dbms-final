// 醫師登入頁面
import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { providerApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layout } from '../../components/Layout';
import '../patient/Auth.css';

export const ProviderLogin: React.FC = () => {
  const [licenseNo, setLicenseNo] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login, user, userType } = useAuth();

  useEffect(() => {
    // 如果已登入，重定向到相應的首頁
    if (user && userType === 'provider') {
      navigate('/provider/sessions', { replace: true });
    } else if (user && userType === 'patient') {
      navigate('/patient/home', { replace: true });
    }
  }, [user, userType, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await providerApi.login({ license_no: licenseNo, password });
      login(user, 'provider');
      navigate('/provider/sessions');
    } catch (err: any) {
      setError(err.response?.data?.detail || '登入失敗，請檢查帳號密碼');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="auth-container">
        <div className="auth-card">
          <h2>醫師登入</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>醫師執照號碼</label>
              <input
                type="text"
                value={licenseNo}
                onChange={(e) => setLicenseNo(e.target.value)}
                required
                placeholder="請輸入執照號碼"
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
            還沒有帳號？ <Link to="/provider/register">醫師註冊</Link>
          </p>
          <p className="auth-link">
            其實我是病人？ <Link to="/patient/login">前往病人登入</Link>
          </p>
        </div>
      </div>
    </Layout>
  );
};

