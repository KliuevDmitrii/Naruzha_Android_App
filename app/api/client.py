from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

import requests

from utils.attachments import attach_text
from utils.config_provider import ConfigProvider
from app.api.endpoints import Endpoints


@dataclass(frozen=True)
class ApiResponse:
    status_code: int
    json: Optional[Union[Dict[str, Any], list]]
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

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> ApiResponse:
        r = self.session.request(
            method,
            self._url(path),
            headers=self._headers(),
            params=params,
            json=json,
            timeout=self.api["timeout"],
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

    # ===== auth+request =====

    def request_email_verification(self, email: str, reason: str = "mobile_request") -> ApiResponse:
        return self._request("POST", Endpoints.REQUEST_EMAIL_VERIFICATION, json={"email": email, "reason": reason})

    def check_email_otp(self, email: str, otp_code: str) -> ApiResponse:
        return self._request("POST", Endpoints.CHECK_EMAIL_OTP, json={"email": email, "otp_code": otp_code})

    def create_quick_login(self) -> ApiResponse:
        return self._request("POST", Endpoints.CREATE_QUICK_LOGIN)

    def check_quick_login(self, quick_login_code: str) -> ApiResponse:
        return self._request("POST", Endpoints.CHECK_QUICK_LOGIN, json={"quick_login_code": quick_login_code})

    def get_request(self, public_request_id: str) -> ApiResponse:
        return self._request("GET", Endpoints.GET_REQUEST, params={"public_request_id": public_request_id})

    # ===== keys =====

    def download_awg_key(self, public_request_id: str, force_update_device: Optional[bool] = None) -> ApiResponse:
        params: Dict[str, Any] = {"public_request_id": public_request_id}
        if force_update_device is not None:
            params["force_update_device"] = str(force_update_device).lower()
        return self._request("GET", Endpoints.DOWNLOAD_AWG_KEY, params=params)

    def download_anonymous_key(self) -> ApiResponse:
        return self._request("GET", Endpoints.DOWNLOAD_ANONYMOUS_KEY)

    # ===== support =====

    def check_change_server(self, public_request_id: str) -> ApiResponse:
        return self._request("GET", Endpoints.CHECK_CHANGE_SERVER, params={"public_request_id": public_request_id})

    def change_server(self, public_request_id: str) -> ApiResponse:
        return self._request("POST", Endpoints.CHANGE_SERVER, json={"public_request_id": public_request_id})

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
        return self._request("POST", Endpoints.APP_REPORT, json=payload)

    # ===== utility =====

    def get_country(self) -> ApiResponse:
        return self._request("GET", Endpoints.GET_COUNTRY)

    def server_datetime(self) -> ApiResponse:
        return self._request("GET", Endpoints.SERVER_DATETIME)

    def countries(self) -> ApiResponse:
        return self._request("GET", Endpoints.COUNTRIES)
