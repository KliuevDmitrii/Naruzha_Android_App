import uuid

import pytest
from faker import Faker

from utils.attachments import attach_page_source, attach_screenshot
from utils.config_provider import ConfigProvider
from utils.data_provider import DataProvider
from app.api.client import NaruzhuApi
from app.db.client import DbClient
from app.db.repository import NaruzhuDb
from tests.helpers.accounts import Account, register_account


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


# ===== Тестовый аккаунт =====
# Источник 1: testdata/test_data.local.json (постоянный аккаунт).
# Источник 2 (если в json пусто): registered_account — новый пользователь,
# зарегистрированный через API с OTP из БД. Один на прогон; на ENV=prod не создаётся.

@pytest.fixture(scope="session")
def registered_account(config: ConfigProvider, api: NaruzhuApi, db_engine) -> Account:
    if config.env == "prod":
        pytest.skip("registered_account is not created on ENV=prod")
    with db_engine.connect() as conn:
        return register_account(api, NaruzhuDb(conn), email=Faker().email())


def _account_value(request: pytest.FixtureRequest, key: str, account_attr: str) -> str:
    value = request.getfixturevalue("data").get(f"test_account.{key}")
    if value:
        return str(value)
    try:
        account = request.getfixturevalue("registered_account")
    except Exception as e:  # нет SSH/DB в config/.env или туннель не поднялся (pytest.skip сюда не попадает)
        pytest.skip(f"test_account.{key} is not set and registered_account is unavailable: {e}")
    return getattr(account, account_attr)


@pytest.fixture()
def account_email(request) -> str:
    return _account_value(request, "email", "email")


@pytest.fixture()
def account_otp(request) -> str:
    return _account_value(request, "otp", "otp")


@pytest.fixture()
def public_request_id(request) -> str:
    return _account_value(request, "public_request_id", "public_request_id")


@pytest.fixture()
def public_user_id(request) -> str:
    return _account_value(request, "public_user_id", "public_user_id")


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
