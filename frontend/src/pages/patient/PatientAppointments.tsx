// 病人掛號管理頁面
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { patientApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layout } from '../../components/Layout';
import type { Appointment, ClinicSession } from '../../types';
import './PatientAppointments.css';

export const PatientAppointments: React.FC = () => {
  const { user, userType } = useAuth();
  const navigate = useNavigate();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [sessions, setSessions] = useState<ClinicSession[]>([]);
  const [groupedSessions, setGroupedSessions] = useState<Record<string, ClinicSession[]>>({});
  const [loading, setLoading] = useState(true);
  const [showBookForm, setShowBookForm] = useState(false);
  const [filters, setFilters] = useState({
    dept_id: '',
    provider_id: '',
    date: '',
  });
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);

  useEffect(() => {
    if (userType !== 'patient' || !user) {
      navigate('/patient/login');
      return;
    }
    loadData();
  }, [user, userType]);

  const groupSessionsByDepartment = (sess: ClinicSession[]) => {
    const grouped: Record<string, ClinicSession[]> = {};
    sess.forEach((session) => {
      const deptName = session.dept_name || '其他';
      if (!grouped[deptName]) {
        grouped[deptName] = [];
      }
      grouped[deptName].push(session);
    });
    
    // 對每個科別的門診依時間排序（先日期，再開始時間）
    Object.keys(grouped).forEach((deptName) => {
      grouped[deptName].sort((a, b) => {
        if (a.date !== b.date) {
          return a.date.localeCompare(b.date);
        }
        return a.start_time.localeCompare(b.start_time);
      });
    });
    
    return grouped;
  };

  const loadData = async () => {
    if (!user) return;
    try {
      const [appts, sess] = await Promise.all([
        patientApi.listAppointments(user.user_id),
        patientApi.listSessions(),
      ]);
      setAppointments(appts);
      setSessions(sess);
      setGroupedSessions(groupSessionsByDepartment(sess));
    } catch (err) {
      console.error('載入資料失敗:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSessions = async () => {
    try {
      const params: any = {};
      if (filters.dept_id) params.dept_id = parseInt(filters.dept_id);
      if (filters.provider_id) params.provider_id = parseInt(filters.provider_id);
      if (filters.date) params.date = filters.date;
      const sess = await patientApi.listSessions(params);
      setSessions(sess);
      setGroupedSessions(groupSessionsByDepartment(sess));
    } catch (err) {
      console.error('查詢失敗:', err);
    }
  };

  const handleBookAppointment = async () => {
    if (!selectedSessionId || !user) return;
    try {
      await patientApi.createAppointment(user.user_id, selectedSessionId);
      alert('掛號成功！');
      setShowBookForm(false);
      setSelectedSessionId(null);
      loadData();
    } catch (err: any) {
      console.error('掛號錯誤:', err);
      console.error('錯誤詳情:', err.response?.data);
      const errorDetail = err.response?.data?.detail;
      alert(errorDetail || '掛號失敗，請稍後再試');
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
      0: { text: '已取消', class: 'status-cancelled' },
      1: { text: '已預約', class: 'status-booked' },
      2: { text: '已報到', class: 'status-checked-in' },
      3: { text: '已完成', class: 'status-completed' },
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
          onClick={() => setShowBookForm(!showBookForm)}
        >
          {showBookForm ? '取消' : '新增掛號'}
        </button>

        {showBookForm && (
          <div className="book-form">
            <h2>查詢可預約門診</h2>
            <div className="filters">
              <input
                type="number"
                placeholder="科別 ID"
                value={filters.dept_id}
                onChange={(e) => setFilters({ ...filters, dept_id: e.target.value })}
              />
              <input
                type="number"
                placeholder="醫師 ID"
                value={filters.provider_id}
                onChange={(e) => setFilters({ ...filters, provider_id: e.target.value })}
              />
              <input
                type="date"
                value={filters.date}
                onChange={(e) => setFilters({ ...filters, date: e.target.value })}
              />
              <button className="btn btn-secondary" onClick={handleSearchSessions}>
                查詢
              </button>
            </div>
            <div className="sessions-list">
              {Object.keys(groupedSessions).length === 0 ? (
                <p>目前沒有可預約的門診</p>
              ) : (
                Object.entries(groupedSessions).map(([deptName, deptSessions]) => (
                  <div key={deptName} className="department-section">
                    <h3>{deptName}</h3>
                    <div className="sessions-grid">
                      {deptSessions.map((session) => {
                        const isAvailable = () => {
                          if (session.status === 0) return false;
                          if (session.booked_count >= session.capacity) return false;
                          const now = new Date();
                          const sessionDate = new Date(`${session.date}T${session.end_time}`);
                          return now <= sessionDate;
                        };
                        const available = isAvailable();
                        
                        return (
                          <div
                            key={session.session_id}
                            className={`session-card ${selectedSessionId === session.session_id ? 'selected' : ''} ${!available ? 'unavailable' : ''}`}
                            onClick={() => available && setSelectedSessionId(session.session_id)}
                          >
                            <div>
                              <strong>{session.provider_name}</strong>
                            </div>
                            <div>
                              {session.date} {session.start_time} - {session.end_time}
                            </div>
                            <div>
                              已預約: {session.booked_count || 0} / {session.capacity}
                            </div>
                            {!available && (
                              <div className="unavailable-badge">
                                {session.status === 0 ? '停診' : 
                                 session.booked_count >= session.capacity ? '已滿' : 
                                 '已過時段'}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))
              )}
            </div>
            {selectedSessionId && (
              <button className="btn btn-primary" onClick={handleBookAppointment}>
                確認掛號
              </button>
            )}
          </div>
        )}

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
                      {appt.status === 1 && (
                        <>
                          <button
                            className="btn-small btn-secondary"
                            onClick={() => {
                              setShowBookForm(true);
                              setSelectedSessionId(null);
                            }}
                          >
                            改期
                          </button>
                          <button
                            className="btn-small btn-danger"
                            onClick={() => handleCancel(appt.appt_id)}
                          >
                            取消
                          </button>
                        </>
                      )}
                      {appt.status === 1 && (
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

