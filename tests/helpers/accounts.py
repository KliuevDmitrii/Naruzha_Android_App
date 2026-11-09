from __future__ import annotations

from dataclasses import dataclass

import allure

from app.api.client import NaruzhuApi
from app.db.repository import NaruzhuDb
from tests.helpers.api_asserts import assert_ok_data


@dataclass(frozen=True)
class Account:
    """Тестовый аккаунт, зарегистрированный через API и подтверждённый OTP из БД."""

    email: str
    otp: str
    user_id: int
    public_user_id: str
    request_db_id: int
    public_request_id: str


def register_account(api: NaruzhuApi, db: NaruzhuDb, email: str) -> Account:
    """
    Регистрация без почты: request-email-verification -> users по email ->
    OTP из requests.comments -> check-email-otp. Возвращает данные нового аккаунта.
    """
    with allure.step(f"API: request-email-verification for {email}"):
        assert_ok_data(api.request_email_verification(email=email))

    with allure.step("DB: find user and request, read OTP"):
        user = db.user_by_email(email)
        assert user is not None, f"User {email} not found in public.users"
        request = db.latest_request_by_email(email)
        assert request is not None, f"No request for user {user['id']} in public.requests"
        otp = db.otp_from_request(request)
        assert otp, f"No otp_code in requests.comments for request {request['db_id']}"

    with allure.step("API: check-email-otp with OTP from DB"):
        data = assert_ok_data(api.check_email_otp(email=email, otp_code=otp))
        public_request_id = data["request"]["public_request_id"]
        assert public_request_id == request["public_request_id"], (
            f"API public_request_id {public_request_id} != DB {request['public_request_id']}"
        )

    return Account(
        email=email,
        otp=otp,
        user_id=user["id"],
        public_user_id=str(user["public_id"]),
        request_db_id=request["db_id"],
        public_request_id=public_request_id,
    )
