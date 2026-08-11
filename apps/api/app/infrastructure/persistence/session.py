"""SQLAlchemy session factory."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.persistence.db import get_engine


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False)


def reset_session_factory_cache() -> None:
    get_session_factory.cache_clear()
