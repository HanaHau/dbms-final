// 病人掛號管理頁面
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { patientApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layout } from '../../components/Layout';
import type { Appointment } from '../../types';
import './PatientAppointments.css';

export const PatientAppointments: React.FC = () => {
  const { user, userType } = useAuth();
  const navigate = useNavigate();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (userType !== 'patient' || !user) {
      navigate('/patient/login');
      return;
    }
    loadData();
  }, [user, userType]);

  const loadData = async () => {
    if (!user) return;
    try {
      const appts = await patientApi.listAppointments(user.user_id);
      setAppointments(appts);
    } catch (err) {
      console.error('載入資料失敗:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (apptId: number) => {
    if (!user || !confirm('確定要取消這個掛號嗎？')) return;
    try {
      await patientApi.cancelAppointment(apptId, user.user_id);
      alert('已取消掛號');
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '取消失敗');
    }
  };


  const handleCheckin = async (apptId: number) => {
    if (!user) return;
    try {
      await patientApi.checkin(apptId, user.user_id);
      alert('報到成功！');
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '報到失敗');
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
      <div className="patient-appointments">
        <h1>我的掛號</h1>
        <button
          className="btn btn-primary"
          onClick={() => navigate('/patient/home')}
        >
          新增掛號
        </button>

        <div className="appointments-list">
          <h2>掛號記錄</h2>
          {appointments.length === 0 ? (
            <p>目前沒有掛號記錄</p>
          ) : (
            <table className="appointments-table">
              <thead>
                <tr>
                  <th>日期時間</th>
                  <th>醫師</th>
                  <th>科別</th>
                  <th>序號</th>
                  <th>狀態</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {appointments.map((appt) => (
                  <tr key={appt.appt_id}>
                    <td>
                      {appt.session_date} {appt.session_start_time}
                    </td>
                    <td>{appt.provider_name}</td>
                    <td>{appt.dept_name}</td>
                    <td>{appt.slot_seq}</td>
                    <td>{getStatusBadge(appt.status)}</td>
                    <td>
                      {(appt.status === 1 || appt.status === 5) && (
                        <button
                          className="btn-small btn-danger"
                          onClick={() => handleCancel(appt.appt_id)}
                        >
                          取消
                        </button>
                      )}
                      {(appt.status === 1 || appt.status === 5) && (
                        <button
                          className="btn-small btn-primary"
                          onClick={() => handleCheckin(appt.appt_id)}
                        >
                          報到
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </Layout>
  );
};

