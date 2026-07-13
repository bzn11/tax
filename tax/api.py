"""
TaxForge REST API — thin FastAPI layer over existing domain services.

Run from the `tax/` directory:
    uvicorn api:app --reload --port 8000

This sits alongside the Streamlit UI and reuses the same calculators,
validation models, and AI service (no duplicated business logic).
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ai.service import get_ai_service
from src.common.paths import ensure_outputs_dir, safe_output_path
from src.common.validation import IncomeTaxInput, PropertyTaxInput, TaxProfile
from src.incometax.calculator import calculate_income_tax
from src.incometax.report import generate_income_report
from src.propertytax.report import generate_property_report
from src.propertytax.service import estimate_property_taxes

ensure_outputs_dir()

app = FastAPI(
    title="TaxForge API",
    description="Ontario tax estimation REST API for the TaxForge portfolio project.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class IncomeReviewRequest(BaseModel):
    calculation: dict[str, Any]
    profile: TaxProfile = Field(default_factory=TaxProfile)


class PropertyReviewRequest(BaseModel):
    calculation: dict[str, Any]
    profile: TaxProfile = Field(default_factory=TaxProfile)


class IncomeReportRequest(BaseModel):
    result: dict[str, Any]
    client_name: str = "Client"
    ai_summary: str | None = None


class PropertyReportRequest(BaseModel):
    results: list[dict[str, Any]]
    client_name: str = "Client"
    ai_summary: str | None = None
    total_tax: float | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "taxforge-api"}


@app.post("/api/v1/income/estimate")
def income_estimate(payload: IncomeTaxInput) -> dict[str, Any]:
    return calculate_income_tax(
        payload.income,
        payload.rrsp,
        payload.other_deductions,
        tax_year=payload.tax_year,
    )


@app.post("/api/v1/property/estimate")
def property_estimate(payload: PropertyTaxInput) -> dict[str, Any]:
    return estimate_property_taxes(
        payload.roll_numbers,
        tax_year=payload.tax_year,
        include_education=payload.include_education,
    )


@app.post("/api/v1/ai/income-review")
def ai_income_review(payload: IncomeReviewRequest) -> dict[str, Any]:
    if not payload.calculation:
        raise HTTPException(status_code=400, detail="calculation payload is required")
    review = get_ai_service().review_income(
        payload.calculation,
        profile=payload.profile.model_dump(),
    )
    return review.as_dict()


@app.post("/api/v1/ai/property-review")
def ai_property_review(payload: PropertyReviewRequest) -> dict[str, Any]:
    if not payload.calculation:
        raise HTTPException(status_code=400, detail="calculation payload is required")
    review = get_ai_service().review_property(
        payload.calculation,
        profile=payload.profile.model_dump(),
    )
    return review.as_dict()


@app.post("/api/v1/ai/recommendations")
def ai_recommendations(profile: TaxProfile) -> dict[str, Any]:
    tips = get_ai_service().dashboard_recommendations(profile.model_dump())
    return {
        "insights": [
            {"kind": t.kind, "title": t.title, "detail": t.detail, "priority": t.priority}
            for t in tips
        ]
    }


@app.post("/api/v1/reports/income")
def income_report(payload: IncomeReportRequest) -> dict[str, Any]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = safe_output_path(f"api_income_{stamp}.pdf")
    generate_income_report(
        payload.result,
        str(path),
        client_name=payload.client_name,
        ai_summary=payload.ai_summary,
    )
    return {"path": str(path.name), "message": "Report generated under tax/outputs/"}


@app.post("/api/v1/reports/property")
def property_report(payload: PropertyReportRequest) -> dict[str, Any]:
    if not payload.results:
        raise HTTPException(status_code=400, detail="results cannot be empty")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = safe_output_path(f"api_property_{stamp}.pdf")
    generate_property_report(
        payload.results,
        str(path),
        client_name=payload.client_name,
        ai_summary=payload.ai_summary,
        total_tax=payload.total_tax,
    )
    return {"path": str(path.name), "message": "Report generated under tax/outputs/"}
