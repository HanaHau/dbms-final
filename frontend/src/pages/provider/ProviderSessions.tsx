// 醫師門診時段管理頁面
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { providerApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layout } from '../../components/Layout';
import type { ClinicSession } from '../../types';
import './ProviderSessions.css';

export const ProviderSessions: React.FC = () => {
  const { user, userType } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<ClinicSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [filters, setFilters] = useState({
    from_date: '',
    to_date: '',
    status: '',
  });
  const [formData, setFormData] = useState({
    date: '',
    start_time: '',
    end_time: '',
    capacity: 10,
    status: 1,
  });

  useEffect(() => {
    if (userType !== 'provider' || !user) {
      navigate('/provider/login');
      return;
    }
    loadSessions();
  }, [user, userType]);

  const loadSessions = async () => {
    if (!user) return;
    try {
      const params: any = {};
      if (filters.from_date) params.from_date = filters.from_date;
      if (filters.to_date) params.to_date = filters.to_date;
      if (filters.status) params.status = parseInt(filters.status);
      const data = await providerApi.listSessions(user.user_id, params);
      setSessions(data);
    } catch (err) {
      console.error('載入門診時段失敗:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, [filters]);

  const handleCreate = async () => {
    if (!user) return;
    try {
      await providerApi.createSession(user.user_id, {
        date: formData.date,
        start_time: formData.start_time,
        end_time: formData.end_time,
        capacity: formData.capacity,
      });
      alert('建立成功！');
      setShowForm(false);
      resetForm();
      loadSessions();
    } catch (err: any) {
      alert(err.response?.data?.detail || '建立失敗');
    }
  };

  const handleUpdate = async () => {
    if (!user || !editingId) return;
    try {
      await providerApi.updateSession(user.user_id, editingId, formData);
      alert('更新成功！');
      setEditingId(null);
      resetForm();
      loadSessions();
    } catch (err: any) {
      alert(err.response?.data?.detail || '更新失敗');
    }
  };

  const handleCancel = async (sessionId: number) => {
    if (!user || !confirm('確定要取消這個門診時段嗎？')) return;
    try {
      await providerApi.cancelSession(user.user_id, sessionId);
      alert('已取消門診');
      loadSessions();
    } catch (err: any) {
      alert(err.response?.data?.detail || '取消失敗');
    }
  };

  const resetForm = () => {
    setFormData({
      date: '',
      start_time: '',
      end_time: '',
      capacity: 10,
      status: 1,
    });
    setShowForm(false);
    setEditingId(null);
  };

  const startEdit = (session: ClinicSession) => {
    setEditingId(session.session_id);
    setFormData({
      date: session.date,
      start_time: session.start_time,
      end_time: session.end_time,
      capacity: session.capacity,
      status: session.status,
    });
    setShowForm(true);
  };

  // 分類門診時段
  const categorizeSessions = (sessions: ClinicSession[]) => {
    const now = new Date();
    const currentDate = now.toISOString().split('T')[0]; // YYYY-MM-DD
    const currentTime = now.toTimeString().split(' ')[0].substring(0, 5); // HH:MM

    const active: ClinicSession[] = [];
    const upcoming: ClinicSession[] = [];
    const cancelled: ClinicSession[] = [];

    sessions.forEach((session) => {
      // 已停診
      if (session.status === 0) {
        cancelled.push(session);
        return;
      }

      // 正常狀態的門診
      const sessionDate = session.date;
      const sessionStartTime = session.start_time.substring(0, 5); // HH:MM
      const sessionEndTime = session.end_time.substring(0, 5); // HH:MM

      // 正在看診：今天且當前時間在 start_time 和 end_time 之間
      if (sessionDate === currentDate && 
          currentTime >= sessionStartTime && 
          currentTime <= sessionEndTime) {
        active.push(session);
      } 
      // 未來門診：日期在未來，或日期是今天但時間在 start_time 之前
      else if (sessionDate > currentDate || 
               (sessionDate === currentDate && currentTime < sessionStartTime)) {
        upcoming.push(session);
      }
      // 其他情況（已過期的正常門診：日期在過去，或日期是今天但時間在 end_time 之後）歸類為已停診
      else {
        cancelled.push(session);
      }
    });

    // 未來門診依時間排序（先日期，再開始時間）
    upcoming.sort((a, b) => {
      if (a.date !== b.date) {
        return a.date.localeCompare(b.date);
      }
      return a.start_time.localeCompare(b.start_time);
    });

    return { active, upcoming, cancelled };
  };

  if (loading) return <Layout><div>載入中...</div></Layout>;

  return (
    <Layout>
      <div className="provider-sessions">
        <h1>門診時段管理</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? '取消' : '新增門診時段'}
        </button>

        <div className="filters">
          <input
            type="date"
            placeholder="開始日期"
            value={filters.from_date}
            onChange={(e) => setFilters({ ...filters, from_date: e.target.value })}
          />
          <input
            type="date"
            placeholder="結束日期"
            value={filters.to_date}
            onChange={(e) => setFilters({ ...filters, to_date: e.target.value })}
          />
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
            <option value="">全部狀態</option>
            <option value="0">停診</option>
            <option value="1">正常</option>
          </select>
        </div>

        {showForm && (
          <div className="session-form">
            <h2>{editingId ? '編輯' : '新增'}門診時段</h2>
            <div className="form-row">
              <div className="form-group">
                <label>日期</label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>開始時間</label>
                <input
                  type="time"
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>結束時間</label>
                <input
                  type="time"
                  value={formData.end_time}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>人數上限</label>
                <input
                  type="number"
                  value={formData.capacity || ''}
                  onChange={(e) => {
                    const val = e.target.value;
                    const num = val === '' ? 0 : parseInt(val, 10);
                    setFormData({ ...formData, capacity: isNaN(num) ? 0 : num });
                  }}
                  required
                  min="1"
                />
              </div>
              {editingId && (
                <div className="form-group">
                  <label>狀態</label>
                  <select
                    value={formData.status}
                    onChange={(e) => {
                      const val = parseInt(e.target.value, 10);
                      setFormData({ ...formData, status: isNaN(val) ? 1 : val });
                    }}
                  >
                    <option value="0">停診</option>
                    <option value="1">正常</option>
                  </select>
                </div>
              )}
            </div>
            <div className="form-actions">
              <button
                className="btn btn-primary"
                onClick={editingId ? handleUpdate : handleCreate}
              >
                {editingId ? '更新' : '建立'}
              </button>
              <button className="btn btn-secondary" onClick={resetForm}>
                取消
              </button>
            </div>
          </div>
        )}

        <div className="sessions-list">
          {sessions.length === 0 ? (
            <p>目前沒有門診時段</p>
          ) : (
            (() => {
              const { active, upcoming, cancelled } = categorizeSessions(sessions);
              
              // 格式化時間，只顯示時分
              const formatTime = (timeStr: string) => {
                if (!timeStr) return '';
                const time = timeStr.split(':');
                return `${time[0]}:${time[1]}`;
              };

              // 渲染門診時段表格
              const renderSessionTable = (sessionList: ClinicSession[], title: string) => {
                if (sessionList.length === 0) return null;
                
                return (
                  <div className="session-category">
                    <h2>{title} ({sessionList.length})</h2>
                    <table className="sessions-table">
                      <thead>
                        <tr>
                          <th>日期</th>
                          <th>時間</th>
                          <th>人數上限</th>
                          <th>已預約</th>
                          <th>狀態</th>
                          <th>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sessionList.map((session) => (
                          <tr key={session.session_id}>
                            <td>{session.date}</td>
                            <td className="time-cell">
                              {formatTime(session.start_time)} - {formatTime(session.end_time)}
                            </td>
                            <td>{session.capacity}</td>
                            <td>{session.booked_count || 0}</td>
                            <td>
                              {session.status === 0 ? (
                                <span className="status-badge status-cancelled">停診</span>
                              ) : (
                                <span className="status-badge status-active">正常</span>
                              )}
                            </td>
                            <td className="actions-cell">
                              <div className="action-buttons">
                                <button
                                  className="btn-small btn-secondary"
                                  onClick={() => startEdit(session)}
                                >
                                  編輯
                                </button>
                                {session.status === 1 && (
                                  <button
                                    className="btn-small btn-danger"
                                    onClick={() => handleCancel(session.session_id)}
                                  >
                                    取消
                                  </button>
                                )}
                                <button
                                  className="btn-small btn-primary"
                                  onClick={() => navigate(`/provider/appointments/${session.session_id}`)}
                                >
                                  查看預約
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              };

              return (
                <>
                  {renderSessionTable(active, '正在看診')}
                  {renderSessionTable(upcoming, '未來門診')}
                  {renderSessionTable(cancelled, '已停診')}
                </>
              );
            })()
          )}
        </div>
      </div>
    </Layout>
  );
};

