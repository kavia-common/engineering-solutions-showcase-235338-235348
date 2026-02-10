from __future__ import annotations

import os
from typing import List

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from src.api.db import check_db_connectivity, get_db_session
from src.api.models import CaseStudy, Service, Testimonial
from src.api.schemas import CaseStudyOut, HealthOut, ServiceOut, TestimonialOut

openapi_tags = [
    {"name": "Health", "description": "Health/readiness endpoints."},
    {"name": "Content", "description": "Read-only content endpoints used by the corporate website frontend."},
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
