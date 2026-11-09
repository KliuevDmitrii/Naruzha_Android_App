import allure
import pytest

from testdata import api_data as td
from tests.helpers.api_asserts import assert_api_error, assert_ok_data


@pytest.mark.api
@allure.feature("API")
@allure.story("Payments")
class TestPayments:
    """Ручки биллинга: предрасчёт, ссылки на оплату, автопродление."""

    @allure.title("toggle-auto-renewal: enabling is not allowed")
    def test_toggle_auto_renewal_enable_not_allowed(self, api):
        r = api.toggle_auto_renewal(td.NONEXISTENT_ID, auto_renewal=True)
        assert_api_error(r, 400, "auto_renewal_not_allowed")

    @allure.title("calculate-payment: invalid plan is rejected")
    def test_calculate_payment_invalid_plan(self, api, public_request_id):
        assert_api_error(api.calculate_payment(public_request_id, plan_id=-1), 400, "invalid_plan")

    @allure.title("calculate-payment: draft calculation for active plan")
    def test_calculate_payment_active_plan(self, api, public_request_id, active_plan_id):
        data = assert_ok_data(api.calculate_payment(public_request_id, plan_id=active_plan_id))
        assert isinstance(data, dict) and data, f"Empty calculation: {data}"

    @pytest.mark.mutating
    @allure.title("make-payment-link: returns payment link for active plan")
    def test_make_payment_link_active_plan(self, api, public_request_id, active_plan_id):
        r = api.make_payment_link(public_request_id, plan_id=active_plan_id, payment_method=td.PAYMENT_METHOD)
        data = assert_ok_data(r)
        assert "http" in str(data), f"No link in response: {data}"

    @pytest.mark.mutating
    @allure.title("get-payment-link: 307 redirect to payment page")
    def test_get_payment_link_redirect(self, api, public_user_id, active_plan_id):
        r = api.get_payment_link(public_user_id, plan_id=active_plan_id)

        with allure.step("Assert 307 with Location"):
            assert r.status_code == 307, f"\nURL: {r.url}\nBODY:\n{r.text[:500]}"
            assert r.headers.get("Location", "").startswith("http"), f"Headers: {r.headers}"

    @pytest.mark.xfail(reason=td.KNOWN_ISSUES["get_payment_link_not_json"], strict=False)
    @allure.title("get-payment-link: unknown user -> JSON error")
    def test_get_payment_link_unknown_user(self, api, active_plan_id):
        assert_api_error(api.get_payment_link(td.NONEXISTENT_ID, plan_id=active_plan_id), 400, "user_not_found")

    @pytest.mark.xfail(reason=td.KNOWN_ISSUES["payment_link_items_500"], strict=False)
    @allure.title("make-payment-link/items: unknown item -> 4xx, not 500")
    def test_make_payment_link_items_unknown_item(self, api, faker):
        r = api.make_payment_link_items(td.NONEXISTENT_ITEM_ID, email=faker.email())

        with allure.step("Assert client error, not server error"):
            assert 400 <= r.status_code < 500, f"\nURL: {r.url}\nGot {r.status_code}\nBODY:\n{r.text[:500]}"

    @pytest.mark.xfail(reason=td.KNOWN_ISSUES["item_payment_link_param"], strict=False)
    @allure.title("get-item-payment-link: unknown item -> 404")
    def test_get_item_payment_link_unknown_item(self, api):
        r = api.get_item_payment_link(td.NONEXISTENT_ITEM_ID, telegram_id=1)
        assert r.status_code == 404, f"\nURL: {r.url}\nBODY:\n{r.text[:500]}"
