"""Validation model tests."""

import pytest
from pydantic import ValidationError

from src.common.validation import IncomeTaxInput, PropertyTaxInput, TaxProfile


def test_income_input_rejects_negative():
    with pytest.raises(ValidationError):
        IncomeTaxInput(tax_year=2024, income=-1, rrsp=0)


def test_property_input_requires_rolls():
    with pytest.raises(ValidationError):
        PropertyTaxInput(tax_year=2024, roll_numbers=[])


def test_profile_defaults():
    profile = TaxProfile()
    assert profile.display_name == "Guest"
    assert profile.province == "Ontario"
