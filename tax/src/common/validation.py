"""Input validation helpers for tax forms."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class IncomeTaxInput(BaseModel):
    """Validated personal income tax request."""

    tax_year: int = Field(ge=2020, le=2030)
    income: float = Field(ge=0, le=50_000_000)
    rrsp: float = Field(ge=0, le=50_000_000)
    other_deductions: float = Field(default=0, ge=0, le=50_000_000)
    filing_status: str = Field(default="single")

    @field_validator("filing_status")
    @classmethod
    def normalize_status(cls, value: str) -> str:
        allowed = {"single", "married", "common_law"}
        normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
        if normalized not in allowed:
            raise ValueError(f"filing_status must be one of {sorted(allowed)}")
        return normalized


class PropertyTaxInput(BaseModel):
    """Validated property tax request."""

    tax_year: int = Field(ge=2020, le=2030)
    include_education: bool = True
    roll_numbers: list[str] = Field(min_length=1)

    @field_validator("roll_numbers")
    @classmethod
    def strip_rolls(cls, values: list[str]) -> list[str]:
        cleaned = [v.strip() for v in values if v and v.strip()]
        if not cleaned:
            raise ValueError("At least one roll number is required")
        if len(cleaned) > 50:
            raise ValueError("Maximum 50 roll numbers per request")
        return cleaned


class TaxProfile(BaseModel):
    """Lightweight user profile for personalization (session-scoped)."""

    display_name: str = Field(default="Guest", max_length=80)
    province: str = Field(default="Ontario")
    municipality: str = Field(default="Toronto")
    owns_property: bool = False
    has_rrsp: bool = True
    employment_type: str = Field(default="employed")
    goals: list[str] = Field(default_factory=list)

    @field_validator("display_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip() or "Guest"
        return cleaned[:80]

    @field_validator("employment_type")
    @classmethod
    def normalize_employment(cls, value: str) -> str:
        allowed = {"employed", "self_employed", "student", "retired"}
        normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
        if normalized not in allowed:
            raise ValueError(f"employment_type must be one of {sorted(allowed)}")
        return normalized


def validate_positive_number(value: Any, field_name: str = "value") -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number") from exc
    if number < 0:
        raise ValueError(f"{field_name} cannot be negative")
    return number
