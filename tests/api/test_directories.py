import re
from datetime import datetime, timezone

import allure
import pytest

from testdata import api_data as td
from tests.helpers.api_asserts import assert_ok_data


@pytest.mark.api
@allure.feature("API")
@allure.story("Directories")
class TestDirectories:
    """Справочники client-api: страны, гео по IP, тарифы, способы оплаты, время сервера."""

    @allure.title("countries: non-empty list with label and ISO code")
    def test_countries_returns_list(self, api):
        data = assert_ok_data(api.countries())
        countries = data["countries"]

        with allure.step("Assert list is not empty"):
            assert isinstance(countries, list) and countries, f"Empty countries: {data}"

        with allure.step("Assert every item has country_label and valid iso_country_code"):
            for c in countries:
                assert c.get("country_label"), f"Empty country_label: {c}"
                assert re.match(td.ISO_COUNTRY_CODE_PATTERN, c.get("iso_country_code", "")), f"Bad ISO code: {c}"

        with allure.step("Assert ISO codes are unique"):
            codes = [c["iso_country_code"] for c in countries]
            assert len(codes) == len(set(codes)), f"Duplicated ISO codes: {codes}"

    @allure.title("get-country: two-letter country of request IP")
    def test_get_country_returns_code(self, api):
        data = assert_ok_data(api.get_country())

        with allure.step("Assert country is 2-letter lowercase code"):
            assert re.match(r"^[a-z]{2}$", data.get("country", "")), f"Bad country: {data}"

    @allure.title("server-datetime: timezone-aware ISO close to local time")
    def test_server_datetime_is_current(self, api):
        data = assert_ok_data(api.server_datetime())

        with allure.step("Parse server_datetime as ISO 8601 with timezone"):
            server_dt = datetime.fromisoformat(data["server_datetime"])
            assert server_dt.tzinfo is not None, f"Naive datetime: {data}"

        with allure.step(f"Assert drift <= {td.SERVER_TIME_TOLERANCE_SECONDS}s"):
            drift = abs((datetime.now(timezone.utc) - server_dt).total_seconds())
            assert drift <= td.SERVER_TIME_TOLERANCE_SECONDS, f"Server time drift {drift:.0f}s: {server_dt}"

    @allure.title("get-plans: active plans with id, name, price and interval")
    def test_get_plans_returns_active_plans(self, api):
        data = assert_ok_data(api.get_plans())
        plans = data["active_plans"]

        with allure.step("Assert active_plans is not empty"):
            assert isinstance(plans, list) and plans, f"No active plans: {data}"

        with allure.step(f"Assert every plan has {td.PLAN_REQUIRED_KEYS} and rub/usd price"):
            for plan in plans:
                missing = [k for k in td.PLAN_REQUIRED_KEYS if k not in plan]
                assert not missing, f"Plan {plan.get('id')} misses {missing}: {plan}"
                assert {"rub", "usd"} <= set(plan["price"]), f"Bad price: {plan}"

        with allure.step("Assert plan ids are unique"):
            ids = [p["id"] for p in plans]
            assert len(ids) == len(set(ids)), f"Duplicated plan ids: {ids}"

    @allure.title("get-payment-providers: service_id, enabled, hidden")
    def test_get_payment_providers_structure(self, api):
        data = assert_ok_data(api.get_payment_providers())

        with allure.step(f"Assert keys {td.PAYMENT_PROVIDERS_KEYS}"):
            assert set(td.PAYMENT_PROVIDERS_KEYS) <= set(data), f"Bad structure: {data}"
            assert isinstance(data["enabled"], list) and isinstance(data["hidden"], list)

    @pytest.mark.xfail(reason=td.KNOWN_ISSUES["promocode_items_type"], strict=False)
    @pytest.mark.parametrize("is_corporate", [False, True], ids=["regular", "corporate"])
    @allure.title("get-promocode-items: list of items")
    def test_get_promocode_items(self, api, is_corporate):
        assert_ok_data(api.get_promocode_items(is_corporate=is_corporate))
