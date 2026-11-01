import allure
import pytest


@pytest.mark.ui
@allure.feature("Android")
@allure.story("Smoke")
@allure.title("App launches and is in foreground")
def test_app_launches(appium_driver, config):
    expected_package = config.appium["app_package"]

    with allure.step(f"Assert current package is {expected_package}"):
        assert appium_driver.current_package == expected_package
