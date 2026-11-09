import allure
import pytest

from app.api.endpoints import Endpoints
from testdata import api_data as td
from tests.helpers.api_asserts import assert_api_error, assert_ok_data


@pytest.mark.api
@allure.feature("API")
@allure.story("Auth · Email OTP")
class TestEmailVerification:
    """request-email-verification: отправка OTP и регистрация по email."""

    @pytest.mark.mutating
    @pytest.mark.parametrize("reason", td.OTP_REASONS)
    @allure.title("Request email verification for new user")
    def test_request_email_verification_new_user(self, api, faker, reason):
        email = faker.email()

        with allure.step(f"Send request-email-verification: {email}, reason={reason}"):
            r = api.request_email_verification(email=email, reason=reason)

        data = assert_ok_data(r)
        # website_request + WEBSITE_NEW_USER_SKIP_OTP может вернуть public_request_id сразу
        assert data is None or "public_request_id" in data, f"Unexpected data: {data}"

    @pytest.mark.parametrize("email,code", td.INVALID_EMAILS, ids=[e for e, _ in td.INVALID_EMAILS])
    @allure.title("Invalid email format is rejected")
    def test_request_email_verification_invalid_email(self, api, email, code):
        assert_api_error(api.request_email_verification(email=email), 400, code)

    @allure.title("Unknown reason is rejected with invalid_parameters")
    def test_request_email_verification_invalid_reason(self, api, faker):
        r = api.request_email_verification(email=faker.email(), reason=td.INVALID_REASON)
        error = assert_api_error(r, 400, "invalid_parameters")

        with allure.step("Assert parameter_errors points to reason"):
            fields = [e.get("field") for e in error.get("parameter_errors", [])]
            assert "reason" in fields, f"parameter_errors: {error}"

    @allure.title("Missing email is rejected with invalid_parameters")
    def test_request_email_verification_without_email(self, api):
        r = api.request("POST", Endpoints.REQUEST_EMAIL_VERIFICATION, json={"reason": td.DEFAULT_REASON})
        assert_api_error(r, 400, "invalid_parameters")


@pytest.mark.api
@allure.feature("API")
@allure.story("Auth · Email OTP")
class TestCheckEmailOtp:
    """check-email-otp: проверка OTP и получение заявки."""

    @allure.title("Unknown user gets user_not_found")
    def test_check_email_otp_unknown_user(self, api, faker):
        r = api.check_email_otp(email=faker.email(), otp_code=td.WRONG_OTP)
        assert_api_error(r, 400, "user_not_found")

    @allure.title("Wrong OTP for existing user gets invalid_otp")
    def test_check_email_otp_wrong_code(self, api, account_email):
        assert_api_error(api.check_email_otp(email=account_email, otp_code=td.WRONG_OTP), 400, "invalid_otp")

    @allure.title("Valid OTP returns request with public_request_id")
    def test_check_email_otp_valid_code(self, api, account_email, account_otp):
        data = assert_ok_data(api.check_email_otp(email=account_email, otp_code=account_otp))

        with allure.step("Assert data.request.public_request_id is present"):
            assert data["request"]["public_request_id"], f"No public_request_id: {data}"
