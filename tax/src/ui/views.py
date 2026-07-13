"""Page/view renderers for the TaxForge workflow."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
from pydantic import ValidationError

from src.ai.service import get_ai_service
from src.common.formatting import fmt_money, fmt_rate
from src.common.paths import safe_output_path
from src.common.validation import IncomeTaxInput, PropertyTaxInput
from src.incometax.calculator import calculate_income_tax
from src.incometax.report import generate_income_report
from src.propertytax.report import generate_property_report
from src.propertytax.service import estimate_property_taxes
from src.services.session import get_profile, navigate, save_profile
from src.ui.components import (
    empty_state,
    error_banner,
    income_result_panel,
    insight_cards,
    metric_row,
)


def page_welcome() -> None:
    st.markdown("### Start your tax estimate")
    st.write(
        "TaxForge walks you through a clear workflow: profile → income/property inputs → "
        "AI review → summary & PDF export. Session data stays in your browser tab."
    )

    with st.form("login_form", clear_on_submit=False):
        name = st.text_input("Display name", value=get_profile().get("display_name", "Guest"))
        col1, col2 = st.columns(2)
        with col1:
            continue_guest = st.form_submit_button("Continue as guest", use_container_width=True)
        with col2:
            continue_named = st.form_submit_button("Enter workspace", type="primary", use_container_width=True)

    if continue_guest or continue_named:
        display = "Guest" if continue_guest else (name.strip() or "Guest")
        profile = get_profile()
        profile["display_name"] = display
        save_profile(profile)
        st.session_state.authenticated = True
        navigate("dashboard")
        st.rerun()

    st.caption("No passwords are stored — this is a lightweight session profile for the portfolio demo.")


def page_dashboard() -> None:
    profile = get_profile()
    name = profile.get("display_name", "Guest")
    st.markdown(f"### Welcome, {name}")
    st.write("Your personalized workspace for Ontario tax estimates.")

    status_cols = st.columns(4)
    flags = {
        "Profile": st.session_state.get("authenticated"),
        "Income estimate": st.session_state.get("income_result") is not None,
        "Property estimate": st.session_state.get("property_result") is not None,
        "AI review": bool(
            st.session_state.get("ai_income_review") or st.session_state.get("ai_property_review")
        ),
    }
    for col, (label, done) in zip(status_cols, flags.items()):
        with col:
            st.metric(label, "Done" if done else "Pending")

    ai = get_ai_service()
    tips = ai.dashboard_recommendations(profile)
    st.markdown("#### Personalized recommendations")
    insight_cards(tips, limit=4)

    st.markdown("#### Continue workflow")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Tax profile", use_container_width=True):
        navigate("profile")
        st.rerun()
    if c2.button("Income tax", use_container_width=True):
        navigate("income")
        st.rerun()
    if c3.button("Property tax", use_container_width=True):
        navigate("property")
        st.rerun()
    if c4.button("AI review", use_container_width=True):
        navigate("ai_review")
        st.rerun()


def page_profile() -> None:
    st.markdown("### Tax profile")
    st.write("Personalize deadlines, deduction reminders, and dashboard tips.")
    profile = get_profile()

    with st.form("profile_form"):
        display_name = st.text_input("Display name", value=profile.get("display_name", "Guest"))
        municipality = st.selectbox(
            "Primary municipality",
            ["Toronto", "Ottawa", "Mississauga", "Hamilton", "Other"],
            index=max(
                0,
                ["Toronto", "Ottawa", "Mississauga", "Hamilton", "Other"].index(
                    profile.get("municipality", "Toronto")
                )
                if profile.get("municipality", "Toronto")
                in ["Toronto", "Ottawa", "Mississauga", "Hamilton", "Other"]
                else 0,
            ),
        )
        employment = st.selectbox(
            "Employment type",
            ["employed", "self_employed", "student", "retired"],
            index=["employed", "self_employed", "student", "retired"].index(
                profile.get("employment_type", "employed")
            ),
        )
        owns_property = st.checkbox("I own property in Ontario", value=bool(profile.get("owns_property")))
        has_rrsp = st.checkbox("I contribute to an RRSP", value=bool(profile.get("has_rrsp", True)))
        goals = st.multiselect(
            "Goals",
            options=["reduce_tax", "buy_home", "retire_soon", "organize_records"],
            default=profile.get("goals") or [],
            format_func=lambda g: g.replace("_", " ").title(),
        )
        submitted = st.form_submit_button("Save profile", type="primary")

    if submitted:
        try:
            save_profile(
                {
                    "display_name": display_name,
                    "province": "Ontario",
                    "municipality": municipality,
                    "owns_property": owns_property,
                    "has_rrsp": has_rrsp,
                    "employment_type": employment,
                    "goals": goals,
                }
            )
            st.session_state.authenticated = True
            st.success("Profile saved.")
        except ValidationError as exc:
            error_banner(str(exc))

    c1, c2 = st.columns(2)
    if c1.button("Back to dashboard"):
        navigate("dashboard")
        st.rerun()
    if c2.button("Next: Income sources", type="primary"):
        navigate("income")
        st.rerun()


def page_income() -> None:
    st.markdown("### Income sources & deductions")
    st.write("Estimate federal + Ontario personal income tax with RRSP and other deductions.")

    with st.form("income_form"):
        tax_year = st.selectbox("Tax year", [2024, 2025, 2026], index=0)
        income = st.number_input("Annual income ($)", min_value=0.0, step=1000.0, value=0.0)
        rrsp = st.number_input("RRSP contribution ($)", min_value=0.0, step=500.0, value=0.0)
        other = st.number_input(
            "Other deductions ($)",
            min_value=0.0,
            step=100.0,
            value=0.0,
            help="Simplified catch-all for demo purposes (e.g. childcare, union dues).",
        )
        submitted = st.form_submit_button("Calculate income tax", type="primary")

    if submitted:
        try:
            payload = IncomeTaxInput(
                tax_year=int(tax_year),
                income=float(income),
                rrsp=float(rrsp),
                other_deductions=float(other),
            )
            with st.spinner("Calculating brackets and effective rates…"):
                result = calculate_income_tax(
                    payload.income,
                    payload.rrsp,
                    payload.other_deductions,
                    tax_year=payload.tax_year,
                )
            st.session_state.income_input = payload.model_dump()
            st.session_state.income_result = result
            st.session_state.ai_income_review = None
            st.success("Income tax calculated.")
        except ValidationError as exc:
            error_banner(f"Validation error: {exc.errors()[0]['msg']}")
            return

    result = st.session_state.get("income_result")
    if not result:
        empty_state(
            "No income estimate yet",
            "Enter income and deductions, then calculate to see metrics and charts.",
            "Tip: try income 100000 and RRSP 8000.",
        )
    else:
        income_result_panel(result)
        fig = px.pie(
            names=["Federal", "Ontario", "Net income"],
            values=[
                result["federal_tax"],
                result["ontario_tax"],
                max(result.get("net_income", 0), 0),
            ],
            title="Where gross income goes",
            color_discrete_sequence=["#0d5c63", "#c45c26", "#b7d7c8"],
        )
        fig.update_layout(margin=dict(t=48, b=16, l=16, r=16))
        st.plotly_chart(fig, use_container_width=True)

        if result.get("rrsp", 0) > 0:
            st.info(
                f"Estimated RRSP tax savings at marginal rate: "
                f"{fmt_money(result.get('rrsp_estimated_savings', 0))}."
            )

    c1, c2, c3 = st.columns(3)
    if c1.button("Tax profile"):
        navigate("profile")
        st.rerun()
    if c2.button("Property tax"):
        navigate("property")
        st.rerun()
    if c3.button("AI review", type="primary"):
        navigate("ai_review")
        st.rerun()


def page_property() -> None:
    st.markdown("### Property tax estimate")
    st.write("Look up sample MPAC assessments and municipal + education rates by roll number.")

    with st.form("property_form"):
        rolls_input = st.text_area(
            "Ontario roll number(s)",
            placeholder="One per line — demo roll: 1936040010123450000",
            height=100,
        )
        include_education = st.checkbox("Include education tax", value=True)
        tax_year = st.number_input("Tax year", min_value=2020, max_value=2026, value=2024)
        submitted = st.form_submit_button("Calculate property tax", type="primary")

    if submitted:
        rolls = [r.strip() for r in rolls_input.splitlines() if r.strip()]
        try:
            payload = PropertyTaxInput(
                tax_year=int(tax_year),
                include_education=include_education,
                roll_numbers=rolls,
            )
        except ValidationError as exc:
            error_banner(exc.errors()[0]["msg"])
            return

        with st.spinner("Loading assessments and tax rates…"):
            outcome = estimate_property_taxes(
                payload.roll_numbers,
                tax_year=payload.tax_year,
                include_education=payload.include_education,
            )
        st.session_state.property_input = payload.model_dump()
        st.session_state.property_result = outcome
        st.session_state.ai_property_review = None

        if outcome["warnings"]:
            st.warning("\n".join(outcome["warnings"]))
        if outcome["results"]:
            st.success(f"Calculated {outcome['property_count']} property(ies).")
        else:
            error_banner("No properties could be calculated. Check roll numbers and sample data.")

    outcome = st.session_state.get("property_result")
    if not outcome or not outcome.get("results"):
        empty_state(
            "No property estimate yet",
            "Enter one or more roll numbers to estimate municipal and education tax.",
            "Demo roll number: 1936040010123450000",
        )
    else:
        display_rows = []
        for r in outcome["results"]:
            display_rows.append(
                {
                    "Roll Number": r["roll_number"],
                    "Address": r["address"],
                    "Municipality": r["municipality"],
                    "Assessment Year": r["assessment_year"],
                    "Assessment Value": fmt_money(r["assessment_value"]),
                    "Municipal Rate": fmt_rate(r["municipal_rate"]),
                    "Education Rate": fmt_rate(r["education_rate"]),
                    "Estimated Tax": fmt_money(r["estimated_tax"]),
                }
            )
        st.dataframe(pd.DataFrame(display_rows), use_container_width=True)
        metric_row(
            [
                ("Properties", str(outcome["property_count"])),
                ("Total estimated tax", fmt_money(outcome["total_tax"])),
                ("Tax year", str(outcome["tax_year"])),
            ]
        )

        chart_data = pd.DataFrame(
            [
                {
                    "Roll": r["roll_number"][-6:],
                    "Municipal": r["municipal_tax"],
                    "Education": r["education_tax"],
                }
                for r in outcome["results"]
            ]
        )
        fig = px.bar(
            chart_data,
            x="Roll",
            y=["Municipal", "Education"],
            title="Tax breakdown by roll (last 6 digits)",
            labels={"value": "Tax ($)", "variable": "Component"},
            color_discrete_sequence=["#0d5c63", "#c45c26"],
        )
        fig.update_layout(margin=dict(t=48, b=16, l=16, r=16))
        st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    if c1.button("Income tax"):
        navigate("income")
        st.rerun()
    if c2.button("AI review", type="primary"):
        navigate("ai_review")
        st.rerun()


def page_ai_review() -> None:
    st.markdown("### AI review")
    st.write(
        "Heuristic insights always work offline. If `OPENAI_API_KEY` is set, summaries can be "
        "enhanced with an LLM."
    )

    profile = get_profile()
    ai = get_ai_service()
    has_income = st.session_state.get("income_result") is not None
    has_property = bool((st.session_state.get("property_result") or {}).get("results"))

    if not has_income and not has_property:
        empty_state(
            "Nothing to review yet",
            "Calculate an income or property estimate first, then return here.",
            "Go to Income or Property from the sidebar.",
        )
        return

    tabs = []
    if has_income:
        tabs.append("Income")
    if has_property:
        tabs.append("Property")
    chosen = st.tabs(tabs)

    tab_idx = 0
    if has_income:
        with chosen[tab_idx]:
            if st.button("Generate income AI review", type="primary", key="ai_income_btn"):
                with st.spinner("Analyzing income estimate…"):
                    review = ai.review_income(st.session_state.income_result, profile=profile)
                    st.session_state.ai_income_review = review.as_dict()
            review = st.session_state.get("ai_income_review")
            if review:
                st.info(f"Provider: {review.get('provider', 'heuristic')}")
                st.markdown(f"**Summary:** {review['summary']}")
                if review.get("missing_fields"):
                    st.warning("Missing information: " + ", ".join(review["missing_fields"]))
                insight_cards(review.get("insights", []))
            else:
                empty_state("No income review yet", "Click the button above to generate insights.")
        tab_idx += 1

    if has_property:
        with chosen[tab_idx]:
            if st.button("Generate property AI review", type="primary", key="ai_property_btn"):
                with st.spinner("Analyzing property estimate…"):
                    review = ai.review_property(st.session_state.property_result, profile=profile)
                    st.session_state.ai_property_review = review.as_dict()
            review = st.session_state.get("ai_property_review")
            if review:
                st.info(f"Provider: {review.get('provider', 'heuristic')}")
                st.markdown(f"**Summary:** {review['summary']}")
                if review.get("missing_fields"):
                    st.warning("Missing information: " + ", ".join(review["missing_fields"]))
                insight_cards(review.get("insights", []))
            else:
                empty_state("No property review yet", "Click the button above to generate insights.")

    if st.button("Go to summary & export", type="primary"):
        navigate("summary")
        st.rerun()


def page_summary() -> None:
    st.markdown("### Tax summary & export")
    profile = get_profile()
    income = st.session_state.get("income_result")
    property_result = st.session_state.get("property_result")
    ai_income = st.session_state.get("ai_income_review")
    ai_property = st.session_state.get("ai_property_review")

    if not income and not (property_result and property_result.get("results")):
        empty_state(
            "No results to export",
            "Complete an income or property calculation before generating reports.",
        )
        return

    if income:
        st.markdown("#### Income tax")
        income_result_panel(income)
        if ai_income:
            st.caption(ai_income.get("summary", ""))

        if st.button("Generate income PDF", type="primary", key="pdf_income"):
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = safe_output_path(f"income_report_{stamp}.pdf")
            generate_income_report(
                income,
                str(path),
                client_name=profile.get("display_name"),
                ai_summary=(ai_income or {}).get("summary"),
            )
            st.download_button(
                "Download income tax report (PDF)",
                data=path.read_bytes(),
                file_name="income_tax_report.pdf",
                mime="application/pdf",
                key=f"dl_income_{stamp}",
            )

    if property_result and property_result.get("results"):
        st.markdown("#### Property tax")
        metric_row(
            [
                ("Properties", str(property_result["property_count"])),
                ("Total tax", fmt_money(property_result["total_tax"])),
            ]
        )
        if ai_property:
            st.caption(ai_property.get("summary", ""))

        if st.button("Generate property PDF", type="primary", key="pdf_property"):
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = safe_output_path(f"property_report_{stamp}.pdf")
            generate_property_report(
                property_result["results"],
                str(path),
                client_name=profile.get("display_name"),
                ai_summary=(ai_property or {}).get("summary"),
                total_tax=property_result["total_tax"],
            )
            st.download_button(
                "Download property tax report (PDF)",
                data=path.read_bytes(),
                file_name="property_tax_report.pdf",
                mime="application/pdf",
                key=f"dl_property_{stamp}",
            )

    st.divider()
    if st.button("Back to dashboard"):
        navigate("dashboard")
        st.rerun()
