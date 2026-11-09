from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

import requests

from utils.attachments import attach_text
from utils.config_provider import ConfigProvider
from app.api.endpoints import Endpoints


@dataclass(frozen=True)
class ApiResponse:
    """
    Неизменяемый снимок HTTP-ответа client-api для проверок в тестах.

    json — распарсенное тело (dict/list) или None, если ответ не JSON
    (например, файл ключа из download-awg-key или текст "400: User not found").
    """

    status_code: int
    json: Optional[Union[Dict[str, Any], list]]
    text: str
    headers: Dict[str, str]
    url: str


def _clean(d: Dict[str, Any]) -> Dict[str, Any]:
    """Убирает ключи со значением None — так опциональные поля не уходят в запрос."""
    return {k: v for k, v in d.items() if v is not None}


class NaruzhuApi:
    """
    HTTP-клиент client-api v1 (VPN Naruzhu): по одному методу на ручку.

    Методы ничего не проверяют — только отправляют запрос и возвращают ApiResponse.
    Заголовки User-Agent / X-Device-Id / X-Supported-Awg-Version берутся из конфига;
    их можно переопределить в конструкторе, а пустая строка убирает заголовок
    (например, NaruzhuApi(cfg, device_id="") — запрос "без устройства").
    """

    def __init__(
        self,
        config: Optional[ConfigProvider] = None,
        *,
        device_id: Optional[str] = None,
        awg_version: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        self.cfg = config or ConfigProvider()
        self.api = self.cfg.api   # dict
        self.device_id = self.api["device_id"] if device_id is None else device_id
        self.awg_version = self.api["supported_awg_version"] if awg_version is None else awg_version
        self.user_agent = self.api["user_agent"] if user_agent is None else user_agent
        self.session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": self.user_agent,
            "X-Device-Id": self.device_id,
            "X-Supported-Awg-Version": self.awg_version,
        }
        return {k: v for k, v in headers.items() if v}

    def _url(self, path: str) -> str:
        return f"{self.api['base_url']}{path}"

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        headers: Optional[Dict[str, Optional[str]]] = None,
        allow_redirects: bool = True,
    ) -> ApiResponse:
        """
        Низкоуровневый запрос: его используют методы ниже и негативные тесты
        с произвольным телом. headers дополняют стандартные, значение None удаляет заголовок.
        """
        merged = self._headers()
        for k, v in (headers or {}).items():
            if v is None:
                merged.pop(k, None)
            else:
                merged[k] = v

        r = self.session.request(
            method,
            self._url(path),
            headers=merged,
            params=params,
            json=json,
            timeout=self.api["timeout"],
            allow_redirects=allow_redirects,
        )
        return self._wrap(r)

    def _wrap(self, r: requests.Response) -> ApiResponse:
        try:
            payload = r.json()
        except ValueError:
            payload = None

        attach_text("Request", f"{r.request.method} {r.request.url}\n\n{dict(r.request.headers)}")
        if r.request.body is not None:
            body = r.request.body
            attach_text("Request Body", body.decode("utf-8", "replace") if isinstance(body, bytes) else str(body))
        attach_text("Response", f"{r.status_code}\n\n{dict(r.headers)}")
        attach_text("Response Body", r.text)

        return ApiResponse(
            status_code=r.status_code,
            json=payload if isinstance(payload, (dict, list)) else None,
            text=r.text,
            headers=dict(r.headers),
            url=r.request.url or "",
        )

    # ===== 01 Auth · Email OTP =====

    def request_email_verification(
        self,
        email: str,
        reason: str = "mobile_request",
        invite_code: Optional[str] = None,
        telegram_user_token: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> ApiResponse:
        """Отправка OTP / регистрация. extra — опциональные поля (utm_params, timezone, ...). Шлёт письмо!"""
        body = _clean({
            "reason": reason,
            "email": email,
            "invite_code": invite_code,
            "telegram_user_token": telegram_user_token,
        })
        body.update(extra or {})
        return self.request("POST", Endpoints.REQUEST_EMAIL_VERIFICATION, json=body)

    def check_email_otp(self, email: str, otp_code: str) -> ApiResponse:
        return self.request("POST", Endpoints.CHECK_EMAIL_OTP, json={"email": email, "otp_code": otp_code})

    # ===== 02 Quick Login (TV) =====

    def create_quick_login(self) -> ApiResponse:
        """Код быстрого входа для текущего X-Device-Id (старые коды устройства удаляются)."""
        return self.request("POST", Endpoints.CREATE_QUICK_LOGIN)

    def confirm_quick_login(self, public_request_id: str, quick_login_code: str) -> ApiResponse:
        """Привязка кода к заявке — вызывает уже авторизованное устройство."""
        return self.request(
            "POST",
            Endpoints.CONFIRM_QUICK_LOGIN,
            json={"public_request_id": public_request_id, "quick_login_code": quick_login_code},
        )

    def check_quick_login(self, quick_login_code: str) -> ApiResponse:
        """data.request = null — код не подтверждён; объект — подтверждён."""
        return self.request("POST", Endpoints.CHECK_QUICK_LOGIN, json={"quick_login_code": quick_login_code})

    # ===== 03 Request · Plan · Status =====

    def get_request(self, public_request_id: str) -> ApiResponse:
        return self.request("GET", Endpoints.GET_REQUEST, params={"public_request_id": public_request_id})

    def get_user_plan(self, public_request_id: str) -> ApiResponse:
        return self.request("GET", Endpoints.GET_USER_PLAN, params={"public_request_id": public_request_id})

    def magic_link(self, public_request_id: str) -> ApiResponse:
        return self.request("GET", Endpoints.MAGIC_LINK, params={"public_request_id": public_request_id})

    def set_free_status(self, public_request_id: str) -> ApiResponse:
        """Blocked -> Free. Изменяет данные!"""
        return self.request("POST", Endpoints.SET_FREE_STATUS, json={"public_request_id": public_request_id})

    # ===== 04 Keys (AWG) =====

    def download_awg_key(
        self,
        public_request_id: str,
        key_type: Optional[str] = None,
        iso_country_code: Optional[str] = None,
        force_update_device: Optional[bool] = None,
    ) -> ApiResponse:
        """Ответ — файл конфига (не JSON). Создаёт/занимает ключ из лимита!"""
        params = _clean({
            "public_request_id": public_request_id,
            "key_type": key_type,
            "iso_country_code": iso_country_code,
            "force_update_device": None if force_update_device is None else str(force_update_device).lower(),
        })
        return self.request("GET", Endpoints.DOWNLOAD_AWG_KEY, params=params)

    def download_anonymous_key(
        self,
        key_type: Optional[str] = None,
        iso_country_code: Optional[str] = None,
    ) -> ApiResponse:
        params = _clean({"key_type": key_type, "iso_country_code": iso_country_code})
        return self.request("GET", Endpoints.DOWNLOAD_ANONYMOUS_KEY, params=params)

    def download_physical_awg_key(
        self,
        public_request_id: str,
        awg_version: Optional[str] = None,
        key_type: Optional[str] = None,
        iso_country_code: Optional[str] = None,
    ) -> ApiResponse:
        """awg_version — в body, не в заголовке. Создаёт ключ и может отправить email!"""
        body = _clean({
            "public_request_id": public_request_id,
            "awg_version": awg_version or self.awg_version,
            "key_type": key_type,
            "iso_country_code": iso_country_code,
        })
        return self.request("POST", Endpoints.DOWNLOAD_PHYSICAL_AWG_KEY, json=body)

    # ===== 05 Change server =====

    def check_change_server(
        self,
        public_request_id: str,
        key_type: Optional[str] = None,
        iso_country_code: Optional[str] = None,
    ) -> ApiResponse:
        params = _clean({
            "public_request_id": public_request_id,
            "key_type": key_type,
            "iso_country_code": iso_country_code,
        })
        return self.request("GET", Endpoints.CHECK_CHANGE_SERVER, params=params)

    def change_server(
        self,
        public_request_id: str,
        key_type: Optional[str] = None,
        iso_country_code: Optional[str] = None,
    ) -> ApiResponse:
        """Меняет сервер у активного ключа и расходует лимит смен (3 за 12 ч)!"""
        body = _clean({
            "public_request_id": public_request_id,
            "key_type": key_type,
            "iso_country_code": iso_country_code,
        })
        return self.request("POST", Endpoints.CHANGE_SERVER, json=body)

    # ===== 06 Diagnostics · Devices =====

    def app_report(
        self,
        public_request_id: str,
        platform: str,
        version: str,
        firebase_installation_id: str,
        additional_info: Optional[Dict[str, Any]] = None,
        client_ip: Optional[str] = None,
    ) -> ApiResponse:
        """Создаёт запись в APP_REPORTS."""
        payload = {
            "version": version,
            "platform": platform,
            "public_request_id": public_request_id,
            "firebase_installation_id": firebase_installation_id,
            "additional_info": additional_info or {},
        }
        headers = {"X-Real-IP": client_ip} if client_ip else None
        return self.request("POST", Endpoints.APP_REPORT, json=payload, headers=headers)

    def update_device_info(
        self,
        public_request_id: str,
        platform: str,
        app_version: str,
        **fields: Any,
    ) -> ApiResponse:
        """DRAFT-ручка. fields — os_version, timezone, locale, device_vendor, device_model."""
        body = {"public_request_id": public_request_id, "platform": platform, "app_version": app_version, **fields}
        return self.request("POST", Endpoints.UPDATE_DEVICE_INFO, json=body)

    # ===== 07 Directories =====

    def countries(self) -> ApiResponse:
        return self.request("GET", Endpoints.COUNTRIES)

    def get_country(self) -> ApiResponse:
        """Страна по IP запроса — зависит от того, откуда идёт запрос."""
        return self.request("GET", Endpoints.GET_COUNTRY)

    def get_plans(self, public_request_id: Optional[str] = None) -> ApiResponse:
        """public_request_id опционален — добавляет архивный тариф пользователя."""
        return self.request("GET", Endpoints.GET_PLANS, params=_clean({"public_request_id": public_request_id}))

    def get_promocode_items(self, is_corporate: bool = False) -> ApiResponse:
        return self.request("GET", Endpoints.GET_PROMOCODE_ITEMS, params={"is_corporate": str(is_corporate).lower()})

    def get_payment_providers(self, service_domain: Optional[str] = None) -> ApiResponse:
        return self.request("GET", Endpoints.GET_PAYMENT_PROVIDERS, params=_clean({"service_domain": service_domain}))

    def server_datetime(self) -> ApiResponse:
        return self.request("GET", Endpoints.SERVER_DATETIME)

    # ===== 08 Payments =====

    def calculate_payment(self, public_request_id: str, plan_id: int, promocode: Optional[str] = None) -> ApiResponse:
        """Предрасчёт (draft) — без сохранения."""
        body = {"public_request_id": public_request_id, "plan_id": plan_id, "promocode": promocode}
        return self.request("POST", Endpoints.CALCULATE_PAYMENT, json=body)

    def make_payment_link(
        self,
        public_request_id: str,
        plan_id: int,
        payment_method: str = "card",
        auto_renewal: bool = False,
        platform: Optional[str] = None,
        promocode: Optional[str] = None,
        provider_id: Optional[str] = None,
    ) -> ApiResponse:
        """Ссылка на оплату подписки. Создаёт счёт в биллинге — только test!"""
        body = {
            "public_request_id": public_request_id,
            "platform": platform,
            "plan_id": plan_id,
            "auto_renewal": auto_renewal,
            "promocode": promocode,
            "payment_method": payment_method,
            "provider_id": provider_id,
        }
        return self.request("POST", Endpoints.MAKE_PAYMENT_LINK, json=body)

    def make_payment_link_items(
        self,
        item_id: int,
        email: str,
        payment_method: str = "card",
        platform: Optional[str] = None,
    ) -> ApiResponse:
        """Разовая покупка (сертификат) + создание пользователя по email."""
        body = _clean({"item_id": item_id, "email": email, "payment_method": payment_method, "platform": platform})
        return self.request("POST", Endpoints.MAKE_PAYMENT_LINK_ITEMS, json=body)

    def get_payment_link(
        self,
        public_user_id: str,
        plan_id: int,
        payment_method: Optional[str] = None,
        platform: Optional[str] = None,
        provider_id: Optional[str] = None,
    ) -> ApiResponse:
        """Успех — 307 с заголовком Location (редирект не выполняется). Меняет BILLING_PLAN_ID!"""
        params = _clean({
            "public_user_id": public_user_id,
            "p": plan_id,
            "payment_method": payment_method,
            "platform": platform,
            "provider_id": provider_id,
        })
        return self.request("GET", Endpoints.GET_PAYMENT_LINK, params=params, allow_redirects=False)

    def get_item_payment_link(
        self,
        item_id: int,
        telegram_id: int,
        payment_method: Optional[str] = None,
    ) -> ApiResponse:
        """Разовая покупка для TG-бота, ответ — редирект (не выполняется). Параметр i — как в коллекции."""
        params = _clean({"i": item_id, "telegram_id": telegram_id, "payment_method": payment_method})
        return self.request("GET", Endpoints.GET_ITEM_PAYMENT_LINK, params=params, allow_redirects=False)

    def toggle_auto_renewal(self, public_request_id: str, auto_renewal: bool = False) -> ApiResponse:
        """Разрешено только выключение; auto_renewal=True -> 400 auto_renewal_not_allowed."""
        body = {"public_request_id": public_request_id, "auto_renewal": auto_renewal}
        return self.request("POST", Endpoints.TOGGLE_AUTO_RENEWAL, json=body)

    def gift_card_activation(self, public_request_id: str, promocode: str, plan_id: Optional[int] = None) -> ApiResponse:
        """Активация 100% промокода — начисляет подписку!"""
        body = {"public_request_id": public_request_id, "promocode": promocode, "plan_id": plan_id}
        return self.request("POST", Endpoints.GIFT_CARD_ACTIVATION, json=body)

    # ===== 09 Refund =====

    def calculate_refund(self, public_request_id: str) -> ApiResponse:
        return self.request("GET", Endpoints.CALCULATE_REFUND, params={"public_request_id": public_request_id})

    def make_refund(self, public_request_id: str) -> ApiResponse:
        """Реальный возврат в биллинге — меняет PAID_UNTIL и статус!"""
        return self.request("POST", Endpoints.MAKE_REFUND, json={"public_request_id": public_request_id})

    # ===== 10 Referral =====

    def get_invite_link(self, public_request_id: str) -> ApiResponse:
        """Реферальная ссылка и invite_code (создаёт код, если его нет)."""
        return self.request("POST", Endpoints.GET_INVITE_LINK, json={"public_request_id": public_request_id})
