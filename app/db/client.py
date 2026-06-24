from __future__ import annotations

from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from utils.config_provider import ConfigProvider


class DbClient:
    def __init__(self) -> None:
        cfg = ConfigProvider()
        db_cfg = cfg.db

        self.ssh_host = db_cfg["ssh_host"]
        self.ssh_port = db_cfg["ssh_port"]
        self.ssh_user = db_cfg["ssh_user"]
        self.ssh_key = db_cfg["ssh_key_path"]

        self.db_host = db_cfg["db_host"]
        self.db_port = db_cfg["db_port"]
        self.db_name = db_cfg["db_name"]
        self.db_user = db_cfg["db_user"]
        self.db_password = db_cfg["db_password"]

        self.tunnel: SSHTunnelForwarder | None = None
        self.engine: Engine | None = None

    def connect(self) -> Engine:
        self.tunnel = SSHTunnelForwarder(
            ssh_address_or_host=(self.ssh_host, self.ssh_port),
            ssh_username=self.ssh_user,
            ssh_pkey=self.ssh_key,
            remote_bind_address=(self.db_host, self.db_port),
            local_bind_address=("127.0.0.1", 0),

            # важно: отключаем поиск ключей в агенте и ~/.ssh
            allow_agent=False,
            host_pkey_directories=[],
        )
        self.tunnel.start()

        local_port = self.tunnel.local_bind_port

        self.engine = create_engine(
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}@127.0.0.1:{local_port}/{self.db_name}",
            pool_pre_ping=True,
        )
        return self.engine

    def close(self) -> None:
        if self.engine is not None:
            self.engine.dispose()

        if self.tunnel is not None:
            self.tunnel.stop()