"""
SQLAlchemy ORM models for the corporate website content schema.

These models align with the MySQL DDL described in:
engineering-solutions-showcase-235338-235349/database/schema.md
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class Service(Base):
    """Represents a service offering displayed on the corporate website."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    short_desc: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(TINYINT(1), nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class Testimonial(Base):
    """Represents a customer testimonial/quote."""

    __tablename__ = "testimonials"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    client_name: Mapped[str] = mapped_column(String(120), nullable=False)
    client_title: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(TINYINT(unsigned=True), nullable=True)
    is_featured: Mapped[bool] = mapped_column(TINYINT(1), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class CaseStudy(Base):
    """Represents a published (or draft) case study entry."""

    __tablename__ = "case_studies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    summary: Mapped[str] = mapped_column(String(600), nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    stack: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    challenge: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    results: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(TINYINT(1), nullable=False, default=1)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
