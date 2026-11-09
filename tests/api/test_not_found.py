import allure
import pytest

from testdata import api_data as td
from tests.helpers.api_asserts import assert_api_error


@pytest.mark.api
@allure.feature("API")
@allure.story("Negative · nonexistent request")
@pytest.mark.parametrize("case", td.NOT_FOUND_CASES, ids=[c["id"] for c in td.NOT_FOUND_CASES])
def test_nonexistent_public_request_id(api, active_plan_id, case):
    """Кейсы — testdata/api_data.py::NOT_FOUND_CASES. Ручки с несуществующей заявкой не меняют данные."""
    allure.dynamic.title(f"{case['id']}: nonexistent public_request_id -> {case['status']} {case['code']}")

    kwargs = dict(case["kwargs"])
    if "plan_id" in kwargs and kwargs["plan_id"] is None:
        kwargs["plan_id"] = active_plan_id

    with allure.step(f"Call {case['method']}({kwargs})"):
        r = getattr(api, case["method"])(**kwargs)

    assert_api_error(r, case["status"], case["code"])


@pytest.mark.api
@allure.feature("API")
@allure.story("Negative · nonexistent request")
@pytest.mark.xfail(reason=td.KNOWN_ISSUES["set_free_status_not_found"], strict=False)
@allure.title("set-free-status: nonexistent public_request_id -> vpnn_request_not_found")
def test_set_free_status_nonexistent_request(api):
    assert_api_error(api.set_free_status(td.NONEXISTENT_ID), 400, "vpnn_request_not_found")


@pytest.mark.api
@allure.feature("API")
@allure.story("Negative · nonexistent request")
@allure.title("get-request: malformed public_request_id -> request_not_found")
def test_get_request_malformed_id(api):
    assert_api_error(api.get_request("not-a-uuid"), 400, "request_not_found")
