import pytest
import allure
import json

from tests.helpers.api_asserts import assert_ok_json


@pytest.mark.api
@allure.feature("API")
@allure.story("User registration")
@allure.title("Request email verification (new user)")
def test_request_email_verification_new_user(api, faker):
    email = faker.email()

    with allure.step(f"Send request-email-verification for email: {email}"):
        r = api.request_email_verification(email=email)

    # Проверяем строго структуру ответа
    body = assert_ok_json(r, exact_keys=["data", "error"])

    with allure.step("Assert error is null"):
        assert body["error"] is None, f"\nURL: {r.url}\nJSON:\n{body}"

    with allure.step("Assert data is null"):
        assert body["data"] is None, f"\nURL: {r.url}\nJSON:\n{body}"