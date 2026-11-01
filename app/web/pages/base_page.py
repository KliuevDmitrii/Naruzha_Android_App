from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

from app.base_page import BasePage


class WebBasePage(BasePage):
    path = "/"

    def __init__(self, driver: WebDriver, base_url: str, timeout: float = 10) -> None:
        super().__init__(driver, timeout)
        self.base_url = base_url

    def open(self) -> "WebBasePage":
        self.driver.get(f"{self.base_url}{self.path}")
        return self

    @property
    def title(self) -> str:
        return self.driver.title
