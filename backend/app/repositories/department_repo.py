# repositories/department_repo.py
from typing import List, Dict
from ..pg_base import get_pg_conn


class DepartmentRepository:
    """部門資料存取層"""

    def list_all_departments(self) -> List[Dict]:
        """
        列出所有部門。
        回傳格式：
        [
          { "dept_id": 1, "name": "內科", "location": "..." },
          ...
        ]
        """
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT dept_id, name, location
                    FROM DEPARTMENT
                    ORDER BY dept_id
                    """
                )
                rows = cur.fetchall()
                return [
                    {
                        "dept_id": row[0],
                        "name": row[1],
                        "location": row[2],
                    }
                    for row in rows
                ]
        finally:
            conn.close()

    def get_department_by_name(self, name: str) -> Dict | None:
        """
        根據部門名稱取得部門資訊。
        回傳格式：
        { "dept_id": 1, "name": "內科", "location": "..." }
        如果找不到則回傳 None。
        """
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT dept_id, name, location
                    FROM DEPARTMENT
                    WHERE name = %s
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
                }
        finally:
            conn.close()
