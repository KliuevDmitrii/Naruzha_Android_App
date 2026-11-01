from __future__ import annotations

from sqlalchemy import text

# Только SELECT. Параметры — через bind (:name), без форматирования строк.

HEALTHCHECK = text("SELECT 1")
