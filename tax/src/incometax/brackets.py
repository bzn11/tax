"""Year-aware simplified Canadian federal + Ontario tax brackets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Bracket:
    up_to: float | None  # None = open-ended top bracket
    rate: float


# Simplified brackets for portfolio/demo use — not CRA-official filing software.
BRACKETS_BY_YEAR: dict[int, dict[str, list[Bracket]]] = {
    2024: {
        "federal": [
            Bracket(55_867, 0.15),
            Bracket(111_733, 0.205),
            Bracket(173_205, 0.26),
            Bracket(246_752, 0.29),
            Bracket(None, 0.33),
        ],
        "ontario": [
            Bracket(51_446, 0.0505),
            Bracket(102_894, 0.0915),
            Bracket(150_000, 0.1116),
            Bracket(220_000, 0.1216),
            Bracket(None, 0.1316),
        ],
    },
    2025: {
        "federal": [
            Bracket(57_375, 0.15),
            Bracket(114_750, 0.205),
            Bracket(177_882, 0.26),
            Bracket(253_414, 0.29),
            Bracket(None, 0.33),
        ],
        "ontario": [
            Bracket(52_886, 0.0505),
            Bracket(105_775, 0.0915),
            Bracket(150_000, 0.1116),
            Bracket(220_000, 0.1216),
            Bracket(None, 0.1316),
        ],
    },
}

# Fallback years use closest known schedule
DEFAULT_YEAR = 2024


def get_brackets(tax_year: int) -> dict[str, list[Bracket]]:
    if tax_year in BRACKETS_BY_YEAR:
        return BRACKETS_BY_YEAR[tax_year]
    # Prefer nearest lower year, else default
    available = sorted(BRACKETS_BY_YEAR.keys())
    for year in reversed(available):
        if year <= tax_year:
            return BRACKETS_BY_YEAR[year]
    return BRACKETS_BY_YEAR[DEFAULT_YEAR]


def apply_brackets(taxable_income: float, brackets: list[Bracket]) -> float:
    """Progressive tax from a bracket schedule."""
    if taxable_income <= 0:
        return 0.0

    tax = 0.0
    lower = 0.0
    for bracket in brackets:
        upper = bracket.up_to if bracket.up_to is not None else float("inf")
        segment = min(taxable_income, upper) - lower
        if segment > 0:
            tax += segment * bracket.rate
        if taxable_income <= upper:
            break
        lower = upper
    return tax


def marginal_rate(taxable_income: float, brackets: list[Bracket]) -> float:
    if taxable_income <= 0:
        return brackets[0].rate if brackets else 0.0
    lower = 0.0
    for bracket in brackets:
        upper = bracket.up_to if bracket.up_to is not None else float("inf")
        if taxable_income <= upper:
            return bracket.rate
        lower = upper
    return brackets[-1].rate if brackets else 0.0
