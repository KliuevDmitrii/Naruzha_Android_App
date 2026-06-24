from sqlalchemy import text


def test_db_connection(db_conn):
    result = db_conn.execute(text("select 1")).scalar()
    assert result == 1