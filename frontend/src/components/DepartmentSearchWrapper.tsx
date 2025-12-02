// 部門搜尋包裝組件
import React, { useState, useMemo } from 'react';
import { DepartmentCategorySection } from './DepartmentCategorySection';
import { SearchBar } from './SearchBar';
import type { DepartmentForUI } from './DepartmentGrid';
import './DepartmentSearchWrapper.css';

interface DepartmentSearchWrapperProps {
  departments: DepartmentForUI[];
}

export const DepartmentSearchWrapper: React.FC<DepartmentSearchWrapperProps> = ({
  departments,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  // 過濾部門（不區分大小寫，支援中文）
  const filteredDepartments = useMemo(() => {
    if (!searchQuery.trim()) {
      return departments;
    }
    const query = searchQuery.trim().toLowerCase();
    return departments.filter((dept) =>
      dept.name.toLowerCase().includes(query)
    );
  }, [departments, searchQuery]);

  // 按分類分組
  const groupedByCategory = useMemo(() => {
    const grouped: Record<string, DepartmentForUI[]> = {};
    filteredDepartments.forEach((dept) => {
      const category = dept.category || '未分類';
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(dept);
    });
    return grouped;
  }, [filteredDepartments]);

  // 分類順序（確保顯示順序一致）
  const categoryOrder = [
    '內科系',
    '外科系',
    '婦幼科',
    '五官科',
    '精神科',
    '牙科',
    '復健科',
    '其他',
    '未分類',
  ];

  return (
    <div className="department-search-wrapper">
      <div className="department-search-bar-container">
        <SearchBar value={searchQuery} onChange={setSearchQuery} />
      </div>

      {searchQuery.trim() ? (
        // 搜尋模式：顯示單一「搜尋結果」區塊
        <div className="department-search-results">
          {filteredDepartments.length > 0 ? (
            <DepartmentCategorySection
              title="搜尋結果"
              departments={filteredDepartments}
            />
          ) : (
            <div className="department-search-empty">
              <p>找不到符合「{searchQuery}」的科別</p>
            </div>
          )}
        </div>
      ) : (
        // 正常模式：按分類顯示
        <div className="department-categories">
          {categoryOrder.map((category) => {
            const depts = groupedByCategory[category];
            if (!depts || depts.length === 0) return null;
            return (
              <DepartmentCategorySection
                key={category}
                title={category}
                departments={depts}
              />
            );
          })}
        </div>
      )}
    </div>
  );
};
