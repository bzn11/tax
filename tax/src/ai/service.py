"""
Reusable AI tax insight service.

Uses deterministic heuristics by default (no API key required).
Optionally enhances narratives via OpenAI when OPENAI_API_KEY is set.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Literal

from dotenv import load_dotenv

load_dotenv()

InsightKind = Literal[
    "deduction",
    "filing",
    "missing_info",
    "optimization",
    "deadline",
    "summary",
    "explanation",
]


@dataclass
class Insight:
    kind: InsightKind
    title: str
    detail: str
    priority: int = 2  # 1 = high, 2 = medium, 3 = low


@dataclass
class AIReviewResult:
    summary: str
    insights: list[Insight] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    provider: str = "heuristic"

    def as_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "provider": self.provider,
            "missing_fields": self.missing_fields,
            "insights": [
                {
                    "kind": i.kind,
                    "title": i.title,
                    "detail": i.detail,
                    "priority": i.priority,
                }
                for i in self.insights
            ],
        }


class TaxAIService:
    """Central AI layer for deduction tips, explanations, and reviews."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or ""
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    @property
    def llm_enabled(self) -> bool:
        return bool(self.api_key.strip())

    def review_income(
        self,
        result: dict[str, Any],
        *,
        profile: dict[str, Any] | None = None,
    ) -> AIReviewResult:
        profile = profile or {}
        insights: list[Insight] = []
        missing: list[str] = []

        income = float(result.get("income", 0))
        rrsp = float(result.get("rrsp", 0))
        other = float(result.get("other_deductions", 0))
        effective = float(result.get("effective_rate", 0))
        marginal = float(result.get("marginal_rate", 0))
        year = result.get("tax_year", 2024)

        if income <= 0:
            missing.append("annual income")
        if profile.get("has_rrsp") and rrsp <= 0:
            missing.append("RRSP contribution (profile indicates RRSP use)")
            insights.append(
                Insight(
                    "missing_info",
                    "RRSP contribution not entered",
                    "Your profile suggests you use an RRSP, but contribution is $0. "
                    "Entering contributions can reduce taxable income.",
                    priority=1,
                )
            )

        # Deduction suggestions
        rough_rrsp_room = max(0.0, min(income * 0.18, 31_560))
        if rrsp < rough_rrsp_room * 0.5 and income >= 40_000:
            insights.append(
                Insight(
                    "deduction",
                    "Consider maximizing RRSP room",
                    f"Approx. annual RRSP room for this income is near "
                    f"${rough_rrsp_room:,.0f} (18% of income, capped). "
                    f"You entered ${rrsp:,.0f}. At a ~{marginal * 100:.0f}% marginal rate, "
                    f"additional contributions may lower current-year tax.",
                    priority=1,
                )
            )

        if profile.get("employment_type") == "self_employed" and other <= 0:
            insights.append(
                Insight(
                    "deduction",
                    "Self-employment expense checklist",
                    "Self-employed filers often miss home-office, vehicle, professional fees, "
                    "and equipment deductions. Capture eligible expenses under Other deductions "
                    "or track them separately before filing.",
                    priority=1,
                )
            )

        if profile.get("employment_type") == "employed":
            insights.append(
                Insight(
                    "filing",
                    "Employment filing reminder",
                    "Confirm T4 slips, union dues, and employment expenses (form T2200) "
                    f"before filing your {year} return.",
                    priority=2,
                )
            )

        if effective > 0.28:
            insights.append(
                Insight(
                    "optimization",
                    "Higher effective tax rate detected",
                    f"Your effective rate is about {effective * 100:.1f}%. "
                    "Strategies like RRSP contributions, charitable donations, or income timing "
                    "may help — discuss with a CPA for your situation.",
                    priority=2,
                )
            )
        elif income > 0 and rrsp == 0 and other == 0:
            insights.append(
                Insight(
                    "optimization",
                    "No deductions applied",
                    "Adding eligible deductions typically lowers taxable income. "
                    "Start with RRSP/FHSA contributions if available.",
                    priority=2,
                )
            )

        insights.append(
            Insight(
                "deadline",
                "Typical filing deadline",
                f"Most individuals file by April 30 for the {year} tax year. "
                "Self-employed individuals often have until mid-June for the return "
                "(balances owing usually still due April 30).",
                priority=3,
            )
        )

        insights.append(
            Insight(
                "explanation",
                "How this estimate works",
                "Tax is applied progressively across federal and Ontario brackets on taxable "
                "income (income minus deductions). This tool uses a simplified model for "
                "demo purposes and omits credits such as BPA, tuition, and medical.",
                priority=3,
            )
        )

        summary = (
            f"For {year}, estimated tax is ${result.get('total_tax', 0):,.2f} on "
            f"${income:,.2f} income "
            f"(effective {effective * 100:.1f}%, marginal ~{marginal * 100:.0f}%). "
        )
        if rrsp > 0:
            summary += (
                f"RRSP of ${rrsp:,.2f} is estimated to save roughly "
                f"${result.get('rrsp_estimated_savings', 0):,.2f} at the marginal rate. "
            )
        high = [i for i in insights if i.priority == 1]
        if high:
            summary += f"Top focus: {high[0].title}."

        review = AIReviewResult(
            summary=summary.strip(),
            insights=sorted(insights, key=lambda x: x.priority),
            missing_fields=missing,
            provider="heuristic",
        )
        return self._maybe_enhance(review, context="income", payload=result, profile=profile)

    def review_property(
        self,
        payload: dict[str, Any],
        *,
        profile: dict[str, Any] | None = None,
    ) -> AIReviewResult:
        profile = profile or {}
        insights: list[Insight] = []
        missing: list[str] = []
        results = payload.get("results") or []
        warnings = payload.get("warnings") or []
        total = float(payload.get("total_tax", 0))
        year = payload.get("tax_year", 2024)

        if not results:
            missing.append("valid property roll number with assessment data")
            insights.append(
                Insight(
                    "missing_info",
                    "No properties calculated",
                    "Enter a valid 18–20 digit Ontario roll number present in the sample "
                    "assessment data (demo includes 1936040010123450000).",
                    priority=1,
                )
            )

        for w in warnings:
            insights.append(Insight("missing_info", "Data issue", w, priority=1))

        for row in results:
            cva = float(row.get("assessment_value", 0))
            tax = float(row.get("estimated_tax", 0))
            muni = row.get("municipality", "your municipality")
            if cva > 0:
                effective = tax / cva
                insights.append(
                    Insight(
                        "explanation",
                        f"Effective property tax rate — {row.get('address', 'property')}",
                        f"Estimated tax {tax:,.2f} on CVA {cva:,.0f} implies roughly "
                        f"{effective * 100:.2f}% combined municipal"
                        f"{' + education' if payload.get('include_education') else ''} rate "
                        f"in {muni}.",
                        priority=2,
                    )
                )

            insights.append(
                Insight(
                    "filing",
                    "Assessment review tip",
                    "MPAC assessments can be appealed within statutory windows if you believe "
                    "the CVA is incorrect. Compare recent sales of similar homes in the area.",
                    priority=2,
                )
            )

        if profile.get("owns_property") is False and results:
            insights.append(
                Insight(
                    "filing",
                    "Profile note",
                    "Your profile marked you as not owning property, but a property estimate "
                    "was run — update your profile for better personalized reminders.",
                    priority=3,
                )
            )

        insights.append(
            Insight(
                "deadline",
                "Municipal instalments",
                f"Property tax instalment schedules vary by municipality. For {year}, "
                "check your city/town portal for due dates to avoid late penalties.",
                priority=3,
            )
        )

        if results:
            addresses = ", ".join(r.get("address", "property") for r in results[:3])
            summary = (
                f"Estimated {year} property tax total is ${total:,.2f} across "
                f"{len(results)} property(ies) including {addresses}."
            )
        else:
            summary = "Unable to produce a property tax estimate from the current inputs."

        review = AIReviewResult(
            summary=summary,
            insights=sorted(insights, key=lambda x: x.priority),
            missing_fields=missing,
            provider="heuristic",
        )
        return self._maybe_enhance(review, context="property", payload=payload, profile=profile)

    def dashboard_recommendations(self, profile: dict[str, Any]) -> list[Insight]:
        """Personalized home-dashboard reminders from the tax profile."""
        tips: list[Insight] = []
        name = profile.get("display_name") or "there"

        tips.append(
            Insight(
                "deadline",
                f"Welcome back, {name}",
                "Complete your tax profile, then estimate income and/or property tax. "
                "Finish with AI Review for plain-language next steps.",
                priority=2,
            )
        )

        if profile.get("owns_property"):
            tips.append(
                Insight(
                    "filing",
                    "Property tax reminder",
                    f"You indicated property ownership in {profile.get('municipality', 'Ontario')}. "
                    "Run a Property Tax estimate with your roll number to forecast annual cost.",
                    priority=1,
                )
            )
        else:
            tips.append(
                Insight(
                    "deduction",
                    "Renter / non-owner tip",
                    "If you rent, ask whether your municipality offers a tax credit or rebate "
                    "for tenants. Keep rent receipts for provincial credit claims where available.",
                    priority=2,
                )
            )

        if profile.get("has_rrsp"):
            tips.append(
                Insight(
                    "optimization",
                    "RRSP contribution timing",
                    "Contributions made in the first 60 days of the year can often be applied "
                    "to the prior tax year — confirm eligibility before filing.",
                    priority=1,
                )
            )

        if profile.get("employment_type") == "student":
            tips.append(
                Insight(
                    "deduction",
                    "Tuition & education amounts",
                    "Gather T2202 slips. Unused tuition amounts can often be carried forward "
                    "or transferred (within limits).",
                    priority=1,
                )
            )

        if profile.get("employment_type") == "retired":
            tips.append(
                Insight(
                    "filing",
                    "Retirement income checklist",
                    "Include T4A, T4A(P), T4RIF, and T5 slips. Watch OAS clawback thresholds "
                    "if income is high.",
                    priority=1,
                )
            )

        goals = profile.get("goals") or []
        if "reduce_tax" in goals:
            tips.append(
                Insight(
                    "optimization",
                    "Tax reduction focus",
                    "Prioritize RRSP/FHSA contributions and track charitable donations. "
                    "Use AI Review after calculating income tax for tailored suggestions.",
                    priority=1,
                )
            )
        if "buy_home" in goals:
            tips.append(
                Insight(
                    "filing",
                    "Home-buyer planning",
                    "Explore FHSA and Home Buyers' Plan (HBP) rules before withdrawing RRSP "
                    "funds for a down payment.",
                    priority=2,
                )
            )

        return sorted(tips, key=lambda x: x.priority)

    def _maybe_enhance(
        self,
        review: AIReviewResult,
        *,
        context: str,
        payload: dict[str, Any],
        profile: dict[str, Any],
    ) -> AIReviewResult:
        if not self.llm_enabled:
            return review

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            prompt = (
                f"You are a Canadian tax assistant for Ontario. Context: {context}. "
                f"Profile: {profile}. Calculation payload: {payload}. "
                f"Existing summary: {review.summary}. "
                "Rewrite the summary in 2-3 clear sentences for a non-expert. "
                "Do not invent specific dollar credits not present in the data. "
                "Remind the user this is not professional tax advice."
            )
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You write concise, plain-language Canadian tax summaries.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=220,
            )
            text = (response.choices[0].message.content or "").strip()
            if text:
                review.summary = text
                review.provider = "openai"
        except Exception:
            # Fall back silently to heuristics — app must work offline.
            review.provider = "heuristic"

        return review


def get_ai_service() -> TaxAIService:
    return TaxAIService()
