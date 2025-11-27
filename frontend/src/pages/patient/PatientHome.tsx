// 病人首頁 - 依科別顯示所有門診
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { patientApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layout } from '../../components/Layout';
import type { ClinicSession } from '../../types';
import './PatientHome.css';

export const PatientHome: React.FC = () => {
  const { user, userType } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<ClinicSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);
  const [groupedSessions, setGroupedSessions] = useState<Record<string, ClinicSession[]>>({});

  useEffect(() => {
    if (userType !== 'patient' || !user) {
      navigate('/patient/login');
      return;
    }
    loadSessions();
  }, [user, userType]);

  const loadSessions = async () => {
    try {
      const data = await patientApi.listSessions();
      setSessions(data);
      
      // 依科別分組
      const grouped: Record<string, ClinicSession[]> = {};
      data.forEach((session) => {
        const deptName = session.dept_name || '其他';
        if (!grouped[deptName]) {
          grouped[deptName] = [];
        }
        grouped[deptName].push(session);
      });
      setGroupedSessions(grouped);
    } catch (err) {
      console.error('載入門診失敗:', err);
    } finally {
      setLoading(false);
    }
  };

  const isSessionAvailable = (session: ClinicSession): boolean => {
    if (session.status === 0) return false; // 停診
    if (session.booked_count >= session.capacity) return false; // 已滿
    
    // 檢查是否已過門診時間
    const now = new Date();
    const sessionDate = new Date(`${session.date}T${session.end_time}`);
    if (now > sessionDate) return false; // 已過時間
    
    return true;
  };

  const handleBookAppointment = async () => {
    if (!selectedSessionId || !user) return;
    
    const session = sessions.find(s => s.session_id === selectedSessionId);
    if (!session || !isSessionAvailable(session)) {
      alert('此門診時段無法預約');
      return;
    }

    try {
      await patientApi.createAppointment(user.user_id, selectedSessionId);
      alert('掛號成功！');
      navigate('/patient/appointments');
    } catch (err: any) {
      console.error('掛號錯誤:', err);
      const errorDetail = err.response?.data?.detail;
      alert(errorDetail || '掛號失敗，請稍後再試');
    }
  };

  const formatTime = (timeStr: string) => {
    if (!timeStr) return '';
    const time = timeStr.split(':');
    return `${time[0]}:${time[1]}`;
  };

  if (loading) return <Layout><div>載入中...</div></Layout>;

  return (
    <Layout>
      <div className="patient-home">
        <h1>可預約門診</h1>
        <p>請選擇您要預約的門診時段</p>

        {Object.keys(groupedSessions).length === 0 ? (
          <p>目前沒有可預約的門診</p>
        ) : (
          Object.entries(groupedSessions).map(([deptName, deptSessions]) => (
            <div key={deptName} className="department-section">
              <h2>{deptName}</h2>
              <div className="sessions-grid">
                {deptSessions.map((session) => {
                  const available = isSessionAvailable(session);
                  return (
                    <div
                      key={session.session_id}
                      className={`session-card ${selectedSessionId === session.session_id ? 'selected' : ''} ${!available ? 'unavailable' : ''}`}
                      onClick={() => available && setSelectedSessionId(session.session_id)}
                    >
                      <div className="session-header">
                        <strong>{session.provider_name || '醫師'}</strong>
                      </div>
                      <div className="session-info">
                        <div>日期：{session.date}</div>
                        <div>時間：{formatTime(session.start_time)} - {formatTime(session.end_time)}</div>
                        <div>已預約：{session.booked_count || 0} / {session.capacity}</div>
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

        {selectedSessionId && (
          <div className="booking-actions">
            <button className="btn btn-primary" onClick={handleBookAppointment}>
              確認掛號
            </button>
            <button className="btn btn-secondary" onClick={() => setSelectedSessionId(null)}>
              取消選擇
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
};

