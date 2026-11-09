import uuid

import pytest
from faker import Faker

from utils.attachments import attach_page_source, attach_screenshot
from utils.config_provider import ConfigProvider
from utils.data_provider import DataProvider
from app.api.client import NaruzhuApi
from app.db.client import DbClient
from app.db.repository import NaruzhuDb


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
def api_new_device(config: ConfigProvider) -> NaruzhuApi:
    """Клиент с уникальным X-Device-Id — "новое устройство" (например, ТВ в quick login)."""
    return NaruzhuApi(config, device_id=f"qa-autotest-{uuid.uuid4().hex[:12]}")


@pytest.fixture()
def api_without_device(config: ConfigProvider) -> NaruzhuApi:
    """Клиент без заголовка X-Device-Id."""
    return NaruzhuApi(config, device_id="")


@pytest.fixture()
def faker() -> Faker:
    return Faker()


# ===== Тестовый аккаунт (testdata/test_data.local.json) =====

def _account_value(data: DataProvider, key: str) -> str:
    value = data.get(f"test_account.{key}")
    if not value:
        pytest.skip(f"test_account.{key} is not set in testdata/test_data.local.json")
    return str(value)


@pytest.fixture()
def account_email(data: DataProvider) -> str:
    return _account_value(data, "email")


@pytest.fixture()
def account_otp(data: DataProvider) -> str:
    return _account_value(data, "otp")


@pytest.fixture()
def public_request_id(data: DataProvider) -> str:
    return _account_value(data, "public_request_id")


@pytest.fixture()
def public_user_id(data: DataProvider) -> str:
    return _account_value(data, "public_user_id")


@pytest.fixture(scope="session")
def active_plan_id(api: NaruzhuApi) -> int:
    """id первого активного тарифа из get-plans — чтобы не хардкодить тарифы стенда."""
    r = api.get_plans()
    plans = (r.json or {}).get("data", {}).get("active_plans") if r.status_code == 200 else None
    if not plans:
        pytest.skip(f"get-plans returned no active plans: {r.status_code} {r.text[:200]}")
    return plans[0]["id"]


# ===== Защита prod от тестов, меняющих данные =====

def pytest_collection_modifyitems(config, items):
    if ConfigProvider().env != "prod":
        return
    skip_prod = pytest.mark.skip(reason="mutating test is not allowed on ENV=prod")
    for item in items:
        if item.get_closest_marker("mutating"):
            item.add_marker(skip_prod)


# ===== DB =====

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


@pytest.fixture(scope="function")
def db(db_conn) -> NaruzhuDb:
    """Чтение данных стенда (users, requests, amnesia_keys, ...) через NaruzhuDb."""
    return NaruzhuDb(db_conn)


# ===== Appium =====

@pytest.fixture(scope="session")
def appium_driver(config: ConfigProvider):
    from app.ui.driver import create_android_driver

    driver = create_android_driver(config)
    try:
        yield driver
    finally:
        driver.quit()


# ===== Web =====

@pytest.fixture(scope="session")
def web_driver(config: ConfigProvider):
    if not config.get("WEB_BASE_URL"):
        pytest.skip("WEB_BASE_URL is not set in config/.env")

    from app.web.driver import create_web_driver

    driver = create_web_driver(config)
    try:
        yield driver
    finally:
        driver.quit()


# ===== Allure: скриншот при падении UI/Web теста =====

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return

    for name in ("appium_driver", "web_driver"):
        driver = item.funcargs.get(name)
        if driver is not None:
            attach_screenshot(driver, name=f"{name} screenshot")
            attach_page_source(driver, name=f"{name} page source")
