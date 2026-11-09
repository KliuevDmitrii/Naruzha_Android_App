import allure
import pytest

from app.api.client import NaruzhuApi
from testdata import db_data as td
from tests.helpers.api_asserts import assert_ok_data


@pytest.mark.e2e
@pytest.mark.api
@pytest.mark.db
@allure.feature("E2E")
@allure.story("API -> DB")
class TestApiToDb:
    """Сквозные проверки: действие через client-api -> состояние в БД стенда."""

    @pytest.mark.mutating
    @allure.title("request-email-verification creates unverified user in DB")
    def test_new_user_saved_in_db(self, api, db, faker):
        email = faker.email()

        with allure.step(f"API: request-email-verification for {email}"):
            assert_ok_data(api.request_email_verification(email=email))

        with allure.step("DB: user exists"):
            user = db.user_by_email(email)
            assert user is not None, f"User {email} not found in public.users"

        with allure.step("DB: email is not verified yet, public_id is set"):
            assert user["email_is_verified"] is False, f"Unexpected user: {user['id']}"
            assert user["public_id"], f"Empty public_id for user {user['id']}"

    @allure.title("get-request matches requests row in DB")
    def test_get_request_matches_db(self, api, db, public_request_id):
        with allure.step("API: get-request"):
            data = assert_ok_data(api.get_request(public_request_id))

        with allure.step("DB: request row"):
            row = db.request_by_public_id(public_request_id)
            assert row is not None, f"Request {public_request_id} not found in public.requests"
            assert row["status"] in td.REQUEST_STATUSES, f"Unknown status: {row['status']}"

        with allure.step("Assert auto_renewal is the same in API and DB"):
            api_request = data.get("request", data)
            if "auto_renewal" in api_request:
                assert api_request["auto_renewal"] == row["auto_renewal"], (
                    f"API auto_renewal={api_request['auto_renewal']}, DB={row['auto_renewal']}"
                )

    @allure.title("Request of test account belongs to its user")
    def test_account_request_has_user(self, db, public_request_id):
        user = db.user_by_public_request_id(public_request_id)
        assert user is not None, f"No user for request {public_request_id}"

        requests = db.requests_by_user_id(user["id"])
        assert public_request_id in [r["public_request_id"] for r in requests]

    @pytest.mark.mutating
    @allure.title("download-awg-key creates active key for device in DB")
    def test_download_awg_key_saved_in_db(self, config, db, public_request_id):
        api = NaruzhuApi(config)

        with allure.step("API: download-awg-key"):
            r = api.download_awg_key(public_request_id, force_update_device=True)
            assert r.status_code == 200, f"\nURL: {r.url}\nBODY:\n{r.text[:500]}"

        with allure.step(f"DB: active key for device {api.device_id}"):
            keys = [k for k in db.keys_by_public_request_id(public_request_id) if k["device_id"] == api.device_id]
            assert keys, f"No key for device {api.device_id} in public.amnesia_keys"
            assert keys[0]["status"] == "active", f"Key {keys[0]['id']} status: {keys[0]['status']}"

        with allure.step("DB: key is on existing server"):
            assert db.wg_server_by_id(keys[0]["server_id"]), f"Server {keys[0]['server_id']} not found"
