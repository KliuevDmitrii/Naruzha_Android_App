from datetime import datetime, timezone

import allure
import pytest

from app.api.client import NaruzhuApi
from testdata import api_data as atd
from testdata import db_data as td
from tests.helpers.accounts import register_account
from tests.helpers.api_asserts import assert_api_error, assert_ok_data


def _as_utc(value) -> datetime:
    dt = datetime.fromisoformat(value) if isinstance(value, str) else value
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@pytest.mark.e2e
@pytest.mark.api
@pytest.mark.db
@pytest.mark.mutating
@allure.feature("E2E")
@allure.story("Registration: API -> DB -> OTP")
class TestRegistration:
    """Регистрация без почтового ящика: OTP берётся из requests.comments."""

    @allure.title("New user: unverified in DB, trial request with OTP")
    def test_new_user_saved_in_db(self, api, db, faker):
        email = faker.email()

        with allure.step(f"API: request-email-verification for {email}"):
            assert_ok_data(api.request_email_verification(email=email))

        with allure.step("DB: user exists, email not verified"):
            user = db.user_by_email(email)
            assert user is not None, f"User {email} not found in public.users"
            assert user["email_is_verified"] is False, f"User {user['id']} already verified"
            assert user["public_id"], f"Empty public_id for user {user['id']}"

        with allure.step("DB: one request in initial status with OTP"):
            requests = db.requests_by_user_id(user["id"])
            assert len(requests) == 1, f"Expected 1 request, got {len(requests)}"
            assert requests[0]["status"] == td.NEW_REQUEST_STATUS, f"Status: {requests[0]['status']}"
            assert db.otp_from_request(requests[0]), f"No OTP in request {requests[0]['db_id']}"

    @allure.title("OTP from DB confirms email and returns the same request")
    def test_registration_with_otp_from_db(self, api, db, faker):
        account = register_account(api, db, email=faker.email())

        with allure.step("DB: email is verified after check-email-otp"):
            assert db.user_by_id(account.user_id)["email_is_verified"] is True

    @allure.title("Wrong OTP is rejected and email stays unverified")
    def test_registration_with_wrong_otp(self, api, db, faker):
        email = faker.email()
        assert_ok_data(api.request_email_verification(email=email))
        real_otp = db.otp_by_email(email)
        wrong_otp = atd.WRONG_OTP if real_otp != atd.WRONG_OTP else "1111"

        with allure.step("API: check-email-otp with wrong code"):
            assert_api_error(api.check_email_otp(email=email, otp_code=wrong_otp), atd.INVALID_OTP_STATUS, "invalid_otp")

        with allure.step("DB: email is still not verified"):
            assert db.user_by_email(email)["email_is_verified"] is False


@pytest.mark.e2e
@pytest.mark.api
@pytest.mark.db
@allure.feature("E2E")
@allure.story("Account: API -> DB")
class TestAccountApiToDb:
    """
    Состояние аккаунта в API и БД совпадает.
    Аккаунт — из test_data.local.json или новый (registered_account).
    """

    @allure.title("get-request matches requests row in DB")
    def test_get_request_matches_db(self, api, db, public_request_id):
        with allure.step("API: get-request"):
            api_request = assert_ok_data(api.get_request(public_request_id))["request"]

        with allure.step("DB: request row"):
            row = db.request_by_public_id(public_request_id)
            assert row is not None, f"Request {public_request_id} not found in public.requests"

        with allure.step("Assert simplified_status matches DB status"):
            expected = td.SIMPLIFIED_STATUS.get(row["status"])
            if expected is None:
                pytest.skip(f"No mapping for DB status '{row['status']}' in db_data.SIMPLIFIED_STATUS")
            assert api_request["simplified_status"] == expected, (
                f"API {api_request['simplified_status']}, DB {row['status']}"
            )

        with allure.step("Assert paid_until matches"):
            assert _as_utc(api_request["paid_until"]) == _as_utc(row["paid_until"]), (
                f"paid_until: API {api_request['paid_until']}, DB {row['paid_until']}"
            )

    @pytest.mark.xfail(reason=atd.KNOWN_ISSUES["get_request_auto_renewal"], strict=False)
    @allure.title("get-request auto_renewal matches requests.auto_renewal")
    def test_get_request_auto_renewal_matches_db(self, api, db, public_request_id):
        api_request = assert_ok_data(api.get_request(public_request_id))["request"]
        row = db.request_by_public_id(public_request_id)
        assert api_request["auto_renewal"] == row["auto_renewal"], (
            f"auto_renewal: API {api_request['auto_renewal']}, DB {row['auto_renewal']}"
        )

    @allure.title("Request of account belongs to its user")
    def test_account_request_has_user(self, db, public_request_id, public_user_id):
        user = db.user_by_public_request_id(public_request_id)
        assert user is not None, f"No user for request {public_request_id}"
        assert str(user["public_id"]) == public_user_id, f"public_id {user['public_id']} != {public_user_id}"

    @pytest.mark.mutating
    @allure.title("download-awg-key creates active key for device in DB")
    def test_download_awg_key_saved_in_db(self, api_new_device, db, public_request_id):
        with allure.step("API: download-awg-key from new device"):
            r = api_new_device.download_awg_key(public_request_id, force_update_device=True)
            assert r.status_code == 200, f"\nURL: {r.url}\nBODY:\n{r.text[:500]}"

        with allure.step(f"DB: active key for device {api_new_device.device_id}"):
            keys = [
                k for k in db.keys_by_public_request_id(public_request_id)
                if k["device_id"] == api_new_device.device_id
            ]
            assert len(keys) == 1, f"Expected 1 key for device, got {len(keys)}"
            assert keys[0]["status"] == td.KEY_STATUS_ACTIVE, f"Key {keys[0]['id']} status: {keys[0]['status']}"

        with allure.step("DB: key is on existing server"):
            assert db.wg_server_by_id(keys[0]["server_id"]), f"Server {keys[0]['server_id']} not found"
