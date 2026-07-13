# Architecture

TaxForge keeps a **domain-first** layout: calculators, AI, and PDF generation live in services; Streamlit and FastAPI are thin adapters.

```
┌─────────────────┐     ┌─────────────────┐
│  Streamlit UI   │     │   FastAPI REST  │
│  (app.py/views) │     │    (api.py)     │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌──────────────────────────────────────────┐
│     Validation (Pydantic) + Session      │
└──────────────────────────────────────────┘
         │
         ├──────────────┬──────────────────┐
         ▼              ▼                  ▼
┌─────────────┐ ┌──────────────┐ ┌─────────────────┐
│ Income Tax  │ │ Property Tax │ │ TaxAIService    │
│ calculator  │ │ service      │ │ (heuristic/LLM) │
└──────┬──────┘ └──────┬───────┘ └────────┬────────┘
       │               │                  │
       ▼               ▼                  ▼
┌─────────────┐ ┌──────────────┐ ┌─────────────────┐
│ PDF report  │ │ CSV data     │ │ Insights / tips │
└─────────────┘ └──────────────┘ └─────────────────┘
```

## Design principles

1. **Preserve domain modules** — original `incometax` / `propertytax` packages remain the source of truth.
2. **No duplicated math** — UI and API call the same service functions.
3. **AI as a service** — `TaxAIService` is reusable from UI, API, and tests; LLM is optional.
4. **Fail closed / degrade gracefully** — invalid rolls become warnings; LLM failures fall back to heuristics.
5. **Portfolio honesty** — disclaimers in UI and PDFs; brackets are simplified on purpose.

## Data

| File | Role |
|------|------|
| `tax/data/mpac.csv` | Sample assessment roll → CVA / municipality |
| `tax/data/tr.csv` | Municipal + education rates by year |

Paths resolve via `src.common.paths` so the app works regardless of CWD (as long as package root is correct).

## Session model

Streamlit `st.session_state` holds:

- `profile` — personalized recommendations
- `income_result` / `property_result` — last calculations
- `ai_*_review` — cached AI payloads
- `page` — workflow navigation

There is **no persistent database** in this demo. A natural next step for production would be Postgres + auth (Clerk/Auth.js/etc.) storing profiles and report history.

## Income tax model

- Year-aware bracket tables in `src/incometax/brackets.py`
- Progressive application in `apply_brackets`
- Outputs include effective rate, combined marginal rate, and rough RRSP savings

## Property tax model

1. Normalize / validate roll number  
2. Select assessment for tax year (else latest)  
3. Load matching municipal rates  
4. `tax = CVA × (municipal + education)`

## AI layer

`src/ai/service.py`:

- Deterministic insights (deductions, missing fields, deadlines, explanations)
- Optional OpenAI chat completion to rewrite the summary only
- Never blocks the app if the API is unavailable

## PDF generation

ReportLab canvases write to `tax/outputs/` through `safe_output_path`, which strips directory components and rejects traversal.
