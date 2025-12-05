// 病人掛號管理頁面
import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { patientApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layout } from '../../components/Layout';
import type { Appointment } from '../../types';
import { getPeriodDisplayName } from '../../lib/periodUtils';
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

  // 格式化日期顯示：2025/2/26（四）
  const formatDateDisplay = (dateStr: string): string => {
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
    const weekday = weekdays[date.getDay()];
    return `${year}/${month}/${day}（${weekday}）`;
  };

  // 將掛號分類到三個區塊
  const { upcomingAppointments, pastAppointments, cancelledAppointments } = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const upcoming: Appointment[] = [];
    const past: Appointment[] = [];
    const cancelled: Appointment[] = [];

    appointments.forEach((appt) => {
      const apptDate = new Date(appt.session_date);
      apptDate.setHours(0, 0, 0, 0);

      // 已取消的項目獨立成一個區塊
      if (appt.status === 4) {
        cancelled.push(appt);
      } else if (apptDate >= today) {
        // 今天和未來的門診（未取消）
        upcoming.push(appt);
      } else {
        // 過去的門診（未取消）
        past.push(appt);
      }
    });

    return { upcomingAppointments: upcoming, pastAppointments: past, cancelledAppointments: cancelled };
  }, [appointments]);

  // 渲染掛號項目（統一格式：日期（年月日）、星期（括號）、時段名稱、科別、醫師、狀態）
  const renderAppointmentItem = (appt: Appointment, showCheckin: boolean = false) => {
    const dateDisplay = formatDateDisplay(appt.session_date);
    const periodDisplay = appt.session_period ? getPeriodDisplayName(appt.session_period) : '';
    
    return (
      <div key={appt.appt_id} className="appointment-item">
        <div className="appointment-info">
          <span className="appointment-date">
            {dateDisplay} {periodDisplay}
          </span>
          <span className="appointment-separator">—</span>
          <span className="appointment-dept">{appt.dept_name}</span>
          <span className="appointment-separator">—</span>
          <span className="appointment-provider">{appt.provider_name}</span>
          {appt.status !== 4 && (
            <>
              <span className="appointment-separator">—</span>
              <span className="appointment-status">{getStatusBadge(appt.status)}</span>
            </>
          )}
        </div>
        <div className="appointment-actions">
          {(appt.status === 1 || appt.status === 5) && (
            <>
              <button
                className="btn-small btn-danger"
                onClick={() => handleCancel(appt.appt_id)}
              >
                取消
              </button>
              {showCheckin && (
                <button
                  className="btn-small btn-primary"
                  onClick={() => handleCheckin(appt.appt_id)}
                >
                  報到
                </button>
              )}
            </>
          )}
        </div>
      </div>
    );
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

        {appointments.length === 0 ? (
          <div className="appointments-empty">
            <p>目前沒有掛號記錄</p>
          </div>
        ) : (
          <div className="appointments-sections">
            {/* 區塊 1：即將到來的門診 */}
            {upcomingAppointments.length > 0 && (
              <div className="appointment-section upcoming-section">
                <h2 className="section-title">📅 即將到來的門診</h2>
                <div className="section-divider"></div>
                <div className="appointment-list">
                  {upcomingAppointments.map((appt) => {
                    const isToday = new Date(appt.session_date).toDateString() === new Date().toDateString();
                    return renderAppointmentItem(appt, isToday);
                  })}
                </div>
              </div>
            )}

            {/* 區塊 2：過去的門診 */}
            {pastAppointments.length > 0 && (
              <div className="appointment-section past-section">
                <h2 className="section-title">📁 過去門診紀錄</h2>
                <div className="section-divider"></div>
                <div className="appointment-list">
                  {pastAppointments.map((appt) => {
                    const dateDisplay = formatDateDisplay(appt.session_date);
                    const periodDisplay = appt.session_period ? getPeriodDisplayName(appt.session_period) : '';
                    return (
                      <div key={appt.appt_id} className="appointment-item">
                        <div className="appointment-info">
                          <span className="appointment-date">
                            {dateDisplay} {periodDisplay}
                          </span>
                          <span className="appointment-separator">—</span>
                          <span className="appointment-dept">{appt.dept_name}</span>
                          <span className="appointment-separator">—</span>
                          <span className="appointment-provider">{appt.provider_name}</span>
                          <span className="appointment-separator">—</span>
                          <span className="appointment-status">{getStatusBadge(appt.status)}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* 區塊 3：已取消的掛號 */}
            {cancelledAppointments.length > 0 && (
              <div className="appointment-section cancelled-section">
                <h2 className="section-title">❌ 已取消掛號</h2>
                <div className="section-divider"></div>
                <div className="appointment-list">
                  {cancelledAppointments.map((appt) => {
                    const dateDisplay = formatDateDisplay(appt.session_date);
                    const periodDisplay = appt.session_period ? getPeriodDisplayName(appt.session_period) : '';
                    return (
                      <div key={appt.appt_id} className="appointment-item">
                        <div className="appointment-info">
                          <span className="appointment-date">
                            {dateDisplay} {periodDisplay}
                          </span>
                          <span className="appointment-separator">—</span>
                          <span className="appointment-dept">{appt.dept_name}</span>
                          <span className="appointment-separator">—</span>
                          <span className="appointment-provider">{appt.provider_name}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
};

