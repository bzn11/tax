"""Unit tests for AI heuristic review service."""

from src.ai.service import TaxAIService


def test_income_review_flags_missing_rrsp():
    service = TaxAIService(api_key="")
    result = {
        "tax_year": 2024,
        "income": 100_000,
        "rrsp": 0,
        "other_deductions": 0,
        "total_tax": 24_000,
        "effective_rate": 0.24,
        "marginal_rate": 0.43,
        "rrsp_estimated_savings": 0,
    }
    review = service.review_income(result, profile={"has_rrsp": True, "employment_type": "employed"})
    assert review.provider == "heuristic"
    assert review.insights
    assert any(i.kind == "missing_info" for i in review.insights)


def test_dashboard_recommendations_for_homeowner():
    service = TaxAIService(api_key="")
    tips = service.dashboard_recommendations(
        {
            "display_name": "Alex",
            "owns_property": True,
            "municipality": "Toronto",
            "has_rrsp": True,
            "employment_type": "employed",
            "goals": ["reduce_tax"],
        }
    )
    assert tips
    assert any("Alex" in t.detail or "Alex" in t.title for t in tips)


def test_property_review_empty_results():
    service = TaxAIService(api_key="")
    review = service.review_property({"results": [], "warnings": [], "total_tax": 0, "tax_year": 2024})
    assert "Unable" in review.summary or review.missing_fields
