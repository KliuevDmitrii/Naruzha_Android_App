from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from utils.config_provider import ConfigProvider
from app.api.endpoints import Endpoints


@dataclass(frozen=True)
class ApiResponse:
    status_code: int
    json: Optional[Dict[str, Any]]
    text: str
    headers: Dict[str, str]
    url: str


class NaruzhuApi:
    def __init__(self, config: Optional[ConfigProvider] = None) -> None:
        self.cfg = config or ConfigProvider()
        self.api = self.cfg.api   # dict
        self.session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": self.api["user_agent"],
            "X-Device-Id": self.api["device_id"],
            "X-Supported-Awg-Version": self.api["supported_awg_version"],
        }

    def _url(self, path: str) -> str:
        return f"{self.api['base_url']}{path}"

    def _attach_allure(self, name: str, value: str) -> None:
        try:
            import allure
            allure.attach(value, name=name, attachment_type=allure.attachment_type.TEXT)
        except Exception:
            pass

    def _wrap(self, r: requests.Response) -> ApiResponse:
        try:
            payload = r.json()
        except Exception:
            payload = None

        self._attach_allure("Request URL", r.request.url or "")
        self._attach_allure("Request Method", r.request.method or "")
        self._attach_allure("Request Headers", str(dict(r.request.headers)))
        if r.request.body is not None:
            self._attach_allure("Request Body", str(r.request.body))
        self._attach_allure("Response Status", str(r.status_code))
        self._attach_allure("Response Headers", str(dict(r.headers)))
        self._attach_allure("Response Body", r.text)

        return ApiResponse(
            status_code=r.status_code,
            json=payload if isinstance(payload, dict) else None,
            text=r.text,
            headers=dict(r.headers),
            url=r.request.url or "",
        )

    # ===== auth+request =====

    def request_email_verification(self, email: str, reason: str = "mobile_request") -> ApiResponse:
        r = self.session.post(
            self._url(Endpoints.REQUEST_EMAIL_VERIFICATION),
            headers=self._headers(),
            json={"email": email, "reason": reason},
            timeout=30,
        )
        return self._wrap(r)

    def check_email_otp(self, email: str, otp_code: str) -> ApiResponse:
        r = self.session.post(
            self._url(Endpoints.CHECK_EMAIL_OTP),
            headers=self._headers(),
            json={"email": email, "otp_code": otp_code},
            timeout=30,
        )
        return self._wrap(r)

    def create_quick_login(self) -> ApiResponse:
        r = self.session.post(
            self._url(Endpoints.CREATE_QUICK_LOGIN),
            headers=self._headers(),
            timeout=30,
        )
        return self._wrap(r)

    def check_quick_login(self, quick_login_code: str) -> ApiResponse:
        r = self.session.post(
            self._url(Endpoints.CHECK_QUICK_LOGIN),
            headers=self._headers(),
            json={"quick_login_code": quick_login_code},
            timeout=30,
        )
        return self._wrap(r)

    def get_request(self, public_request_id: str) -> ApiResponse:
        r = self.session.get(
            self._url(Endpoints.GET_REQUEST),
            headers=self._headers(),
            params={"public_request_id": public_request_id},
            timeout=30,
        )
        return self._wrap(r)

    # ===== keys =====

    def download_awg_key(self, public_request_id: str, force_update_device: Optional[bool] = None) -> ApiResponse:
        params: Dict[str, Any] = {"public_request_id": public_request_id}
        if force_update_device is not None:
            params["force_update_device"] = str(force_update_device).lower()

        r = self.session.get(
            self._url(Endpoints.DOWNLOAD_AWG_KEY),
            headers=self._headers(),
            params=params,
            timeout=30,
        )
        return self._wrap(r)

    def download_anonymous_key(self) -> ApiResponse:
        r = self.session.get(
            self._url(Endpoints.DOWNLOAD_ANONYMOUS_KEY),
            headers=self._headers(),
            timeout=30,
        )
        return self._wrap(r)

    # ===== support =====

    def check_change_server(self, public_request_id: str) -> ApiResponse:
        r = self.session.get(
            self._url(Endpoints.CHECK_CHANGE_SERVER),
            headers=self._headers(),
            params={"public_request_id": public_request_id},
            timeout=30,
        )
        return self._wrap(r)

    def change_server(self, public_request_id: str) -> ApiResponse:
        r = self.session.post(
            self._url(Endpoints.CHANGE_SERVER),
            headers=self._headers(),
            json={"public_request_id": public_request_id},
            timeout=30,
        )
        return self._wrap(r)

    def app_report(
        self,
        public_request_id: str,
        platform: str,
        version: str,
        firebase_installation_id: str,
        additional_info: Optional[Dict[str, Any]] = None,
    ) -> ApiResponse:
        payload = {
            "version": version,
            "platform": platform,
            "public_request_id": public_request_id,
            "firebase_installation_id": firebase_installation_id,
            "additional_info": additional_info or {},
        }
        r = self.session.post(
            self._url(Endpoints.APP_REPORT),
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        return self._wrap(r)

    # ===== utility =====

    def get_country(self) -> ApiResponse:
        r = self.session.get(
            self._url(Endpoints.GET_COUNTRY),
            headers=self._headers(),
            timeout=30,
        )
        return self._wrap(r)

    def server_datetime(self) -> ApiResponse:
        r = self.session.get(
            self._url(Endpoints.SERVER_DATETIME),
            headers=self._headers(),
            timeout=30,
        )
        return self._wrap(r)

    def countries(self) -> ApiResponse:
        r = self.session.get(
            self._url(Endpoints.COUNTRIES),
            headers=self._headers(),
            timeout=30,
        )
        return self._wrap(r)