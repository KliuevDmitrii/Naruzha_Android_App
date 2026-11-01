import allure
import pytest

from app.web.pages.base_page import WebBasePage


@pytest.mark.web
@allure.feature("Web")
@allure.story("Smoke")
@allure.title("Web cabinet main page opens")
def test_main_page_opens(web_driver, config):
    page = WebBasePage(web_driver, config.web["base_url"])

    with allure.step("Open main page"):
        page.open()

    with allure.step("Assert page has title"):
        assert page.title, f"Empty <title> at {web_driver.current_url}"
