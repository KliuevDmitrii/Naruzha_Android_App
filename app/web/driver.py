from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from utils.config_provider import ConfigProvider


def create_web_driver(config: ConfigProvider) -> WebDriver:
    cfg = config.web
    browser = cfg["browser"]

    if browser == "chrome":
        options = webdriver.ChromeOptions()
        if cfg["headless"]:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        return webdriver.Chrome(options=options)

    if browser == "firefox":
        options = webdriver.FirefoxOptions()
        if cfg["headless"]:
            options.add_argument("-headless")
        driver = webdriver.Firefox(options=options)
        driver.set_window_size(1920, 1080)
        return driver

    raise ValueError(f"Unsupported WEB_BROWSER: {browser}")
