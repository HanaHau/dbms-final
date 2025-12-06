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

  // 分類順序：從資料庫獲取，如果沒有則使用預設順序
  // 注意：這裡的分類順序應該從 API 獲取，但目前先使用動態排序
  // 按分類出現的順序排列（保持資料庫的順序）
  const categoryOrder = useMemo(() => {
    const categories = new Set<string>();
    filteredDepartments.forEach((dept) => {
      if (dept.category) {
        categories.add(dept.category);
      }
    });
    // 將未分類放在最後
    const sorted = Array.from(categories).sort((a, b) => {
      if (a === '未分類') return 1;
      if (b === '未分類') return -1;
      return a.localeCompare(b, 'zh-TW');
    });
    return sorted;
  }, [filteredDepartments]);

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
