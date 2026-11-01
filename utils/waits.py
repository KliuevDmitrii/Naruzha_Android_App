from __future__ import annotations

from typing import Tuple

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

Locator = Tuple[str, str]


def wait_visible(driver: WebDriver, locator: Locator, timeout: float) -> WebElement:
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located(locator),
        message=f"Element not visible after {timeout}s: {locator}",
    )


def wait_clickable(driver: WebDriver, locator: Locator, timeout: float) -> WebElement:
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(locator),
        message=f"Element not clickable after {timeout}s: {locator}",
    )


def wait_invisible(driver: WebDriver, locator: Locator, timeout: float) -> bool:
    return WebDriverWait(driver, timeout).until(
        EC.invisibility_of_element_located(locator),
        message=f"Element still visible after {timeout}s: {locator}",
    )


def is_visible(driver: WebDriver, locator: Locator, timeout: float = 2) -> bool:
    try:
        wait_visible(driver, locator, timeout)
        return True
    except Exception:
        return False
