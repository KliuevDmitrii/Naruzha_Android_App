import allure
import pytest

from app.db import queries


@pytest.mark.db
@allure.feature("DB")
@allure.story("Connection")
@allure.title("PostgreSQL is reachable through SSH tunnel")
def test_db_connection(db_conn):
    result = db_conn.execute(queries.HEALTHCHECK).scalar()
    assert result == 1
