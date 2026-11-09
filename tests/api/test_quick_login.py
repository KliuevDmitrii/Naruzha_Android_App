import re
from datetime import datetime, timedelta, timezone

import allure
import pytest

from app.api.endpoints import Endpoints
from testdata import api_data as td
from tests.helpers.api_asserts import assert_api_error, assert_ok_data


@pytest.mark.api
@allure.feature("API")
@allure.story("Quick Login (TV)")
class TestQuickLogin:
    """Флоу быстрого входа: create (ТВ) -> confirm (телефон) -> check (ТВ)."""

    @allure.title("create-quick-login returns code and expiration")
    def test_create_quick_login_returns_code(self, api_new_device):
        data = assert_ok_data(api_new_device.create_quick_login())
        ql = data["quick_login"]

        with allure.step(f"Assert code matches {td.QUICK_LOGIN_CODE_PATTERN}"):
            assert re.match(td.QUICK_LOGIN_CODE_PATTERN, ql["quick_login_code"]), f"Bad code: {ql}"

        with allure.step(f"Assert expires in ~{td.QUICK_LOGIN_TTL_MINUTES} min"):
            expires = datetime.fromisoformat(ql["expires_at_datetime"])
            left = expires - datetime.now(timezone.utc)
            assert timedelta(0) < left <= timedelta(minutes=td.QUICK_LOGIN_TTL_MINUTES + 1), f"TTL {left}: {ql}"

    @allure.title("create-quick-login without X-Device-Id gets device_id error")
    def test_create_quick_login_without_device(self, api_without_device):
        assert_api_error(api_without_device.create_quick_login(), 400, "device_id")

    @allure.title("Fresh code is not confirmed yet: request is null")
    def test_check_quick_login_not_confirmed(self, api_new_device):
        code = assert_ok_data(api_new_device.create_quick_login())["quick_login"]["quick_login_code"]
        data = assert_ok_data(api_new_device.check_quick_login(code))

        with allure.step("Assert data.request is null"):
            assert data == {"request": None}, f"Unexpected data: {data}"

    @allure.title("Code is bound to device: other device gets quick_login_not_found")
    def test_check_quick_login_other_device(self, api_new_device, api):
        code = assert_ok_data(api_new_device.create_quick_login())["quick_login"]["quick_login_code"]
        assert_api_error(api.check_quick_login(code), 404, "quick_login_not_found")

    @allure.title("New code invalidates previous code of the same device")
    def test_create_quick_login_replaces_old_code(self, api_new_device):
        old = assert_ok_data(api_new_device.create_quick_login())["quick_login"]["quick_login_code"]
        new = assert_ok_data(api_new_device.create_quick_login())["quick_login"]["quick_login_code"]

        assert_ok_data(api_new_device.check_quick_login(new))
        assert_api_error(api_new_device.check_quick_login(old), 404, "quick_login_not_found")

    @allure.title("check-quick-login with unknown code gets quick_login_not_found")
    def test_check_quick_login_unknown_code(self, api_new_device):
        r = api_new_device.check_quick_login(td.NONEXISTENT_QUICK_LOGIN_CODE)
        assert_api_error(r, 404, "quick_login_not_found")

    @allure.title("check-quick-login without code gets invalid_parameters")
    def test_check_quick_login_without_code(self, api_new_device):
        r = api_new_device.request("POST", Endpoints.CHECK_QUICK_LOGIN, json={})
        assert_api_error(r, 400, "invalid_parameters")

    @allure.title("confirm-quick-login with unknown code gets quick_login_not_found")
    def test_confirm_quick_login_unknown_code(self, api):
        r = api.confirm_quick_login(td.NONEXISTENT_ID, td.NONEXISTENT_QUICK_LOGIN_CODE)
        assert_api_error(r, 404, "quick_login_not_found")

    @pytest.mark.mutating
    @allure.title("Full flow: create -> confirm -> check returns request")
    def test_quick_login_full_flow(self, api_new_device, api, public_request_id):
        with allure.step("TV: create code"):
            code = assert_ok_data(api_new_device.create_quick_login())["quick_login"]["quick_login_code"]

        with allure.step("Phone: confirm code with account request"):
            assert_ok_data(api.confirm_quick_login(public_request_id, code))

        with allure.step("TV: check code"):
            data = assert_ok_data(api_new_device.check_quick_login(code))

        with allure.step("Assert TV received account public_request_id"):
            assert data["request"]["public_request_id"] == public_request_id, f"Unexpected request: {data}"
