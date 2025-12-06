// 部門首頁 - 顯示所有科別
import React, { useState, useEffect } from 'react';
import { Layout } from '../../components/Layout';
import { DepartmentSearchWrapper } from '../../components/DepartmentSearchWrapper';
import { slugifyChinese } from '../../lib/slugify';
import type { DepartmentForUI } from '../../components/DepartmentGrid';
import { patientApi } from '../../services/api';
import './Departments.css';

export const Departments: React.FC = () => {
  const [departments, setDepartments] = useState<DepartmentForUI[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDepartments();
  }, []);

  const loadDepartments = async () => {
    try {
      setLoading(true);
      setError(null);

      // 從 API 獲取部門列表
      const data = await patientApi.listDepartments();
      
      // 如果 API 返回空陣列或無效數據
      if (!data || !Array.isArray(data) || data.length === 0) {
        setError('目前沒有可用的科別');
        setDepartments([]);
        return;
      }

      // 使用資料庫的分類資訊
      const mappedDepartments: DepartmentForUI[] = data.map((dept: any) => ({
        deptId: dept.dept_id,
        name: dept.name,
        slug: slugifyChinese(dept.name),
        category: dept.category_name || '未分類',
      }));
      setDepartments(mappedDepartments);
    } catch (err: any) {
      console.error('載入部門失敗:', err);
      setError('載入部門列表失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="departments-page">
          <div className="departments-loading">載入中...</div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="departments-page">
          <div className="departments-error">{error}</div>
        </div>
      </Layout>
    );
  }

  console.log('渲染部門頁面，部門數量:', departments.length);

  return (
    <Layout>
      <div className="departments-page">
        <h1 className="departments-title">可預約門診</h1>
        <p className="departments-subtitle">請先選擇欲預約的科別。</p>
        {departments.length === 0 ? (
          <div className="departments-empty">
            <p>目前沒有可用的科別</p>
          </div>
        ) : (
          <DepartmentSearchWrapper departments={departments} />
        )}
      </div>
    </Layout>
  );
};
