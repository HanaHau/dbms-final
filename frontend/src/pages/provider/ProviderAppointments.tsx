// 醫師預約管理頁面
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { providerApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layout } from '../../components/Layout';
import type { Appointment } from '../../types';
import './ProviderAppointments.css';

export const ProviderAppointments: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { user, userType } = useAuth();
  const navigate = useNavigate();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (userType !== 'provider' || !user || !sessionId) {
      navigate('/provider/login');
      return;
    }
    loadAppointments();
  }, [user, userType, sessionId]);

  const loadAppointments = async () => {
    if (!user || !sessionId) return;
    try {
      const data = await providerApi.listAppointments(user.user_id, parseInt(sessionId));
      setAppointments(data);
    } catch (err) {
      console.error('載入預約失敗:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: number) => {
    const statusMap: Record<number, { text: string; class: string }> = {
      1: { text: '已預約', class: 'status-booked' },
      2: { text: '已報到', class: 'status-checked-in' },
      3: { text: '已完成', class: 'status-completed' },
      4: { text: '已取消', class: 'status-cancelled' },
      5: { text: '未報到', class: 'status-no-show' },
      6: { text: '候補', class: 'status-waitlisted' },
    };
    const s = statusMap[status] || { text: '未知', class: 'status-unknown' };
    return <span className={`status-badge ${s.class}`}>{s.text}</span>;
  };

  if (loading) return <Layout><div>載入中...</div></Layout>;

  return (
    <Layout>
      <div className="provider-appointments">
        <button className="btn btn-secondary" onClick={() => navigate('/provider/sessions')}>
          ← 返回門診時段
        </button>
        <h1>預約管理 - Session #{sessionId}</h1>
        {appointments.length === 0 ? (
          <p>目前沒有預約</p>
        ) : (
          <table className="appointments-table">
            <thead>
              <tr>
                <th>序號</th>
                <th>病人姓名</th>
                <th>狀態</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((appt) => (
                <tr key={appt.appt_id}>
                  <td>{appt.slot_seq}</td>
                  <td>{appt.patient_name}</td>
                  <td>{getStatusBadge(appt.status)}</td>
                  <td>
                    {appt.status === 2 && (
                      <button
                        className="btn btn-primary btn-small"
                        onClick={() => navigate(`/provider/encounter/${appt.appt_id}`)}
                      >
                        建立就診記錄
                      </button>
                    )}
                    {appt.status >= 3 && (
                      <button
                        className="btn btn-primary btn-small"
                        onClick={() => navigate(`/provider/encounter/${appt.appt_id}`)}
                      >
                        查看/編輯就診記錄
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  );
};

