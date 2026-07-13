# Testing strategy

## Goals

Demonstrate testing readiness without shipping hollow or snapshot-junk tests. Every test asserts real domain behaviour.

## Pyramid

| Layer | Location | What we cover |
|-------|----------|----------------|
| Unit | `tax/tests/test_income_calculator.py`, `test_property.py`, `test_validation.py`, `test_ai_service.py` | Brackets/deductions, roll validation, Pydantic rules, heuristic insights |
| API / integration | `tax/tests/test_api.py` | FastAPI routes via `TestClient`, validation errors (`422`) |
| Manual | Streamlit UI | Workflow, empty/loading states, PDF download |

## Running tests

```bash
pip install -r requirements.txt
pytest
pytest --cov=src --cov-report=term-missing   # from tax/ with PYTHONPATH set via pytest.ini
```

`pytest.ini` sets `pythonpath = tax` and `testpaths = tax/tests`.

## Integration test plan (manual / CI stretch)

1. **Income happy path** — income `100000`, RRSP `8000` → metrics render, pie chart loads, PDF downloads.
2. **Property happy path** — roll `1936040010123450000` → table + stacked bar + PDF.
3. **Invalid roll** — warning shown, empty results stay graceful.
4. **AI review** — without API key, heuristic provider; with key, provider may be `openai`.
5. **API parity** — same inputs to `/api/v1/income/estimate` match Streamlit calculator within rounding.
6. **Security** — POST negative income → `422`; oversized roll list rejected by validation.

## What we intentionally do not fake

- No UI screenshot tests with empty asserts
- No mocked coverage of unreachable branches just to inflate metrics
- LLM calls are not required in CI; heuristics are the guaranteed path

## Future hardening

- Contract tests sharing JSON fixtures between UI session fixtures and API
- Property-based tests for bracket math (`hypothesis`)
- Playwright smoke for the Streamlit workflow in CI
