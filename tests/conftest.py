import pytest
from faker import Faker

from utils.config_provider import ConfigProvider
from utils.data_provider import DataProvider
from app.api.client import NaruzhuApi
from app.db.client import DbClient


@pytest.fixture(scope="session")
def config() -> ConfigProvider:
    return ConfigProvider()


@pytest.fixture(scope="session")
def data() -> DataProvider:
    return DataProvider()


@pytest.fixture(scope="session")
def api(config: ConfigProvider) -> NaruzhuApi:
    return NaruzhuApi(config)


@pytest.fixture()
def faker() -> Faker:
    return Faker()


@pytest.fixture(scope="session")
def db_engine():
    client = DbClient()
    engine = client.connect()
    try:
        yield engine
    finally:
        client.close()


@pytest.fixture(scope="function")
def db_conn(db_engine):
    conn = db_engine.connect()
    tx = conn.begin()
    try:
        yield conn
    finally:
        tx.rollback()
        conn.close()