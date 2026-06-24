from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


class DataProvider:
    """
    Хранит тест-данные из testdata/test_data.json.
    - Ленивая загрузка
    - Можно сохранять runtime-поля обратно в файл (по желанию)
    """

    def __init__(self, project_root: Optional[Path] = None, filename: str = "test_data.json") -> None:
        self._root = project_root or Path(__file__).resolve().parents[1]
        self._path = self._root / "testdata" / filename
        self._data: Optional[Dict[str, Any]] = None

    def _load(self) -> None:
        if self._data is not None:
            return
        if not self._path.exists():
            raise FileNotFoundError(f"Test data file not found: {self._path}")
        self._data = json.loads(self._path.read_text(encoding="utf-8"))

    @property
    def data(self) -> Dict[str, Any]:
        self._load()
        assert self._data is not None
        return self._data

    def get(self, path: str, default: Any = None) -> Any:
        self._load()
        assert self._data is not None

        node: Any = self._data
        for key in path.split("."):
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                return default
        return node

    def set(self, path: str, value: Any) -> None:
        self._load()
        assert self._data is not None

        keys = path.split(".")
        node: Any = self._data
        for k in keys[:-1]:
            if k not in node or not isinstance(node[k], dict):
                node[k] = {}
            node = node[k]
        node[keys[-1]] = value

    def save(self) -> None:
        self._load()
        assert self._data is not None
        self._path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )