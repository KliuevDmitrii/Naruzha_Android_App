from __future__ import annotations

import allure


def attach_text(name: str, value: str) -> None:
    allure.attach(value, name=name, attachment_type=allure.attachment_type.TEXT)


def attach_json(name: str, value: str) -> None:
    allure.attach(value, name=name, attachment_type=allure.attachment_type.JSON)


def attach_screenshot(driver, name: str = "Screenshot") -> None:
    """Скриншот из Appium/Selenium драйвера. Ошибки не роняют тест."""
    try:
        allure.attach(driver.get_screenshot_as_png(), name=name, attachment_type=allure.attachment_type.PNG)
    except Exception:
        pass


def attach_page_source(driver, name: str = "Page source") -> None:
    try:
        allure.attach(driver.page_source, name=name, attachment_type=allure.attachment_type.XML)
    except Exception:
        pass
