from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class ConfigProvider:
    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = project_root or Path(__file__).resolve().parents[1]

        # config/.example.env
        example_env = self.project_root / "config" / ".example.env"
        # config/.env
        local_env = self.project_root / "config" / ".env"

        # Сначала загружаем example как дефолты
        if example_env.exists():
            load_dotenv(example_env, override=False)

        # Потом локальный .env поверх
        if local_env.exists():
            load_dotenv(local_env, override=True)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        value = os.getenv(key)
        return value if value is not None else default

    def get_required(self, key: str) -> str:
        value = os.getenv(key)
        if value is None or value.strip() == "":
            raise ValueError(f"Missing required config: {key}")
        return value

    @property
    def env(self) -> str:
        return self.get("ENV", "test").lower()

    @property
    def api(self) -> dict:
        env = self.env

        if env == "test2":
            base_url = self.get_required("API_BASE_URL_TEST_2")
        elif env == "prod":
            base_url = self.get_required("API_BASE_URL")
        else:
            base_url = self.get_required("API_BASE_URL_TEST")

        return {
            "env": env,
            "base_url": base_url.rstrip("/"),
            "user_agent": self.get_required("USER_AGENT"),
            "supported_awg_version": self.get_required("SUPPORTED_AWG_VERSION"),
            "device_id": self.get_required("DEVICE_ID"),
        }

    @property
    def appium(self) -> dict:
        return {
            "appium_url": self.get_required("APPIUM_URL"),
            "device_name": self.get_required("DEVICE_NAME"),
            "udid": self.get_required("UDID"),
            "app_package": self.get_required("APP_PACKAGE"),
            "app_activity": self.get_required("APP_ACTIVITY"),
        }

    @property
    def db(self) -> dict:
        return {
            "ssh_host": self.get_required("SSH_HOST"),
            "ssh_port": int(self.get("SSH_PORT", "22")),
            "ssh_user": self.get_required("SSH_USER"),
            "ssh_key_path": self.get_required("SSH_KEY_PATH"),
            "db_host": self.get_required("DB_HOST"),
            "db_port": int(self.get("DB_PORT", "5432")),
            "db_name": self.get_required("DB_NAME"),
            "db_user": self.get_required("DB_USER"),
            "db_password": self.get_required("DB_PASSWORD"),
        }