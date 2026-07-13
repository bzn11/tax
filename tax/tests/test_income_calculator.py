"""Unit tests for income tax calculator."""

from src.incometax.calculator import calculate_income_tax


def test_zero_income():
    result = calculate_income_tax(0, 0, tax_year=2024)
    assert result["total_tax"] == 0
    assert result["taxable_income"] == 0
    assert result["effective_rate"] == 0


def test_rrsp_reduces_taxable_income():
    base = calculate_income_tax(100_000, 0, tax_year=2024)
    with_rrsp = calculate_income_tax(100_000, 10_000, tax_year=2024)
    assert with_rrsp["taxable_income"] == 90_000
    assert with_rrsp["total_tax"] < base["total_tax"]
    assert with_rrsp["rrsp_estimated_savings"] > 0


def test_other_deductions_apply():
    result = calculate_income_tax(80_000, 0, other_deductions=5_000, tax_year=2024)
    assert result["taxable_income"] == 75_000
    assert result["total_deductions"] == 5_000


def test_negative_inputs_clamped():
    result = calculate_income_tax(-10, -5, other_deductions=-1, tax_year=2024)
    assert result["income"] == 0
    assert result["rrsp"] == 0
    assert result["total_tax"] == 0


def test_result_keys_present():
    result = calculate_income_tax(50_000, 2_000, tax_year=2025)
    for key in (
        "federal_tax",
        "ontario_tax",
        "total_tax",
        "net_income",
        "effective_rate",
        "marginal_rate",
        "tax_year",
    ):
        assert key in result
