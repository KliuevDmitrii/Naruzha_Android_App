"""
SQL-запросы к БД стенда (PostgreSQL, база naruzhu_test, схема public).

Только SELECT. Параметры — через bind (:name), без форматирования строк.
Списки колонок вынесены в константы: запрос без WHERE по большим таблицам
всегда с :limit.

Связи таблиц:
  users.id            <- requests.user_id
  requests.db_id      <- amnesia_keys.request_id, request_actions.request_id, request_events.request_id
  wg_servers.id       <- amnesia_keys.server_id
  requests.public_request_id — id заявки в client-api
"""
from __future__ import annotations

from sqlalchemy import text

HEALTHCHECK = text("SELECT 1")

# ===== users =====

USERS_COLUMNS = """
    id, email, public_id, consent_to_emails, telegram_id, is_employed, key_limit,
    billing_id, billing_plan_id, billing_auto_renewal, chosen_plan_id, auth_id,
    first_paid_at, last_paid_at, email_is_verified
"""

USERS = text(f"SELECT {USERS_COLUMNS} FROM public.users ORDER BY id DESC LIMIT :limit")
USER_BY_ID = text(f"SELECT {USERS_COLUMNS} FROM public.users WHERE id = :user_id")
USER_BY_EMAIL = text(f"SELECT {USERS_COLUMNS} FROM public.users WHERE lower(email) = lower(:email)")
USER_BY_PUBLIC_ID = text(f"SELECT {USERS_COLUMNS} FROM public.users WHERE public_id = :public_id")
USER_BY_PUBLIC_REQUEST_ID = text(f"""
    SELECT {', '.join('u.' + c.strip() for c in USERS_COLUMNS.split(','))}
    FROM public.users u
    JOIN public.requests r ON r.user_id = u.id
    WHERE r.public_request_id = :public_request_id
""")

# ===== requests =====

REQUESTS_COLUMNS = """
    db_id, invite_code, status, created_time, "comments", have_code, public_request_id,
    requested_country_id, paid_until, initial_user_ip, auto_renewal, pool_prefix, chat_id,
    fixed_otp, service_type, user_id, alias, created_with_device_id
"""

REQUESTS = text(f"SELECT {REQUESTS_COLUMNS} FROM public.requests ORDER BY db_id DESC LIMIT :limit")
REQUEST_BY_DB_ID = text(f"SELECT {REQUESTS_COLUMNS} FROM public.requests WHERE db_id = :db_id")
REQUEST_BY_PUBLIC_ID = text(
    f"SELECT {REQUESTS_COLUMNS} FROM public.requests WHERE public_request_id = :public_request_id"
)
REQUESTS_BY_USER_ID = text(
    f"SELECT {REQUESTS_COLUMNS} FROM public.requests WHERE user_id = :user_id ORDER BY db_id DESC"
)

# ===== amnesia_keys =====
# client_private_key — секрет: не выводить в логи/Allure и не сравнивать целиком в assert.

AMNESIA_KEYS_COLUMNS = """
    id, key_name, request_id, status, created_time, client_public_key, client_private_key,
    client_ip, country_id, server_id, pool_prefix, is_light, is_base, token_id, "type",
    invite_code, device_id, first_auth_time, last_auth_time, manually_updated_server_at,
    user_agent, last_requested
"""

AMNESIA_KEYS = text(f"SELECT {AMNESIA_KEYS_COLUMNS} FROM public.amnesia_keys ORDER BY id DESC LIMIT :limit")
AMNESIA_KEY_BY_ID = text(f"SELECT {AMNESIA_KEYS_COLUMNS} FROM public.amnesia_keys WHERE id = :key_id")
AMNESIA_KEYS_BY_REQUEST_ID = text(
    f"SELECT {AMNESIA_KEYS_COLUMNS} FROM public.amnesia_keys WHERE request_id = :request_id ORDER BY id DESC"
)
AMNESIA_KEYS_BY_DEVICE_ID = text(
    f"SELECT {AMNESIA_KEYS_COLUMNS} FROM public.amnesia_keys WHERE device_id = :device_id ORDER BY id DESC"
)
AMNESIA_KEYS_BY_PUBLIC_REQUEST_ID = text(f"""
    SELECT {', '.join('k.' + c.strip() for c in AMNESIA_KEYS_COLUMNS.split(','))}
    FROM public.amnesia_keys k
    JOIN public.requests r ON r.db_id = k.request_id
    WHERE r.public_request_id = :public_request_id
    ORDER BY k.id DESC
""")

# ===== request_actions =====

REQUEST_ACTIONS_COLUMNS = "id, request_id, action_type, is_done, is_failed, created_at, action_parameters"

REQUEST_ACTIONS = text(
    f"SELECT {REQUEST_ACTIONS_COLUMNS} FROM public.request_actions ORDER BY id DESC LIMIT :limit"
)
REQUEST_ACTIONS_BY_REQUEST_ID = text(
    f"SELECT {REQUEST_ACTIONS_COLUMNS} FROM public.request_actions WHERE request_id = :request_id ORDER BY id DESC"
)

# ===== request_events =====

REQUEST_EVENTS_COLUMNS = "id, request_id, event_time, event_name, event_parameters"

REQUEST_EVENTS = text(
    f"SELECT {REQUEST_EVENTS_COLUMNS} FROM public.request_events ORDER BY id DESC LIMIT :limit"
)
REQUEST_EVENTS_BY_REQUEST_ID = text(
    f"SELECT {REQUEST_EVENTS_COLUMNS} FROM public.request_events WHERE request_id = :request_id ORDER BY id DESC"
)

# ===== wg_servers =====

WG_SERVERS_COLUMNS = """
    id, ip, status, provider, "location", "comments", created_time, last_synchronization_time,
    "template", template_params, bandwidth_mbps, updated_at, interface, usage_limit_percentage,
    used_capacity_percentage, current_load_mbps, hard_limit_percent, no_ips, subdomain, server_name,
    server_types, start_client_ip, end_client_ip, server_pool, supported_awg_versions, tunnel_probe_url
"""

WG_SERVERS = text(f"SELECT {WG_SERVERS_COLUMNS} FROM public.wg_servers ORDER BY id LIMIT :limit")
WG_SERVER_BY_ID = text(f"SELECT {WG_SERVERS_COLUMNS} FROM public.wg_servers WHERE id = :server_id")
