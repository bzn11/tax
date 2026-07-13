"""API smoke tests for TaxForge REST endpoints."""

from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_income_estimate_endpoint():
    response = client.post(
        "/api/v1/income/estimate",
        json={
            "tax_year": 2024,
            "income": 100000,
            "rrsp": 5000,
            "other_deductions": 0,
            "filing_status": "single",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["taxable_income"] == 95000
    assert body["total_tax"] > 0


def test_property_estimate_endpoint():
    response = client.post(
        "/api/v1/property/estimate",
        json={
            "tax_year": 2024,
            "include_education": True,
            "roll_numbers": ["1936040010123450000"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["property_count"] == 1


def test_income_estimate_validation_error():
    response = client.post(
        "/api/v1/income/estimate",
        json={"tax_year": 2024, "income": -5, "rrsp": 0},
    )
    assert response.status_code == 422
