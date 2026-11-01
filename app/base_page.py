from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from utils.waits import Locator, is_visible, wait_clickable, wait_visible


class BasePage:
    """Общая база Page Object для Appium (app/ui) и Web (app/web)."""

    def __init__(self, driver: WebDriver, timeout: float = 15) -> None:
        self.driver = driver
        self.timeout = timeout

    def find(self, locator: Locator) -> WebElement:
        return wait_visible(self.driver, locator, self.timeout)

    def tap(self, locator: Locator) -> None:
        wait_clickable(self.driver, locator, self.timeout).click()

    def type(self, locator: Locator, text: str) -> None:
        el = self.find(locator)
        el.clear()
        el.send_keys(text)

    def text_of(self, locator: Locator) -> str:
        return self.find(locator).text

    def is_displayed(self, locator: Locator, timeout: float = 2) -> bool:
        return is_visible(self.driver, locator, timeout)

    def back(self) -> None:
        self.driver.back()
