"""
Тестовые данные для DB- и e2e-тестов (база naruzhu_test / naruzhu_test2).

Наборы значений собраны с тестовой БД. Появился новый статус/тип —
добавьте его сюда, тесты трогать не нужно.
"""

# Сколько последних записей проверять в тестах целостности
INTEGRITY_SAMPLE = 50

# requests.status
REQUEST_STATUSES = [
    "Blocked",
    "Free Trial",
    "Success - Paid Keys Email Sent",
]

# amnesia_keys.status / amnesia_keys.type
KEY_STATUSES = ["active", "blocked", "blocked forever"]
KEY_TYPES = ["R", "S", "X"]

# wg_servers.status / supported_awg_versions
SERVER_STATUSES = ["Ready", "Disabled", "Overloaded"]
AWG_VERSIONS = ["1.0", "1.5", "2.0", "2.1"]

# request_actions.action_type
ACTION_CREATE_LIGHT_KEY = "Create new key amnesia light"
ACTION_CREATE_BASE_KEY = "Create new key amnesia base"
ACTION_REFUND = "Refund of payment"

# request_events.event_name
EVENT_EMAIL_SENT = "Email sent"
EVENT_BILLING_SYNC = "Billing sync"
EVENT_PAID_UNTIL_CHANGED = "Paid Until changed"
