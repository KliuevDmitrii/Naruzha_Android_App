"""
Тестовые данные для API-тестов client-api.

Здесь только статичные, не секретные значения: дефолты запросов, наборы
для параметризации и негативные кейсы. Меняете ожидание или добавляете
кейс — правите этот файл, тесты трогать не нужно.

Данные конкретного аккаунта (email, OTP, public_request_id, public_user_id)
лежат в testdata/test_data.local.json (не в git), шаблон — test_data.json.
"""

# ===== Общие значения =====

# Заведомо несуществующая заявка/пользователь
NONEXISTENT_ID = "00000000-0000-0000-0000-000000000000"
NONEXISTENT_QUICK_LOGIN_CODE = "0000-0000"
NONEXISTENT_ITEM_ID = 999999

PLATFORM = "test"
APP_VERSION = "1.6.1"
PAYMENT_METHOD = "card"
FIREBASE_INSTALLATION_ID = "qa-autotest"

# ===== Auth =====

# Допустимые reason для request-email-verification
OTP_REASONS = ["mobile_request", "website_request", "extension_request"]
DEFAULT_REASON = "mobile_request"

# (email, ожидаемый error.code)
INVALID_EMAILS = [
    ("not-an-email", "invalid_email_format"),
    ("user@", "invalid_email_format"),
    ("@example.com", "invalid_email_format"),
    ("user@@example.com", "invalid_email_format"),
]

INVALID_REASON = "bad_reason"
WRONG_OTP = "0000"
# По доке/коллекции invalid_otp -> 400, фактически API отвечает 401 (см. KNOWN_ISSUES["invalid_otp_status"])
INVALID_OTP_STATUS = 401

# ===== Quick Login =====

QUICK_LOGIN_CODE_PATTERN = r"^\d{4}-\d{4}$"
QUICK_LOGIN_TTL_MINUTES = 5

# ===== Keys (AWG) =====

# X-Supported-Awg-Version: пусто -> 1.0, невалидное -> 400 invalid_awg_version
AWG_VERSIONS = ["1.0", "1.5", "2.0", "2.1"]
INVALID_AWG_VERSIONS = ["9.9", "abc", "1"]

# ===== Directories =====

ISO_COUNTRY_CODE_PATTERN = r"^[A-Z]{2}$"
PLAN_REQUIRED_KEYS = ["id", "name", "price", "interval"]
PAYMENT_PROVIDERS_KEYS = ["service_id", "enabled", "hidden"]
# Допустимое расхождение часов сервера и машины с тестами
SERVER_TIME_TOLERANCE_SECONDS = 300

# ===== Negative: несуществующая заявка =====
# Один кейс = вызов метода NaruzhuApi с аргументами и ожидаемый ответ.
# Поля: id (имя кейса в отчёте), method, kwargs, status, code, mutating (ручка меняет данные при успехе).
NOT_FOUND_CASES = [
    dict(id="get-request", method="get_request",
         kwargs={"public_request_id": NONEXISTENT_ID}, status=400, code="request_not_found"),
    dict(id="get-user-plan", method="get_user_plan",
         kwargs={"public_request_id": NONEXISTENT_ID}, status=400, code="user_not_found"),
    dict(id="magic-link", method="magic_link",
         kwargs={"public_request_id": NONEXISTENT_ID}, status=400, code="request_not_found"),
    dict(id="download-awg-key", method="download_awg_key",
         kwargs={"public_request_id": NONEXISTENT_ID}, status=404, code="invalid_public_request_id"),
    dict(id="download-physical-awg-key", method="download_physical_awg_key",
         kwargs={"public_request_id": NONEXISTENT_ID}, status=404, code="invalid_public_request_id"),
    dict(id="check-change-server", method="check_change_server",
         kwargs={"public_request_id": NONEXISTENT_ID}, status=404, code="vpnn_request_not_found"),
    dict(id="change-server", method="change_server",
         kwargs={"public_request_id": NONEXISTENT_ID}, status=404, code="vpnn_request_not_found"),
    dict(id="calculate-payment", method="calculate_payment",
         kwargs={"public_request_id": NONEXISTENT_ID, "plan_id": None}, status=400, code="request_not_found"),
    dict(id="make-payment-link", method="make_payment_link",
         kwargs={"public_request_id": NONEXISTENT_ID, "plan_id": None}, status=400, code="request_not_found"),
    dict(id="toggle-auto-renewal", method="toggle_auto_renewal",
         kwargs={"public_request_id": NONEXISTENT_ID, "auto_renewal": False}, status=400, code="request_not_found"),
    dict(id="gift-card-activation", method="gift_card_activation",
         kwargs={"public_request_id": NONEXISTENT_ID, "promocode": "QA-NOT-EXISTS"}, status=400, code="request_not_found"),
    dict(id="calculate-refund", method="calculate_refund",
         kwargs={"public_request_id": NONEXISTENT_ID}, status=404, code="vpnn_request_not_found"),
    dict(id="make-refund", method="make_refund",
         kwargs={"public_request_id": NONEXISTENT_ID}, status=404, code="vpnn_request_not_found"),
    dict(id="get-invite-link", method="get_invite_link",
         kwargs={"public_request_id": NONEXISTENT_ID}, status=400, code="user_not_found"),
]
# plan_id=None в кейсах выше подставляется тестом: берётся первый активный тариф из get-plans.

# ===== Известные расхождения / баги (тесты помечены xfail) =====
KNOWN_ISSUES = {
    "promocode_items_type": "get-promocode-items всегда 400: требует поле 'type', которого нет в доке/коллекции",
    "item_payment_link_param": "get-item-payment-link: в коллекции параметр 'i', API требует 'item_id' и 'type'",
    "payment_link_items_500": "make-payment-link/items с несуществующим item_id отвечает 500 вместо 4xx",
    "set_free_status_not_found": "set-free-status с несуществующей заявкой -> not_allowed_free_status вместо vpnn_request_not_found",
    "update_device_info_draft": "update-device-info (DRAFT) не задеплоен: 404 Not Found",
    "get_payment_link_not_json": "get-payment-link отвечает текстом '400: User not found' вместо JSON {data, error}",
    "invalid_otp_status": "check-email-otp с неверным OTP: по доке 400, фактически 401 (тесты ждут 401)",
    "get_request_auto_renewal": "get-request возвращает auto_renewal=null, в requests.auto_renewal = true",
}

# Ошибка download-awg-key, когда на стенде нет живого сервера под версию AWG — это данные стенда, не баг
NO_SERVER_ERROR_CODE = "available_wg_server_not_found"
