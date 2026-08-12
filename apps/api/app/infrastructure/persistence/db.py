"""Database URL and engine helpers (sync) — no business logic."""

from __future__ import annotations

import os
from functools import lru_cache
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def build_database_url() -> str:
    """Prefer DATABASE_URL; otherwise assemble from MYSQL_* env."""
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit

    user = os.getenv("MYSQL_USER", "stk")
    password = os.getenv("MYSQL_PASSWORD", "changeme_stk_dev")
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    database = os.getenv("MYSQL_DATABASE", "stk")
    return (
        f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{database}?charset=utf8mb4"
    )


def build_connect_args() -> dict:
    """TLS for managed MySQL with require_secure_transport=ON."""
    flag = os.getenv("MYSQL_SSL", "").strip().lower()
    if flag not in ("1", "true", "yes", "required"):
        return {}

    import ssl

    ctx = ssl.create_default_context()
    ca_path = os.getenv("MYSQL_SSL_CA", "").strip()
    if ca_path:
        ctx.load_verify_locations(ca_path)
    return {"ssl": ctx}


def create_db_engine(*, poolclass=None) -> Engine:
    kwargs: dict = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }
    connect_args = build_connect_args()
    if connect_args:
        kwargs["connect_args"] = connect_args
    if poolclass is not None:
        kwargs["poolclass"] = poolclass
    return create_engine(build_database_url(), **kwargs)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_db_engine()


def reset_engine_cache() -> None:
    """Test helper — drop cached engine after env changes."""
    get_engine.cache_clear()


def check_database() -> bool:
    """Return True if MySQL answers SELECT 1."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
