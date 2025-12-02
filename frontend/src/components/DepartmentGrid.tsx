// 部門網格組件
import React from 'react';
import { DepartmentCard } from './DepartmentCard';
import './DepartmentGrid.css';

// 用於 UI 顯示的部門接口（與資料庫的 Department 不同）
export interface DepartmentForUI {
  deptId: number | string;
  name: string;
  slug: string;
  category?: string;
}

interface DepartmentGridProps {
  departments: DepartmentForUI[];
}

export const DepartmentGrid: React.FC<DepartmentGridProps> = ({
  departments,
}) => {
  return (
    <div className="department-grid">
      {departments.map((dept) => (
        <DepartmentCard
          key={dept.deptId}
          deptId={dept.deptId}
          name={dept.name}
          slug={dept.slug}
          category={dept.category}
        />
      ))}
    </div>
  );
};
