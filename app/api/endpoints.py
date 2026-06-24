from __future__ import annotations


class Endpoints:
    # ===== auth+request =====
    REQUEST_EMAIL_VERIFICATION = "/client-api/v1/request-email-verification"
    CHECK_EMAIL_OTP = "/client-api/v1/check-email-otp"
    CREATE_QUICK_LOGIN = "/client-api/v1/create-quick-login"
    CHECK_QUICK_LOGIN = "/client-api/v1/check-quick-login"
    GET_REQUEST = "/client-api/v1/get-request"

    # ===== keys =====
    DOWNLOAD_AWG_KEY = "/client-api/v1/download-awg-key"
    DOWNLOAD_ANONYMOUS_KEY = "/client-api/v1/download-anonymous-key"

    # ===== support =====
    CHECK_CHANGE_SERVER = "/client-api/v1/check-change-server"
    CHANGE_SERVER = "/client-api/v1/change-server"
    APP_REPORT = "/client-api/v1/app-report"

    # ===== utility =====
    GET_COUNTRY = "/client-api/v1/get-country"
    SERVER_DATETIME = "/client-api/v1/server-datetime"
    COUNTRIES = "/client-api/v1/countries"