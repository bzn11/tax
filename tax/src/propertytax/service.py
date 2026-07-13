"""Property tax estimation orchestration service."""

from __future__ import annotations

from typing import Any

from src.propertytax.assessment import load_assessments, select_most_recent_assessment
from src.propertytax.calculator import calculate_estimated_tax
from src.propertytax.rollnumber import is_valid_roll_number, normalize_roll_number
from src.propertytax.taxrates import get_latest_tax_rate, load_tax_rates


def estimate_property_taxes(
    roll_numbers: list[str],
    *,
    tax_year: int,
    include_education: bool = True,
) -> dict[str, Any]:
    """
    Estimate property taxes for one or more Ontario roll numbers.

    Returns structured results plus warnings for invalid/missing data.
    """
    assessments_df = load_assessments()
    rates_df = load_tax_rates()

    results: list[dict[str, Any]] = []
    warnings: list[str] = []

    for raw in roll_numbers:
        roll = normalize_roll_number(raw)

        if not is_valid_roll_number(roll):
            warnings.append(f"Invalid roll number: {raw}")
            continue

        assessment = select_most_recent_assessment(assessments_df, roll, year=tax_year)
        if assessment is None:
            warnings.append(f"No assessment found for {roll}")
            continue

        rate = get_latest_tax_rate(
            rates_df,
            assessment["municipality"],
            assessment["property_class"],
            year=tax_year,
        )
        if rate is None:
            warnings.append(f"No tax rate found for {roll}")
            continue

        edu_rate = float(rate["education_rate"]) if include_education else 0.0
        municipal_rate = float(rate["municipal_rate"])
        estimated_tax = calculate_estimated_tax(
            float(assessment["cva"]),
            municipal_rate,
            edu_rate,
        )
        municipal_portion = round(float(assessment["cva"]) * municipal_rate, 2)
        education_portion = round(float(assessment["cva"]) * edu_rate, 2)

        results.append(
            {
                "roll_number": roll,
                "address": assessment["address"],
                "municipality": assessment["municipality"],
                "property_class": assessment["property_class"],
                "assessment_year": int(assessment["tax_year"]),
                "assessment_value": float(assessment["cva"]),
                "tax_rate_year": int(rate["year"]),
                "municipal_rate": municipal_rate,
                "education_rate": edu_rate,
                "municipal_tax": municipal_portion,
                "education_tax": education_portion,
                "estimated_tax": estimated_tax,
            }
        )

    total_tax = round(sum(r["estimated_tax"] for r in results), 2)
    return {
        "tax_year": tax_year,
        "include_education": include_education,
        "results": results,
        "warnings": warnings,
        "total_tax": total_tax,
        "property_count": len(results),
    }
