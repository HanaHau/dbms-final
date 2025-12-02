// 部門卡片組件
import React from 'react';
import { Link } from 'react-router-dom';
import './DepartmentCard.css';

interface DepartmentCardProps {
  deptId: number | string;
  name: string;
  slug: string;
  category?: string;
}

export const DepartmentCard: React.FC<DepartmentCardProps> = ({
  name,
  slug,
  category,
}) => {
  return (
    <Link to={`/departments/${slug}`} className="department-card">
      <div className="department-card-name">{name}</div>
      {category && (
        <div className="department-card-category">{category}</div>
      )}
    </Link>
  );
};
