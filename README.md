# TaxForge — Ontario Tax Estimation Portal

AI-assisted property and personal income tax estimation for Ontario. Built as a portfolio-ready Python product with a Streamlit workspace, FastAPI REST layer, PDF reports, heuristic (+ optional LLM) insights, and automated tests.

> **Not tax advice.** Figures use simplified brackets and sample MPAC/municipal rate data for demonstration only.

---

## Features

- **Guided workflow:** Welcome → Dashboard → Tax Profile → Income / Property → AI Review → Summary & PDF export
- **Income tax engine:** Year-aware federal + Ontario brackets, RRSP/other deductions, effective & marginal rates
- **Property tax engine:** Roll-number lookup against sample assessments and municipal/education rates
- **AI insights:** Offline heuristic recommendations; optional OpenAI-enhanced summaries via `OPENAI_API_KEY`
- **REST API:** FastAPI endpoints sharing the same domain services as the UI
- **PDF export:** Client-ready income and property reports (ReportLab)
- **Validation & tests:** Pydantic models + pytest coverage for calculators, AI service, and API

---

## Quick start

```bash
# From repository root
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # optional — add OPENAI_API_KEY for LLM summaries

cd tax
streamlit run app.py
```

Streamlit UI: [http://localhost:8501](http://localhost:8501)

### REST API (optional)

```bash
cd tax
uvicorn api:app --reload --port 8000
```

OpenAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Tests

```bash
# From repository root
pytest
```

---

## Demo data

| Roll number           | Address            | City        |
|-----------------------|--------------------|-------------|
| `1936040010123450000` | 123 Queen St W     | Toronto     |
| `1901010010012340000` | 45 Elgin St        | Ottawa      |
| `2105010010098760000` | 88 Hurontario St   | Mississauga |

---

## Project structure

```
tax/                          # repository root
├── README.md
├── ARCHITECTURE.md
├── TESTING.md
├── requirements.txt
├── .env.example
├── pytest.ini
└── tax/                      # runnable application package
    ├── app.py                # Streamlit entry
    ├── api.py                # FastAPI entry
    ├── data/                 # Sample MPAC + tax rate CSVs
    ├── outputs/              # Generated PDFs
    ├── src/
    │   ├── ai/               # Reusable AI insight service
    │   ├── common/           # Formatting, paths, validation
    │   ├── incometax/        # Brackets, calculator, PDF
    │   ├── propertytax/      # Assessments, rates, service, PDF
    │   ├── services/         # Session / profile helpers
    │   └── ui/               # Styles, components, views
    └── tests/
```

---

## Environment variables

| Variable         | Required | Description                                      |
|------------------|----------|--------------------------------------------------|
| `OPENAI_API_KEY` | No       | Enables LLM-enhanced AI summaries                |
| `OPENAI_MODEL`   | No       | Defaults to `gpt-4o-mini`                        |
| `APP_OWNER_NAME` | No       | Display/PDF branding override                    |

Copy `.env.example` → `.env`. Without an API key, heuristic AI still works fully offline.

---

## User workflow

1. **Welcome** — session profile (guest or named)
2. **Dashboard** — completion status + personalized tips
3. **Tax Profile** — municipality, employment, ownership, goals
4. **Income & Deductions** — calculate federal/Ontario estimate
5. **Property Tax** — estimate from roll numbers
6. **AI Review** — deduction ideas, missing-info flags, plain-language summary
7. **Summary & Export** — metrics + downloadable PDFs

---

## API overview

| Method | Path                              | Purpose                    |
|--------|-----------------------------------|----------------------------|
| GET    | `/health`                         | Liveness                   |
| POST   | `/api/v1/income/estimate`         | Income tax calculation     |
| POST   | `/api/v1/property/estimate`       | Property tax calculation   |
| POST   | `/api/v1/ai/income-review`        | AI review (income)         |
| POST   | `/api/v1/ai/property-review`      | AI review (property)       |
| POST   | `/api/v1/ai/recommendations`      | Profile-based tips         |
| POST   | `/api/v1/reports/income`          | Generate income PDF        |
| POST   | `/api/v1/reports/property`        | Generate property PDF      |

See [ARCHITECTURE.md](ARCHITECTURE.md) and [TESTING.md](TESTING.md) for deeper detail.

---

## Security notes

- Inputs validated with Pydantic (ranges, roll-number limits, employment enums)
- PDF paths sandboxed under `tax/outputs/` (path traversal rejected)
- API CORS limited to local Streamlit origins by default
- No secrets committed; use `.env` locally
- Session profile is in-memory only (Streamlit session state) — suitable for demos, not multi-user auth

---

## License / attribution

Portfolio / educational project. Sample assessment and rate figures are illustrative.
