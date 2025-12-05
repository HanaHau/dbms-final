// 醫師註冊頁面
import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { providerApi, patientApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layout } from '../../components/Layout';
import '../patient/Auth.css';

interface Department {
  dept_id: number;
  name: string;
}

export const ProviderRegister: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    password: '',
    license_no: '',
    dept_id: 0,
  });
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loadingDepartments, setLoadingDepartments] = useState(true);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    loadDepartments();
  }, []);

  const loadDepartments = async () => {
    try {
      setLoadingDepartments(true);
      const depts = await patientApi.listDepartments();
      setDepartments(depts);
      // 如果有科別，設置第一個為預設值
      if (depts.length > 0) {
        setFormData(prev => ({ ...prev, dept_id: depts[0].dept_id }));
      }
    } catch (err) {
      console.error('載入科別列表失敗:', err);
      setError('無法載入科別列表，請重新整理頁面');
    } finally {
      setLoadingDepartments(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // 驗證必填欄位
    if (!formData.name || !formData.password || !formData.license_no || !formData.dept_id) {
      setError('請填寫所有必填欄位');
      setLoading(false);
      return;
    }

    // 驗證科別 ID
    if (formData.dept_id <= 0) {
      setError('請選擇科別');
      setLoading(false);
      return;
    }

    try {
      // 確保發送的數據格式正確
      const requestData = {
        name: formData.name.trim(),
        password: formData.password,
        license_no: formData.license_no.trim(),
        dept_id: formData.dept_id,
      };
      
      console.log('發送註冊請求:', requestData);
      const user = await providerApi.register(requestData);
      login(user, 'provider');
      navigate('/provider/sessions');
    } catch (err: any) {
      console.error('註冊錯誤:', err);
      console.error('錯誤詳情:', err.response?.data);
      const errorDetail = err.response?.data?.detail;
      if (Array.isArray(errorDetail)) {
        // Pydantic 驗證錯誤
        const errorMessages = errorDetail.map((e: any) => {
          const field = e.loc && e.loc.length > 0 ? e.loc[e.loc.length - 1] : 'unknown';
          return `${field}: ${e.msg}`;
        }).join(', ');
        setError(`驗證錯誤: ${errorMessages}`);
      } else if (errorDetail) {
        // 顯示更具體的錯誤訊息
        let displayError = errorDetail;
        if (errorDetail.includes('執照號碼') || errorDetail.includes('license_no')) {
          displayError = '此執照號碼已被使用，請使用不同的執照號碼。';
        } else if (errorDetail.includes('科別') || errorDetail.includes('dept_id')) {
          displayError = '科別 ID 不存在，請確認科別 ID 是否正確。';
        }
        setError(displayError);
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
          <h2>醫師註冊</h2>
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
              <label>醫師執照號碼</label>
              <input
                type="text"
                value={formData.license_no}
                onChange={(e) => setFormData({ ...formData, license_no: e.target.value })}
                required
                placeholder="請輸入執照號碼"
              />
            </div>
            <div className="form-group">
              <label>科別</label>
              <select
                value={formData.dept_id}
                onChange={(e) => setFormData({ ...formData, dept_id: parseInt(e.target.value) })}
                required
                disabled={loadingDepartments}
              >
                {loadingDepartments ? (
                  <option value={0}>載入中...</option>
                ) : departments.length === 0 ? (
                  <option value={0}>無可用科別</option>
                ) : (
                  departments.map((dept) => (
                    <option key={dept.dept_id} value={dept.dept_id}>
                      {dept.name}
                    </option>
                  ))
                )}
              </select>
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
            {error && <div className="error-message">{error}</div>}
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '註冊中...' : '註冊'}
            </button>
          </form>
          <p className="auth-link">
            已有帳號？ <Link to="/provider/login">立即登入</Link>
          </p>
        </div>
      </div>
    </Layout>
  );
};

