# repositories/department_repo.py
from typing import List, Dict, Optional
from ..pg_base import get_pg_conn


class DepartmentRepository:
    """部門資料存取層"""

    def list_all_departments(self) -> List[Dict]:
        """
        列出所有部門，包含分類資訊。
        回傳格式：
        [
          { 
            "dept_id": 1, 
            "name": "內科", 
            "location": "...",
            "category_id": 1,
            "category_name": "內科系"
          },
          ...
        ]
        """
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        d.dept_id, 
                        d.name, 
                        d.location,
                        d.category_id,
                        dc.name AS category_name
                    FROM DEPARTMENT d
                    LEFT JOIN DEPARTMENT_CATEGORY dc ON d.category_id = dc.category_id
                    ORDER BY 
                        COALESCE(dc.category_id, 999999),
                        d.dept_id
                    """
                )
                rows = cur.fetchall()
                return [
                    {
                        "dept_id": row[0],
                        "name": row[1],
                        "location": row[2],
                        "category_id": row[3],
                        "category_name": row[4],
                    }
                    for row in rows
                ]
        finally:
            conn.close()

    def list_all_categories(self) -> List[Dict]:
        """
        列出所有分類。
        回傳格式：
        [
          { "category_id": 1, "name": "內科系" },
          ...
        ]
        """
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT category_id, name
                    FROM DEPARTMENT_CATEGORY
                    ORDER BY category_id
                    """
                )
                rows = cur.fetchall()
                return [
                    {
                        "category_id": row[0],
                        "name": row[1],
                    }
                    for row in rows
                ]
        finally:
            conn.close()

    def get_department_by_name(self, name: str) -> Dict | None:
        """
        根據部門名稱取得部門資訊，包含分類資訊。
        回傳格式：
        { 
            "dept_id": 1, 
            "name": "內科", 
            "location": "...",
            "category_id": 1,
            "category_name": "內科系"
        }
        如果找不到則回傳 None。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        d.dept_id, 
                        d.name, 
                        d.location,
                        d.category_id,
                        dc.name AS category_name
                    FROM DEPARTMENT d
                    LEFT JOIN DEPARTMENT_CATEGORY dc ON d.category_id = dc.category_id
                    WHERE d.name = %s
                    """,
                    (name,),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                return {
                    "dept_id": row[0],
                    "name": row[1],
                    "location": row[2],
                    "category_id": row[3],
                    "category_name": row[4],
                }
        finally:
            conn.close()
