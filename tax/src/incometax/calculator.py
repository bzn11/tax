"""Personal income tax estimation (Federal + Ontario)."""

from __future__ import annotations

from typing import Any

from src.incometax.brackets import apply_brackets, get_brackets, marginal_rate


def calculate_income_tax(
    income: float,
    rrsp: float = 0.0,
    other_deductions: float = 0.0,
    tax_year: int = 2024,
) -> dict[str, Any]:
    """
    Simplified Canada Federal + Ontario tax estimate.

    Portfolio/demo model — not a substitute for certified tax software.
    Includes year-aware brackets, effective/marginal rates, and net income.
    """
    income = max(0.0, float(income))
    rrsp = max(0.0, float(rrsp))
    other_deductions = max(0.0, float(other_deductions))

    total_deductions = rrsp + other_deductions
    taxable_income = max(0.0, income - total_deductions)

    brackets = get_brackets(tax_year)
    federal = apply_brackets(taxable_income, brackets["federal"])
    ontario = apply_brackets(taxable_income, brackets["ontario"])
    total_tax = federal + ontario

    combined_marginal = marginal_rate(taxable_income, brackets["federal"]) + marginal_rate(
        taxable_income, brackets["ontario"]
    )
    effective_rate = (total_tax / income) if income > 0 else 0.0
    rrsp_tax_savings = rrsp * combined_marginal if rrsp > 0 else 0.0

    return {
        "tax_year": tax_year,
        "income": round(income, 2),
        "rrsp": round(rrsp, 2),
        "other_deductions": round(other_deductions, 2),
        "total_deductions": round(total_deductions, 2),
        "taxable_income": round(taxable_income, 2),
        "federal_tax": round(federal, 2),
        "ontario_tax": round(ontario, 2),
        "total_tax": round(total_tax, 2),
        "net_income": round(income - total_tax, 2),
        "effective_rate": round(effective_rate, 4),
        "marginal_rate": round(combined_marginal, 4),
        "rrsp_estimated_savings": round(rrsp_tax_savings, 2),
    }
