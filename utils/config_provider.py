from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class ConfigProvider:
    """
    Единая точка доступа к настройкам проекта.

    Загружает config/.example.env (дефолты), затем config/.env (локальные значения поверх)
    и отдаёт готовые словари по слоям: api, db, appium, web.
    Окружение API выбирается переменной ENV: test | test2 | prod.
    """

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

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.get(key)
        if value is None or value.strip() == "":
            return default
        return value.strip().lower() in ("1", "true", "yes", "on")

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
            "timeout": float(self.get("API_TIMEOUT", "30")),
        }

    @property
    def appium(self) -> dict:
        return {
            "appium_url": self.get_required("APPIUM_URL"),
            "device_name": self.get_required("DEVICE_NAME"),
            "udid": self.get_required("UDID"),
            "app_package": self.get_required("APP_PACKAGE"),
            "app_activity": self.get_required("APP_ACTIVITY"),
            "no_reset": self.get_bool("APPIUM_NO_RESET", True),
            "implicit_wait": float(self.get("APPIUM_IMPLICIT_WAIT", "0")),
            "explicit_wait": float(self.get("APPIUM_EXPLICIT_WAIT", "15")),
        }

    @property
    def web(self) -> dict:
        return {
            "base_url": self.get_required("WEB_BASE_URL").rstrip("/"),
            "browser": self.get("WEB_BROWSER", "chrome").lower(),
            "headless": self.get_bool("WEB_HEADLESS", False),
            "explicit_wait": float(self.get("WEB_EXPLICIT_WAIT", "10")),
        }

    @property
    def db_name(self) -> str:
        """База под текущий ENV: DB_NAME_TEST / DB_NAME_TEST_2, иначе (и для prod) — DB_NAME."""
        key = {"test": "DB_NAME_TEST", "test2": "DB_NAME_TEST_2"}.get(self.env)
        return (self.get(key) if key else None) or self.get_required("DB_NAME")

    @property
    def db(self) -> dict:
        return {
            "ssh_host": self.get_required("SSH_HOST"),
            "ssh_port": int(self.get("SSH_PORT", "22")),
            "ssh_user": self.get_required("SSH_USER"),
            "ssh_key_path": self.get_required("SSH_KEY_PATH"),
            "db_host": self.get_required("DB_HOST"),
            "db_port": int(self.get("DB_PORT", "5432")),
            "db_name": self.db_name,
            "db_user": self.get_required("DB_USER"),
            "db_password": self.get_required("DB_PASSWORD"),
        }