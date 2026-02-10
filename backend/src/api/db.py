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

    Supported env formats:
    - MYSQL_URL already in SQLAlchemy form (preferred):
        * mysql+pymysql://user:pass@host:port/dbname
        * mysql://user:pass@host:port/dbname
      In this case we use it (upgrading to mysql+pymysql if needed).

    - MYSQL_URL in "host:port/dbname" (or "mysql://host:port/dbname") form without credentials.
      This is a common platform-provided value; we then inject credentials from MYSQL_USER/MYSQL_PASSWORD.

    - Fallback: assemble from MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB.

    Returns:
        SQLAlchemy URL string usable by SQLAlchemy 2.x.
    """
    mysql_url = os.getenv("MYSQL_URL", "").strip()

    user = os.getenv("MYSQL_USER", "appuser").strip() or "appuser"
    password = os.getenv("MYSQL_PASSWORD", "dbuser123")
    host = os.getenv("MYSQL_HOST", "localhost").strip() or "localhost"
    # Default to the project’s MySQL port (see database/db_connection.txt).
    # Environment variables (MYSQL_PORT) still override this as expected.
    port = os.getenv("MYSQL_PORT", "5000").strip() or "5000"
    db = os.getenv("MYSQL_DB", "myapp").strip() or "myapp"

    if mysql_url:
        # 1) Fully-qualified SQLAlchemy URLs with creds.
        if mysql_url.startswith("mysql+pymysql://"):
            return mysql_url
        if mysql_url.startswith("mysql+mysqldb://"):
            # Normalize to PyMySQL (pure python) to avoid native driver deps.
            return "mysql+pymysql://" + mysql_url.removeprefix("mysql+mysqldb://")
        if mysql_url.startswith("mysql://"):
            # If credentials are present, keep them; otherwise inject from env.
            rest = mysql_url.removeprefix("mysql://")
            if "@" in rest:
                return "mysql+pymysql://" + rest
            # e.g. mysql://localhost:5000/myapp  -> inject creds
            return f"mysql+pymysql://{user}:{password}@{rest}"

        # 2) Non-SQLAlchemy host:port/db form (no scheme). Inject creds.
        # Examples:
        # - localhost:5000/myapp
        # - 127.0.0.1/myapp
        return f"mysql+pymysql://{user}:{password}@{mysql_url.lstrip('/')}"

    # 3) Assemble from individual MYSQL_* variables.
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
