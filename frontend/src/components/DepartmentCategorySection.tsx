// 部門分類區塊組件
import React from 'react';
import { DepartmentGrid } from './DepartmentGrid';
import type { DepartmentForUI } from './DepartmentGrid';
import './DepartmentCategorySection.css';

interface DepartmentCategorySectionProps {
  title: string;
  departments: DepartmentForUI[];
}

export const DepartmentCategorySection: React.FC<DepartmentCategorySectionProps> = ({
  title,
  departments,
}) => {
  return (
    <div className="department-category-section">
      <h2 className="department-category-section-title">{title}</h2>
      <DepartmentGrid departments={departments} />
    </div>
  );
};
