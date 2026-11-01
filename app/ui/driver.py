from __future__ import annotations

from appium import webdriver
from appium.options.android import UiAutomator2Options

from utils.config_provider import ConfigProvider


def create_android_driver(config: ConfigProvider) -> webdriver.Remote:
    cfg = config.appium

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = cfg["device_name"]
    options.udid = cfg["udid"]
    options.app_package = cfg["app_package"]
    options.app_activity = cfg["app_activity"]
    options.no_reset = cfg["no_reset"]   # не чистить данные приложения
    options.full_reset = False

    driver = webdriver.Remote(cfg["appium_url"], options=options)
    driver.implicitly_wait(cfg["implicit_wait"])
    return driver
