from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import TextClause
from sqlalchemy.engine import Connection

from app.db import queries as q

Row = Dict[str, Any]


class NaruzhuDb:
    """
    Чтение данных стенда для проверок: пользователи, заявки, ключи, действия, события, серверы.

    Обёртка над запросами из app/db/queries.py: методы возвращают строки как dict
    (одна строка или None, список строк). Только чтение — ничего не меняет.
    В тестах — через фикстуру db (транзакция откатывается после теста).
    """

    DEFAULT_LIMIT = 10

    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def _one(self, query: TextClause, **params: Any) -> Optional[Row]:
        row = self.conn.execute(query, params).mappings().first()
        return dict(row) if row is not None else None

    def _all(self, query: TextClause, **params: Any) -> List[Row]:
        return [dict(r) for r in self.conn.execute(query, params).mappings().all()]

    # ===== users =====

    def users(self, limit: int = DEFAULT_LIMIT) -> List[Row]:
        return self._all(q.USERS, limit=limit)

    def user_by_id(self, user_id: int) -> Optional[Row]:
        return self._one(q.USER_BY_ID, user_id=user_id)

    def user_by_email(self, email: str) -> Optional[Row]:
        return self._one(q.USER_BY_EMAIL, email=email)

    def user_by_public_id(self, public_id: str) -> Optional[Row]:
        return self._one(q.USER_BY_PUBLIC_ID, public_id=public_id)

    def user_by_public_request_id(self, public_request_id: str) -> Optional[Row]:
        return self._one(q.USER_BY_PUBLIC_REQUEST_ID, public_request_id=public_request_id)

    # ===== requests =====

    def requests(self, limit: int = DEFAULT_LIMIT) -> List[Row]:
        return self._all(q.REQUESTS, limit=limit)

    def request_by_db_id(self, db_id: int) -> Optional[Row]:
        return self._one(q.REQUEST_BY_DB_ID, db_id=db_id)

    def request_by_public_id(self, public_request_id: str) -> Optional[Row]:
        return self._one(q.REQUEST_BY_PUBLIC_ID, public_request_id=public_request_id)

    def requests_by_user_id(self, user_id: int) -> List[Row]:
        return self._all(q.REQUESTS_BY_USER_ID, user_id=user_id)

    # ===== amnesia_keys =====

    def keys(self, limit: int = DEFAULT_LIMIT) -> List[Row]:
        return self._all(q.AMNESIA_KEYS, limit=limit)

    def key_by_id(self, key_id: int) -> Optional[Row]:
        return self._one(q.AMNESIA_KEY_BY_ID, key_id=key_id)

    def keys_by_request_id(self, request_id: int) -> List[Row]:
        return self._all(q.AMNESIA_KEYS_BY_REQUEST_ID, request_id=request_id)

    def keys_by_public_request_id(self, public_request_id: str) -> List[Row]:
        return self._all(q.AMNESIA_KEYS_BY_PUBLIC_REQUEST_ID, public_request_id=public_request_id)

    def keys_by_device_id(self, device_id: str) -> List[Row]:
        return self._all(q.AMNESIA_KEYS_BY_DEVICE_ID, device_id=device_id)

    # ===== request_actions / request_events =====

    def request_actions(self, limit: int = DEFAULT_LIMIT) -> List[Row]:
        return self._all(q.REQUEST_ACTIONS, limit=limit)

    def actions_by_request_id(self, request_id: int) -> List[Row]:
        return self._all(q.REQUEST_ACTIONS_BY_REQUEST_ID, request_id=request_id)

    def request_events(self, limit: int = DEFAULT_LIMIT) -> List[Row]:
        return self._all(q.REQUEST_EVENTS, limit=limit)

    def events_by_request_id(self, request_id: int) -> List[Row]:
        return self._all(q.REQUEST_EVENTS_BY_REQUEST_ID, request_id=request_id)

    # ===== wg_servers =====

    def wg_servers(self, limit: int = 100) -> List[Row]:
        return self._all(q.WG_SERVERS, limit=limit)

    def wg_server_by_id(self, server_id: int) -> Optional[Row]:
        return self._one(q.WG_SERVER_BY_ID, server_id=server_id)
