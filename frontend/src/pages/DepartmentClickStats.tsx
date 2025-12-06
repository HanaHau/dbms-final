// 科別點擊統計頁面
import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { departmentClickLogger, type DepartmentClickRecord } from '../lib/departmentClickLogger';
import './DepartmentClickStats.css';

interface DepartmentStats {
  deptId: number | string;
  deptName: string;
  count: number;
}

interface UserStats {
  userId: number | null;
  userName: string | null;
  userType: string | null;
  count: number;
}

interface DateStats {
  date: string;
  count: number;
}

export const DepartmentClickStats: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [totalClicks, setTotalClicks] = useState(0);
  const [departmentStats, setDepartmentStats] = useState<DepartmentStats[]>([]);
  const [userStats, setUserStats] = useState<UserStats[]>([]);
  const [dateStats, setDateStats] = useState<DateStats[]>([]);
  const [recentClicks, setRecentClicks] = useState<DepartmentClickRecord[]>([]);

  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      setLoading(true);
      const allClicks = await departmentClickLogger.getAllClicks();

      // 總點擊數
      setTotalClicks(allClicks.length);

      // 按科別統計
      const deptMap = new Map<number | string, { name: string; count: number }>();
      allClicks.forEach((click) => {
        const existing = deptMap.get(click.deptId) || { name: click.deptName, count: 0 };
        deptMap.set(click.deptId, {
          name: existing.name,
          count: existing.count + 1,
        });
      });
      const deptStats: DepartmentStats[] = Array.from(deptMap.entries())
        .map(([deptId, data]) => ({
          deptId,
          deptName: data.name,
          count: data.count,
        }))
        .sort((a, b) => b.count - a.count);
      setDepartmentStats(deptStats);

      // 按使用者統計
      const userMap = new Map<string, { userId: number | null; userName: string | null; userType: string | null; count: number }>();
      allClicks.forEach((click) => {
        const key = click.userId !== null ? `${click.userType}-${click.userId}` : 'anonymous';
        const existing = userMap.get(key) || {
          userId: click.userId,
          userName: click.userName,
          userType: click.userType,
          count: 0,
        };
        userMap.set(key, {
          ...existing,
          count: existing.count + 1,
        });
      });
      const usrStats: UserStats[] = Array.from(userMap.values())
        .map((data) => ({
          userId: data.userId,
          userName: data.userName || '匿名使用者',
          userType: data.userType || '未登入',
          count: data.count,
        }))
        .sort((a, b) => b.count - a.count);
      setUserStats(usrStats);

      // 按日期統計
      const dateMap = new Map<string, number>();
      allClicks.forEach((click) => {
        const existing = dateMap.get(click.date) || 0;
        dateMap.set(click.date, existing + 1);
      });
      const dtStats: DateStats[] = Array.from(dateMap.entries())
        .map(([date, count]) => ({ date, count }))
        .sort((a, b) => b.date.localeCompare(a.date))
        .slice(0, 30); // 只顯示最近 30 天
      setDateStats(dtStats);

      // 最近的點擊記錄
      const recent = [...allClicks]
        .sort((a, b) => b.timestamp - a.timestamp)
        .slice(0, 20); // 顯示最近 20 筆
      setRecentClicks(recent);
    } catch (error) {
      console.error('載入統計資料失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return `${date.toLocaleDateString('zh-TW')} ${date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`;
  };

  if (loading) {
    return (
      <Layout>
        <div className="stats-page">
          <div className="stats-loading">載入統計資料中...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="stats-page">
        <h1 className="stats-title">科別點擊統計</h1>

        {/* 總覽卡片 */}
        <div className="stats-overview">
          <div className="stat-card">
            <div className="stat-value">{totalClicks}</div>
            <div className="stat-label">總點擊數</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{departmentStats.length}</div>
            <div className="stat-label">科別數</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{userStats.length}</div>
            <div className="stat-label">使用者數</div>
          </div>
        </div>

        {/* 科別點擊排行 */}
        <section className="stats-section">
          <h2 className="stats-section-title">科別點擊排行</h2>
          {departmentStats.length === 0 ? (
            <p className="stats-empty">尚無點擊記錄</p>
          ) : (
            <div className="stats-table-container">
              <table className="stats-table">
                <thead>
                  <tr>
                    <th>排名</th>
                    <th>科別名稱</th>
                    <th>點擊次數</th>
                    <th>佔比</th>
                  </tr>
                </thead>
                <tbody>
                  {departmentStats.map((dept, index) => (
                    <tr key={dept.deptId}>
                      <td>{index + 1}</td>
                      <td>{dept.deptName}</td>
                      <td>{dept.count}</td>
                      <td>{totalClicks > 0 ? ((dept.count / totalClicks) * 100).toFixed(2) : 0}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* 使用者點擊統計 */}
        <section className="stats-section">
          <h2 className="stats-section-title">使用者點擊統計</h2>
          {userStats.length === 0 ? (
            <p className="stats-empty">尚無點擊記錄</p>
          ) : (
            <div className="stats-table-container">
              <table className="stats-table">
                <thead>
                  <tr>
                    <th>使用者名稱</th>
                    <th>使用者類型</th>
                    <th>點擊次數</th>
                    <th>佔比</th>
                  </tr>
                </thead>
                <tbody>
                  {userStats.map((user, index) => (
                    <tr key={index}>
                      <td>{user.userName}</td>
                      <td>
                        {user.userType === 'patient' ? '病患' : user.userType === 'provider' ? '醫師' : user.userType}
                      </td>
                      <td>{user.count}</td>
                      <td>{totalClicks > 0 ? ((user.count / totalClicks) * 100).toFixed(2) : 0}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* 日期分布 */}
        <section className="stats-section">
          <h2 className="stats-section-title">日期點擊分布（最近 30 天）</h2>
          {dateStats.length === 0 ? (
            <p className="stats-empty">尚無點擊記錄</p>
          ) : (
            <div className="stats-table-container">
              <table className="stats-table">
                <thead>
                  <tr>
                    <th>日期</th>
                    <th>點擊次數</th>
                  </tr>
                </thead>
                <tbody>
                  {dateStats.map((dateStat) => (
                    <tr key={dateStat.date}>
                      <td>{new Date(dateStat.date).toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })}</td>
                      <td>{dateStat.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* 最近點擊記錄 */}
        <section className="stats-section">
          <h2 className="stats-section-title">最近點擊記錄</h2>
          {recentClicks.length === 0 ? (
            <p className="stats-empty">尚無點擊記錄</p>
          ) : (
            <div className="stats-table-container">
              <table className="stats-table">
                <thead>
                  <tr>
                    <th>時間</th>
                    <th>使用者</th>
                    <th>科別</th>
                    <th>分類</th>
                  </tr>
                </thead>
                <tbody>
                  {recentClicks.map((click) => (
                    <tr key={click.id}>
                      <td>{formatDateTime(click.timestamp)}</td>
                      <td>
                        {click.userName || '匿名使用者'}
                        {click.userType && ` (${click.userType === 'patient' ? '病患' : '醫師'})`}
                      </td>
                      <td>{click.deptName}</td>
                      <td>{click.category || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </Layout>
  );
};

