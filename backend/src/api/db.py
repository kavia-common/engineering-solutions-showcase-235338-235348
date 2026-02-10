"""
Database configuration and session utilities.

Environment variables (preferred):
- MYSQL_URL: A SQLAlchemy-compatible URL, or a mysql CLI-style host/port info may be embedded by platform.
  Example SQLAlchemy URL: mysql+pymysql://user:pass@host:port/dbname

Fallback environment variables:
- MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

Notes:
- We keep this simple (no migrations) per project instructions.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def _build_sqlalchemy_url() -> str:
    """
    Build a SQLAlchemy MySQL URL from environment variables.

    MYSQL_URL, if present, is used as-is when it already looks like a SQLAlchemy URL.
    Otherwise, we assemble from individual MYSQL_* variables.

    Returns:
        SQLAlchemy URL string.
    """
    mysql_url = os.getenv("MYSQL_URL", "").strip()
    if mysql_url:
        # If it's already a SQLAlchemy URL, use it.
        if mysql_url.startswith("mysql+pymysql://") or mysql_url.startswith("mysql+mysqldb://") or mysql_url.startswith(
            "mysql://"
        ):
            return mysql_url

    host = os.getenv("MYSQL_HOST", "localhost").strip() or "localhost"
    port = os.getenv("MYSQL_PORT", "5000").strip() or "5000"
    user = os.getenv("MYSQL_USER", "appuser").strip() or "appuser"
    password = os.getenv("MYSQL_PASSWORD", "dbuser123")
    db = os.getenv("MYSQL_DB", "myapp").strip() or "myapp"

    # Use PyMySQL (pure python) driver.
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"


_ENGINE: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


# PUBLIC_INTERFACE
def get_engine() -> Engine:
    """Create (if needed) and return the SQLAlchemy engine."""
    global _ENGINE, _SessionLocal

    if _ENGINE is None:
        url = _build_sqlalchemy_url()
        _ENGINE = create_engine(
            url,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE)

    return _ENGINE


# PUBLIC_INTERFACE
def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session."""
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


# PUBLIC_INTERFACE
def check_db_connectivity() -> bool:
    """
    Perform a simple DB connectivity check.

    Returns:
        True if a trivial SELECT succeeds, else False.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@contextmanager
def db_session_context() -> Generator[Session, None, None]:
    """Context manager for non-FastAPI usage (kept for internal utilities)."""
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
