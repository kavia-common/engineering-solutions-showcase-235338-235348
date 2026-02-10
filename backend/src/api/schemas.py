"""
Pydantic schemas for API responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ServiceOut(BaseModel):
    """Response model for a service offering."""

    id: int = Field(..., description="Database id of the service.")
    slug: str = Field(..., description="Unique service identifier (used in URLs/UI).")
    title: str = Field(..., description="Service display title.")
    short_desc: str = Field(..., description="Short summary used in cards/sections.")
    body: Optional[str] = Field(None, description="Optional long-form description.")
    icon: Optional[str] = Field(None, description="Optional UI icon token.")
    sort_order: int = Field(..., description="Sort order (ascending).")
    is_active: bool = Field(..., description="Whether the service is active/visible.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")

    model_config = {"from_attributes": True}


class TestimonialOut(BaseModel):
    """Response model for a testimonial."""

    id: int = Field(..., description="Database id of the testimonial.")
    client_name: str = Field(..., description="Name of the client (or anonymized label).")
    client_title: Optional[str] = Field(None, description="Client title/role.")
    company: Optional[str] = Field(None, description="Client company name.")
    quote: str = Field(..., description="Testimonial quote text.")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Optional rating (1-5).")
    is_featured: bool = Field(..., description="Whether this testimonial is featured.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")

    model_config = {"from_attributes": True}


class CaseStudyOut(BaseModel):
    """Response model for a case study entry."""

    id: int = Field(..., description="Database id of the case study.")
    slug: str = Field(..., description="Unique case study identifier (used in URLs/UI).")
    title: str = Field(..., description="Case study title.")
    summary: str = Field(..., description="Short summary.")
    industry: Optional[str] = Field(None, description="Industry (optional).")
    stack: Optional[str] = Field(None, description="Technology stack (optional).")
    challenge: Optional[str] = Field(None, description="Problem/challenge narrative.")
    solution: Optional[str] = Field(None, description="Solution narrative.")
    results: Optional[str] = Field(None, description="Results/outcomes narrative.")
    is_published: bool = Field(..., description="Whether the case study is published.")
    published_at: Optional[datetime] = Field(None, description="Publish date/time (optional).")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")

    model_config = {"from_attributes": True}


class HealthOut(BaseModel):
    """Response model for health/readiness checks."""

    status: str = Field(..., description="Overall status, e.g. 'ok' or 'degraded'.")
    db_connected: bool = Field(..., description="Whether the API can reach the database.")
