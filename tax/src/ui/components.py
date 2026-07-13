"""Reusable Streamlit UI helpers."""

from __future__ import annotations

from typing import Any, Iterable

import streamlit as st

from src.ai.service import Insight
from src.common.formatting import fmt_money, fmt_pct
from src.common.paths import ui_css_path
from src.services.session import WORKFLOW_STEPS, completion_status, workflow_index


def inject_styles() -> None:
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap" rel="stylesheet">
        """,
        unsafe_allow_html=True,
    )
    css_path = ui_css_path()
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_header(subtitle: str | None = None) -> None:
    st.markdown(
        f"""
        <div class="otp-hero">
            <p class="otp-eyebrow">Ontario · Portfolio Demo</p>
            <h1 class="otp-brand">TaxForge</h1>
            <p class="otp-tagline">{subtitle or "AI-assisted property &amp; personal income tax estimation for Ontario."}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_rail(current: str | None = None) -> None:
    idx = workflow_index(current)
    status = completion_status()
    done_map = {
        "welcome": True,
        "dashboard": True,
        "profile": status["profile"],
        "income": status["income"],
        "property": status["property"],
        "ai_review": status["ai_review"],
        "summary": status["income"] or status["property"],
    }
    parts = ['<div class="otp-rail" role="navigation" aria-label="Workflow">']
    for i, (key, label) in enumerate(WORKFLOW_STEPS):
        classes = ["otp-rail-step"]
        if i == idx:
            classes.append("is-current")
        if done_map.get(key):
            classes.append("is-done")
        parts.append(
            f'<div class="{" ".join(classes)}"><span class="otp-rail-index">{i + 1}</span>'
            f"<span>{label}</span></div>"
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def empty_state(title: str, body: str, cta: str | None = None) -> None:
    st.markdown(
        f"""
        <div class="otp-empty" role="status">
            <h3>{title}</h3>
            <p>{body}</p>
            {f'<p class="otp-empty-cta">{cta}</p>' if cta else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def error_banner(message: str) -> None:
    st.markdown(
        f'<div class="otp-error" role="alert">{message}</div>',
        unsafe_allow_html=True,
    )


def insight_cards(insights: Iterable[Insight] | Iterable[dict[str, Any]], limit: int = 6) -> None:
    items = list(insights)[:limit]
    if not items:
        empty_state("No insights yet", "Run a calculation first, then open AI Review.")
        return

    for item in items:
        if isinstance(item, Insight):
            kind, title, detail, priority = item.kind, item.title, item.detail, item.priority
        else:
            kind = item.get("kind", "summary")
            title = item.get("title", "Insight")
            detail = item.get("detail", "")
            priority = item.get("priority", 2)

        st.markdown(
            f"""
            <div class="otp-insight priority-{priority}">
                <div class="otp-insight-meta">
                    <span class="otp-chip">{kind.replace('_', ' ')}</span>
                    <span class="otp-priority">P{priority}</span>
                </div>
                <h4>{title}</h4>
                <p>{detail}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def metric_row(metrics: list[tuple[str, str]]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, value)


def income_result_panel(result: dict[str, Any]) -> None:
    metric_row(
        [
            ("Total tax", fmt_money(result["total_tax"])),
            ("Net income", fmt_money(result.get("net_income", 0))),
            ("Effective rate", fmt_pct(result.get("effective_rate", 0) * 100)),
            ("Marginal rate", fmt_pct(result.get("marginal_rate", 0) * 100)),
        ]
    )
    st.markdown("#### Breakdown")
    c1, c2, c3 = st.columns(3)
    c1.write(f"**Federal:** {fmt_money(result['federal_tax'])}")
    c2.write(f"**Ontario:** {fmt_money(result['ontario_tax'])}")
    c3.write(f"**Taxable income:** {fmt_money(result['taxable_income'])}")


def render_footer() -> None:
    st.markdown(
        """
        <div class="otp-footer">
            TaxForge · Built with Python &amp; Streamlit · Estimates for portfolio/demo use only — not tax advice.
        </div>
        """,
        unsafe_allow_html=True,
    )
