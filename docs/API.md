# API reference

Base URL (local): `http://localhost:8000`

Interactive docs: `/docs` · ReDoc: `/redoc`

All money figures are JSON numbers (not pre-formatted strings).

---

## `GET /health`

Liveness probe.

**Response**

```json
{ "status": "ok", "service": "taxforge-api" }
```

---

## `POST /api/v1/income/estimate`

**Body**

```json
{
  "tax_year": 2024,
  "income": 100000,
  "rrsp": 5000,
  "other_deductions": 0,
  "filing_status": "single"
}
```

**Response** includes `federal_tax`, `ontario_tax`, `total_tax`, `effective_rate`, `marginal_rate`, `net_income`, etc.

---

## `POST /api/v1/property/estimate`

**Body**

```json
{
  "tax_year": 2024,
  "include_education": true,
  "roll_numbers": ["1936040010123450000"]
}
```

**Response**

```json
{
  "tax_year": 2024,
  "results": [ { "address": "...", "estimated_tax": 7258.0 } ],
  "warnings": [],
  "total_tax": 7258.0,
  "property_count": 1
}
```

---

## `POST /api/v1/ai/income-review`

**Body**

```json
{
  "calculation": { "income": 100000, "rrsp": 0, "total_tax": 24000, "effective_rate": 0.24, "marginal_rate": 0.43, "tax_year": 2024 },
  "profile": { "display_name": "Alex", "has_rrsp": true, "employment_type": "employed" }
}
```

---

## `POST /api/v1/ai/property-review`

Same shape with a property `calculation` payload (output of the property estimate endpoint).

---

## `POST /api/v1/ai/recommendations`

Accepts a `TaxProfile` body; returns prioritized dashboard insights.

---

## `POST /api/v1/reports/income` · `POST /api/v1/reports/property`

Generate PDFs under `tax/outputs/` and return the filename. Prefer the Streamlit download buttons for end-user export UX.

---

## Errors

| Code | Meaning |
|------|---------|
| 400  | Semantic request issue (e.g. empty calculation) |
| 422  | Pydantic validation failure |
| 500  | Unexpected server error |
