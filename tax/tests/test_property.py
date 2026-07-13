"""Unit tests for property tax helpers and service."""

from src.propertytax.calculator import calculate_estimated_tax
from src.propertytax.rollnumber import is_valid_roll_number, normalize_roll_number
from src.propertytax.service import estimate_property_taxes


def test_normalize_roll_number():
    assert normalize_roll_number("1936-040-010-12345-0000") == "1936040010123450000"
    assert normalize_roll_number(" 1936040010123450000 ") == "1936040010123450000"


def test_valid_roll_number():
    assert is_valid_roll_number("1936040010123450000")
    assert not is_valid_roll_number("123")
    assert not is_valid_roll_number("abc6040010123450000")


def test_calculate_estimated_tax():
    assert calculate_estimated_tax(1_000_000, 0.006, 0.0015) == 7500.0


def test_estimate_known_toronto_roll():
    outcome = estimate_property_taxes(
        ["1936040010123450000"],
        tax_year=2024,
        include_education=True,
    )
    assert outcome["property_count"] == 1
    assert outcome["total_tax"] > 0
    assert outcome["results"][0]["municipality"] == "Toronto"
    assert not outcome["warnings"]


def test_estimate_invalid_roll_warns():
    outcome = estimate_property_taxes(["bad-roll"], tax_year=2024)
    assert outcome["property_count"] == 0
    assert outcome["warnings"]
