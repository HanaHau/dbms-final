// 部門詳情頁面 - 顯示該部門的醫師和會話
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../../components/Layout';
import { DoctorSessionList } from '../../components/DoctorSessionList';
import type { SessionForUI } from '../../components/DoctorSessionList';
import { getDepartmentCategory } from '../../lib/departmentCategory';
import { formatDateWithWeekday } from '../../lib/dateFormat';
import { patientApi } from '../../services/api';
import type { ClinicSession } from '../../types';
import './DepartmentDetail.css';

export const DepartmentDetail: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [department, setDepartment] = useState<{
    dept_id: number;
    name: string;
    location?: string;
  } | null>(null);
  const [sessions, setSessions] = useState<SessionForUI[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) {
      setError('無效的部門連結');
      setLoading(false);
      return;
    }
    loadDepartmentData();
  }, [slug]);

  const loadDepartmentData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 解碼 slug 為部門名稱
      const departmentName = decodeURIComponent(slug!);

      // 獲取部門資訊
      const deptData = await patientApi.getDepartmentByName(departmentName);
      if (!deptData) {
        setError('找不到該部門');
        setLoading(false);
        return;
      }

      setDepartment(deptData);

      // 獲取該部門的會話
      const sessionsData = await patientApi.listSessions({
        dept_id: deptData.dept_id,
      });

      // 轉換為 UI 格式
      const formattedSessions: SessionForUI[] = sessionsData.map(
        (session: ClinicSession) => {
          const date = new Date(session.date + 'T00:00:00');
          const weekdayLabels = [
            '星期日',
            '星期一',
            '星期二',
            '星期三',
            '星期四',
            '星期五',
            '星期六',
          ];
          const weekdayLabel = weekdayLabels[date.getDay()];

          const formatTime = (timeStr: string) => {
            if (!timeStr) return '';
            const time = timeStr.split(':');
            return `${time[0]}:${time[1]}`;
          };

          return {
            sessionId: session.session_id,
            doctorName: session.provider_name || '醫師',
            date: session.date,
            weekdayLabel,
            startTime: formatTime(session.start_time),
            endTime: formatTime(session.end_time),
            capacity: session.capacity,
            remaining: session.capacity - (session.booked_count || 0),
          };
        }
      );

      // 過濾未來日期並排序
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const futureSessions = formattedSessions
        .filter((s) => {
          const sessionDate = new Date(s.date + 'T00:00:00');
          return sessionDate >= today;
        })
        .sort((a, b) => {
          if (a.date !== b.date) {
            return a.date.localeCompare(b.date);
          }
          return a.startTime.localeCompare(b.startTime);
        });

      setSessions(futureSessions);
    } catch (err: any) {
      console.error('載入部門資料失敗:', err);
      setError('載入部門資料失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  // 按日期分組
  const groupedByDate: Record<string, SessionForUI[]> = {};
  sessions.forEach((session) => {
    if (!groupedByDate[session.date]) {
      groupedByDate[session.date] = [];
    }
    groupedByDate[session.date].push(session);
  });

  // 按日期排序
  const sortedDates = Object.keys(groupedByDate).sort((a, b) =>
    a.localeCompare(b)
  );

  if (loading) {
    return (
      <Layout>
        <div className="department-detail-page">
          <div className="department-detail-loading">載入中...</div>
        </div>
      </Layout>
    );
  }

  if (error || !department) {
    return (
      <Layout>
        <div className="department-detail-page">
          <div className="department-detail-error">
            {error || '找不到該部門'}
          </div>
          <button
            className="btn btn-secondary"
            onClick={() => navigate('/departments')}
          >
            返回部門列表
          </button>
        </div>
      </Layout>
    );
  }

  const categoryLabel = getDepartmentCategory(department.name);

  return (
    <Layout>
      <div className="department-detail-page">
        <h1 className="department-detail-title">{department.name}</h1>
        <p className="department-detail-subtitle">{categoryLabel} 門診</p>

        {sortedDates.length === 0 ? (
          <p className="department-detail-empty">
            目前沒有可預約門診。
          </p>
        ) : (
          sortedDates.map((dateKey) => (
            <section key={dateKey} className="department-detail-section">
              <h2 className="department-detail-section-title">
                {formatDateWithWeekday(dateKey)}
              </h2>
              <div className="department-detail-sessions">
                {groupedByDate[dateKey].map((session) => (
                  <DoctorSessionList 
                    key={session.sessionId} 
                    session={session}
                    onAppointmentSuccess={() => {
                      // 重新載入數據
                      loadDepartmentData();
                    }}
                  />
                ))}
              </div>
            </section>
          ))
        )}
      </div>
    </Layout>
  );
};
