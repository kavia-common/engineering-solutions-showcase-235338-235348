from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from src.api.db import check_db_connectivity, get_db_session
from src.api.models import CaseStudy, Lead, Service, Testimonial
from src.api.schemas import (
    CaseStudyOut,
    ContactCreateIn,
    ContactCreateOut,
    HealthOut,
    ServiceOut,
    TestimonialOut,
)

openapi_tags = [
    {"name": "Health", "description": "Health/readiness endpoints."},
    {"name": "Content", "description": "Read-only content endpoints used by the corporate website frontend."},
    {"name": "Contact", "description": "Endpoints for creating contact/lead submissions."},
]


def _cors_origins() -> List[str]:
    """Compute allowed CORS origins based on environment variables and safe defaults."""
    origins: List[str] = []

    # Frontend may supply its public URL as REACT_APP_FRONTEND_URL (or similar) during deployments.
    frontend_url = os.getenv("REACT_APP_FRONTEND_URL", "").strip()
    if frontend_url:
        origins.append(frontend_url)

    # Local dev default for React
    origins.append("http://localhost:3000")

    # Kavia internal preview URLs can vary; allow all by default only if explicitly requested.
    # If you want to allow all origins, set BACKEND_ALLOW_ALL_CORS=true.
    if os.getenv("BACKEND_ALLOW_ALL_CORS", "").lower() in {"1", "true", "yes"}:
        return ["*"]

    # De-duplicate while preserving order
    seen = set()
    deduped = []
    for o in origins:
        if o not in seen:
            deduped.append(o)
            seen.add(o)
    return deduped


app = FastAPI(
    title="Engineering Solutions Showcase API",
    description="Read-only content API for services, testimonials, and case studies.",
    version="0.2.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    response_model=HealthOut,
    tags=["Health"],
    summary="Health/readiness check",
    description="Returns service health. Attempts a lightweight DB connectivity check for readiness.",
    operation_id="health_get",
)
# PUBLIC_INTERFACE
def health_check() -> HealthOut:
    """Health/readiness check endpoint."""
    db_ok = check_db_connectivity()
    return HealthOut(status="ok" if db_ok else "degraded", db_connected=db_ok)


@app.get(
    "/api/services",
    response_model=list[ServiceOut],
    tags=["Content"],
    summary="List services",
    description="Returns active services ordered by sort_order, then title.",
    operation_id="list_services",
)
# PUBLIC_INTERFACE
def list_services(db: Session = Depends(get_db_session)) -> list[ServiceOut]:
    """Return active service offerings for the frontend UI."""
    rows = (
        db.query(Service)
        .filter(Service.is_active == 1)
        .order_by(asc(Service.sort_order), asc(Service.title))
        .all()
    )
    return [ServiceOut.model_validate(r) for r in rows]


@app.get(
    "/api/testimonials",
    response_model=list[TestimonialOut],
    tags=["Content"],
    summary="List testimonials",
    description="Returns testimonials ordered by featured first, then newest first.",
    operation_id="list_testimonials",
)
# PUBLIC_INTERFACE
def list_testimonials(db: Session = Depends(get_db_session)) -> list[TestimonialOut]:
    """Return testimonials for the frontend UI."""
    rows = (
        db.query(Testimonial)
        .order_by(desc(Testimonial.is_featured), desc(Testimonial.created_at), desc(Testimonial.id))
        .all()
    )
    return [TestimonialOut.model_validate(r) for r in rows]


@app.get(
    "/api/case-studies",
    response_model=list[CaseStudyOut],
    tags=["Content"],
    summary="List case studies",
    description="Returns published case studies ordered by published_at (desc), then id (desc).",
    operation_id="list_case_studies",
)
# PUBLIC_INTERFACE
def list_case_studies(db: Session = Depends(get_db_session)) -> list[CaseStudyOut]:
    """Return published case studies for the frontend UI."""
    rows = (
        db.query(CaseStudy)
        .filter(CaseStudy.is_published == 1)
        .order_by(desc(CaseStudy.published_at), desc(CaseStudy.id))
        .all()
    )
    return [CaseStudyOut.model_validate(r) for r in rows]


@app.get(
    "/api/case_studies",
    response_model=list[CaseStudyOut],
    tags=["Content"],
    summary="List case studies (legacy alias)",
    description="Alias of /api/case-studies for compatibility with alternative naming.",
    operation_id="list_case_studies_alias",
)
# PUBLIC_INTERFACE
def list_case_studies_alias(db: Session = Depends(get_db_session)) -> list[CaseStudyOut]:
    """Alias endpoint for /api/case-studies."""
    return list_case_studies(db)


def _get_client_ip(request: Request) -> Optional[str]:
    """
    Best-effort client IP extraction.

    Note: If the app is behind a proxy, proper trusted proxy handling should be configured.
    For now we record the direct client host and (optionally) the first X-Forwarded-For entry.
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # Take the first value (original client) and trim whitespace.
        return xff.split(",")[0].strip()[:45] or None
    if request.client and request.client.host:
        return request.client.host[:45]
    return None


@app.post(
    "/api/contact",
    response_model=ContactCreateOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Contact"],
    summary="Submit a contact form lead",
    description=(
        "Accepts contact/lead submissions, validates input, persists it to the MySQL `leads` table, "
        "and returns the created lead id and timestamp. Includes a honeypot field for basic spam filtering."
    ),
    operation_id="create_contact_lead",
)
# PUBLIC_INTERFACE
def create_contact_lead(payload: ContactCreateIn, request: Request, db: Session = Depends(get_db_session)) -> ContactCreateOut:
    """
    Create a new lead from a contact form submission.

    Parameters:
        payload: Validated contact submission fields.
        request: FastAPI request, used to capture IP/user-agent (best effort).
        db: SQLAlchemy session (dependency).

    Returns:
        ContactCreateOut containing id, created_at, and status.

    Notes:
        - Honeypot: if `payload.honeypot` is non-empty, we treat as likely spam and do not create a lead.
        - Rate limiting: TODO - integrate at gateway/proxy level or add a lightweight in-memory limiter if needed.
    """
    # Honeypot check (simple anti-bot measure).
    if payload.honeypot and payload.honeypot.strip():
        # Intentionally vague error; do not leak spam detection details.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid submission.")

    lead = Lead(
        name=payload.name.strip(),
        email=str(payload.email).strip(),
        company=(payload.company.strip() if payload.company else None),
        phone=(payload.phone.strip() if payload.phone else None),
        service_slug=(payload.service_slug.strip() if payload.service_slug else None),
        message=payload.message.strip(),
        source=(payload.source.strip() if payload.source else "website"),
        status="new",
        ip=_get_client_ip(request),
        user_agent=(request.headers.get("user-agent", "").strip()[:255] or None),
    )

    try:
        db.add(lead)
        db.commit()
        db.refresh(lead)
    except Exception:
        db.rollback()
        # Keep message generic; detailed error logging can be added later.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to submit contact request.")

    # Use DB-populated created_at when available; otherwise fall back to "now".
    created_at = getattr(lead, "created_at", None) or datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        # Ensure the API returns an aware datetime for consistency in JSON (clients can treat it as UTC).
        created_at = created_at.replace(tzinfo=timezone.utc)

    return ContactCreateOut(id=int(lead.id), created_at=created_at, status=str(lead.status))
