// 病人註冊頁面
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { patientApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layout } from '../../components/Layout';
import './Auth.css';

export const PatientRegister: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    password: '',
    national_id: '',
    birth_date: '',
    sex: 'M' as 'M' | 'F' | 'O',
    phone: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // 驗證必填欄位
    if (!formData.name || !formData.password || !formData.national_id || !formData.birth_date || !formData.phone) {
      setError('請填寫所有必填欄位');
      setLoading(false);
      return;
    }

    // 驗證日期格式
    if (!formData.birth_date.match(/^\d{4}-\d{2}-\d{2}$/)) {
      setError('請選擇有效的日期');
      setLoading(false);
      return;
    }

    try {
      // 確保發送的數據格式正確
      const requestData = {
        name: formData.name.trim(),
        password: formData.password,
        national_id: formData.national_id.trim().toUpperCase(),
        birth_date: formData.birth_date,
        sex: formData.sex,
        phone: formData.phone.trim(),
      };
      
      console.log('發送註冊請求:', requestData);
      const user = await patientApi.register(requestData);
      login(user, 'patient');
      navigate('/patient/appointments');
    } catch (err: any) {
      // 只在開發環境顯示詳細錯誤
      if (process.env.NODE_ENV === 'development') {
      console.error('註冊錯誤:', err);
      console.error('錯誤詳情:', err.response?.data);
      }
      const errorDetail = err.response?.data?.detail;
      if (Array.isArray(errorDetail)) {
        // Pydantic 驗證錯誤
        const errorMessages = errorDetail.map((e: any) => {
          const field = e.loc && e.loc.length > 0 ? e.loc[e.loc.length - 1] : 'unknown';
          // 將欄位名稱轉換為中文
          const fieldMap: Record<string, string> = {
            'national_id': '身分證字號',
            'birth_date': '生日',
            'phone': '電話',
            'name': '姓名',
            'password': '密碼',
            'sex': '性別',
          };
          const fieldName = fieldMap[field] || field;
          return `${fieldName}: ${e.msg}`;
        }).join('；');
        setError(`驗證錯誤：${errorMessages}`);
      } else if (errorDetail) {
        setError(typeof errorDetail === 'string' ? errorDetail : '註冊失敗，請檢查輸入資料');
      } else {
        setError(err.message || '註冊失敗，請檢查輸入資料');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="auth-container">
        <div className="auth-card">
          <h2>病人註冊</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>姓名</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                placeholder="請輸入姓名"
              />
            </div>
            <div className="form-group">
              <label>身分證字號</label>
              <input
                type="text"
                value={formData.national_id}
                onChange={(e) => setFormData({ ...formData, national_id: e.target.value })}
                required
                placeholder="請輸入身分證字號"
              />
            </div>
            <div className="form-group">
              <label>密碼</label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                placeholder="請輸入密碼"
              />
            </div>
            <div className="form-group">
              <label>生日</label>
              <input
                type="date"
                value={formData.birth_date}
                onChange={(e) => setFormData({ ...formData, birth_date: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>性別</label>
              <select
                value={formData.sex}
                onChange={(e) => setFormData({ ...formData, sex: e.target.value as 'M' | 'F' | 'O' })}
                required
              >
                <option value="M">男</option>
                <option value="F">女</option>
                <option value="O">其他</option>
              </select>
            </div>
            <div className="form-group">
              <label>電話</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                required
                placeholder="請輸入電話"
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '註冊中...' : '註冊'}
            </button>
          </form>
          <p className="auth-link">
            已有帳號？ <Link to="/patient/login">立即登入</Link>
          </p>
        </div>
      </div>
    </Layout>
  );
};

