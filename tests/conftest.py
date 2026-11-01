import pytest
from faker import Faker

from utils.attachments import attach_page_source, attach_screenshot
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
