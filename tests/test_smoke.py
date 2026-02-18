from appium import webdriver
from appium.options.android import UiAutomator2Options
import time

def test_session_starts():
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = "Android"
    options.automation_name = "UiAutomator2"
    options.udid = "9b01005930533036340018673718c0"

    # важно:
    options.no_reset = True      # не чистить данные приложения
    options.full_reset = False

    options.app_package = "com.android.settings"
    options.app_activity = ".Settings"

    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
    try:
        time.sleep(5)  # посмотри глазами
        # assert driver.current_package
    finally:
        driver.quit()
