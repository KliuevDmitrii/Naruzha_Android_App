from __future__ import annotations


class Endpoints:
    """
    Пути ручек client-api v1 — единый источник URL для NaruzhuApi и тестов.

    Группы повторяют папки Insomnia-коллекции "VPNN client-api v1".
    Базовый адрес стенда (без /client-api/v1) берётся из ConfigProvider.api["base_url"].
    """

    PREFIX = "/client-api/v1"

    # ===== 01 Auth · Email OTP =====
    REQUEST_EMAIL_VERIFICATION = f"{PREFIX}/request-email-verification"
    CHECK_EMAIL_OTP = f"{PREFIX}/check-email-otp"

    # ===== 02 Quick Login (TV) =====
    CREATE_QUICK_LOGIN = f"{PREFIX}/create-quick-login"
    CONFIRM_QUICK_LOGIN = f"{PREFIX}/confirm-quick-login"
    CHECK_QUICK_LOGIN = f"{PREFIX}/check-quick-login"

    # ===== 03 Request · Plan · Status =====
    GET_REQUEST = f"{PREFIX}/get-request"
    GET_USER_PLAN = f"{PREFIX}/get-user-plan"
    MAGIC_LINK = f"{PREFIX}/magic-link"
    SET_FREE_STATUS = f"{PREFIX}/set-free-status"

    # ===== 04 Keys (AWG) =====
    DOWNLOAD_AWG_KEY = f"{PREFIX}/download-awg-key"
    DOWNLOAD_ANONYMOUS_KEY = f"{PREFIX}/download-anonymous-key"
    DOWNLOAD_PHYSICAL_AWG_KEY = f"{PREFIX}/download-physical-awg-key"

    # ===== 05 Change server =====
    CHECK_CHANGE_SERVER = f"{PREFIX}/check-change-server"
    CHANGE_SERVER = f"{PREFIX}/change-server"

    # ===== 06 Diagnostics · Devices =====
    APP_REPORT = f"{PREFIX}/app-report"
    UPDATE_DEVICE_INFO = f"{PREFIX}/update-device-info"  # DRAFT

    # ===== 07 Directories =====
    COUNTRIES = f"{PREFIX}/countries"
    GET_COUNTRY = f"{PREFIX}/get-country"
    GET_PLANS = f"{PREFIX}/get-plans"
    GET_PROMOCODE_ITEMS = f"{PREFIX}/get-promocode-items"
    GET_PAYMENT_PROVIDERS = f"{PREFIX}/get-payment-providers"
    SERVER_DATETIME = f"{PREFIX}/server-datetime"  # нет в коллекции

    # ===== 08 Payments =====
    CALCULATE_PAYMENT = f"{PREFIX}/calculate-payment"
    MAKE_PAYMENT_LINK = f"{PREFIX}/make-payment-link"
    MAKE_PAYMENT_LINK_ITEMS = f"{PREFIX}/make-payment-link/items"
    GET_PAYMENT_LINK = f"{PREFIX}/get-payment-link"
    GET_ITEM_PAYMENT_LINK = f"{PREFIX}/get-item-payment-link"
    TOGGLE_AUTO_RENEWAL = f"{PREFIX}/toggle-auto-renewal"
    GIFT_CARD_ACTIVATION = f"{PREFIX}/gift-card-activation"

    # ===== 09 Refund =====
    CALCULATE_REFUND = f"{PREFIX}/calculate-refund"
    MAKE_REFUND = f"{PREFIX}/make-refund"

    # ===== 10 Referral =====
    GET_INVITE_LINK = f"{PREFIX}/invites/get-invite-link"
