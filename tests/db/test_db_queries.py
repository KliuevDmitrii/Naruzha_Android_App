import allure
import pytest

from app.db import queries as q
from testdata import db_data as td


def _columns(columns_sql: str) -> set[str]:
    return {c.strip().strip('"') for c in columns_sql.split(",")}


TABLES = [
    ("users", "users", q.USERS_COLUMNS),
    ("requests", "requests", q.REQUESTS_COLUMNS),
    ("amnesia_keys", "keys", q.AMNESIA_KEYS_COLUMNS),
    ("request_actions", "request_actions", q.REQUEST_ACTIONS_COLUMNS),
    ("request_events", "request_events", q.REQUEST_EVENTS_COLUMNS),
    ("wg_servers", "wg_servers", q.WG_SERVERS_COLUMNS),
]


@pytest.mark.db
@allure.feature("DB")
@allure.story("Schema")
@pytest.mark.parametrize("table,method,columns", TABLES, ids=[t[0] for t in TABLES])
def test_table_has_expected_columns(db, table, method, columns):
    """Запросы из app/db/queries.py выполняются, таблица не пустая, все колонки на месте."""
    allure.dynamic.title(f"{table}: query works and returns expected columns")

    rows = getattr(db, method)(limit=1)

    with allure.step(f"Assert {table} is not empty"):
        assert rows, f"Table public.{table} is empty"

    with allure.step("Assert columns"):
        assert set(rows[0]) == _columns(columns), f"Columns mismatch in {table}: {sorted(rows[0])}"


@pytest.mark.db
@allure.feature("DB")
@allure.story("Integrity")
class TestIntegrity:
    """Ссылочная целостность на последних записях: ключ -> заявка -> пользователь, ключ -> сервер."""

    @allure.title("Latest requests belong to existing users")
    def test_requests_reference_users(self, db):
        for req in db.requests(limit=td.INTEGRITY_SAMPLE):
            if req["user_id"] is None:
                continue
            with allure.step(f"request {req['db_id']} -> user {req['user_id']}"):
                assert db.user_by_id(req["user_id"]), f"Request {req['db_id']}: user {req['user_id']} not found"

    @allure.title("Latest keys belong to existing requests and servers")
    def test_keys_reference_requests_and_servers(self, db):
        for key in db.keys(limit=td.INTEGRITY_SAMPLE):
            with allure.step(f"key {key['id']} -> request {key['request_id']}, server {key['server_id']}"):
                # request_id = NULL — анонимный ключ (download-anonymous-key), заявки нет
                if key["request_id"] is not None:
                    assert db.request_by_db_id(key["request_id"]), f"Key {key['id']}: request not found"
                if key["server_id"] is not None:
                    assert db.wg_server_by_id(key["server_id"]), f"Key {key['id']}: server not found"

    @allure.title("Request statuses are from known set")
    def test_request_statuses_known(self, db):
        statuses = {r["status"] for r in db.requests(limit=td.INTEGRITY_SAMPLE)}
        unknown = statuses - set(td.REQUEST_STATUSES)
        assert not unknown, f"Unknown request statuses: {unknown} (обновите REQUEST_STATUSES в testdata/db_data.py)"

    @allure.title("Servers support known AWG versions")
    def test_wg_servers_awg_versions(self, db):
        for server in db.wg_servers():
            versions = set(server["supported_awg_versions"] or [])
            unknown = versions - set(td.AWG_VERSIONS)
            assert not unknown, f"Server {server['id']} has unknown AWG versions: {unknown}"
