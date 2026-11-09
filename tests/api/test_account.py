import allure
import pytest

from testdata import api_data as td
from tests.helpers.api_asserts import assert_ok_data


@pytest.mark.api
@allure.feature("API")
@allure.story("Request · Plan · Status")
class TestAccount:
    """
    Ручки по заявке тестового аккаунта (read-only).
    Нужен test_account.public_request_id в testdata/test_data.local.json, иначе skip.
    """

    @allure.title("get-request: request of test account")
    def test_get_request_existing(self, api, public_request_id):
        data = assert_ok_data(api.get_request(public_request_id))

        with allure.step("Assert response contains requested public_request_id"):
            assert public_request_id in str(data), f"Other request returned: {data}"

    @allure.title("get-user-plan: current plan of test account")
    def test_get_user_plan_existing(self, api, public_request_id):
        data = assert_ok_data(api.get_user_plan(public_request_id))
        assert data, f"Empty user plan: {data}"

    @allure.title("magic-link: vpn:// link")
    def test_magic_link_existing(self, api, public_request_id):
        r = api.magic_link(public_request_id)
        assert_ok_data(r)

        with allure.step("Assert link uses vpn:// scheme"):
            assert "vpn://" in r.text, f"No vpn:// link:\n{r.text[:500]}"

    @allure.title("get-plans with public_request_id: active plans present")
    def test_get_plans_for_user(self, api, public_request_id):
        data = assert_ok_data(api.get_plans(public_request_id))
        assert data["active_plans"], f"No active plans: {data}"

    @allure.title("calculate-refund: amount is returned")
    def test_calculate_refund_existing(self, api, public_request_id):
        data = assert_ok_data(api.calculate_refund(public_request_id))
        assert "amount" in str(data), f"No amount: {data}"

    @pytest.mark.mutating
    @allure.title("invites/get-invite-link: referral link and invite_code")
    def test_get_invite_link_existing(self, api, public_request_id):
        data = assert_ok_data(api.get_invite_link(public_request_id))
        assert "invite_code" in str(data), f"No invite_code: {data}"


@pytest.mark.api
@allure.feature("API")
@allure.story("Diagnostics · Devices")
class TestDiagnostics:
    """app-report и update-device-info."""

    @pytest.mark.mutating
    @allure.title("app-report: creates report and returns its id")
    def test_app_report_created(self, api, public_request_id):
        r = api.app_report(
            public_request_id=public_request_id,
            platform=td.PLATFORM,
            version=td.APP_VERSION,
            firebase_installation_id=td.FIREBASE_INSTALLATION_ID,
            additional_info={"note": "qa-autotest"},
        )
        data = assert_ok_data(r)
        assert isinstance(data["app_report_id"], int), f"Unexpected data: {data}"

    @pytest.mark.xfail(reason=td.KNOWN_ISSUES["update_device_info_draft"], strict=False)
    @allure.title("update-device-info: endpoint is available")
    def test_update_device_info_available(self, api):
        r = api.update_device_info(td.NONEXISTENT_ID, platform=td.PLATFORM, app_version=td.APP_VERSION)
        assert r.status_code != 404 or r.json is not None, f"Endpoint not deployed: {r.text[:200]}"
