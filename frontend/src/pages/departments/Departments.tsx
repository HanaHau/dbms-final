// 部門首頁 - 顯示所有科別
import React, { useState, useEffect } from 'react';
import { Layout } from '../../components/Layout';
import { DepartmentSearchWrapper } from '../../components/DepartmentSearchWrapper';
import { getDepartmentCategory } from '../../lib/departmentCategory';
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

      // 預設部門列表（如果 API 不存在時使用）
      const defaultDepartmentNames = [
        '泌尿科',
        '眼科',
        '兒科',
        '骨科',
        '整形外科',
        '復健科',
        '腎臟內科',
        '皮膚科',
        '神經科',
        '胃腸肝膽科',
        '婦產科',
        '家庭醫學科',
        '急診醫學科',
        '耳鼻喉科',
        '牙科',
        '精神科',
        '內科',
        '胸腔內科',
        '外科',
        '心臟內科',
      ];

      // 嘗試從 API 獲取部門列表
      try {
        const data = await patientApi.listDepartments();
        console.log('API 返回的部門數據:', data);
        
        // 如果 API 返回空陣列或無效數據，使用預設列表
        if (!data || !Array.isArray(data) || data.length === 0) {
          console.warn('API 返回空數據，使用預設列表');
          throw new Error('API returned empty or invalid data');
        }

        const mappedDepartments: DepartmentForUI[] = data.map((dept: any) => ({
          deptId: dept.dept_id,
          name: dept.name,
          slug: slugifyChinese(dept.name),
          category: getDepartmentCategory(dept.name),
        }));
        console.log('映射後的部門列表:', mappedDepartments);
        setDepartments(mappedDepartments);
      } catch (apiError) {
        // 如果 API 不存在或失敗，使用硬編碼的部門列表
        console.warn('無法從 API 獲取部門列表，使用預設列表', apiError);
        const defaultDepartments: DepartmentForUI[] = defaultDepartmentNames.map(
          (name, index) => ({
            deptId: index + 1,
            name,
            slug: slugifyChinese(name),
            category: getDepartmentCategory(name),
          })
        );
        console.log('使用預設部門列表:', defaultDepartments);
        setDepartments(defaultDepartments);
      }
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
