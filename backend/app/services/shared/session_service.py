# services/shared/session_service.py
from typing import Optional
from datetime import date
from fastapi import HTTPException

from ...repositories import SessionRepository


class SessionService:
    """共享的 Session 服務，提供通用的門診時段查詢功能"""

    def __init__(self):
        self.session_repo = SessionRepository()

    def get_session_by_id(self, session_id: int):
        """
        根據 session_id 取得門診時段資訊，包含 provider 和 department 資訊。
        """
        session = self.session_repo.get_session_by_id(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

    def get_booked_count(self, session_id: int) -> int:
        """
        取得某個門診時段的已預約數量。
        """
        count = self.session_repo.get_booked_count(session_id)
        if count is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return count

    def get_remaining_capacity(self, session_id: int) -> Optional[int]:
        """
        取得某個門診時段的剩餘容量。
        回傳：capacity - booked_count，如果 session 不存在則回傳 None。
        """
        remaining = self.session_repo.get_remaining_capacity(session_id)
        if remaining is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return remaining

    def search_sessions(
        self,
        dept_id: Optional[int] = None,
        provider_id: Optional[int] = None,
        date_: Optional[date] = None,
    ):
        """
        搜尋門診時段，可根據科別、醫師、日期過濾。
        回傳每個 session 的資訊，包含 provider 和 department 資訊，以及已預約人數。
        """
        return self.session_repo.search_sessions(
            dept_id=dept_id,
            provider_id=provider_id,
            date_=date_,
        )

