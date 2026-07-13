"""
TaxForge — Ontario Tax Estimation Portal

Run from the `tax/` directory:
    streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure `src.*` imports resolve when launched via Streamlit
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.common.paths import ensure_outputs_dir
from src.services.session import init_session, navigate
from src.ui.components import inject_styles, render_footer, render_header, render_workflow_rail
from src.ui.views import (
    page_ai_review,
    page_dashboard,
    page_income,
    page_profile,
    page_property,
    page_summary,
    page_welcome,
)

ensure_outputs_dir()

st.set_page_config(
    page_title="TaxForge | Ontario Tax Estimation",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()
init_session()

PAGE_LABELS = {
    "welcome": "Welcome",
    "dashboard": "Dashboard",
    "profile": "Tax Profile",
    "income": "Income & Deductions",
    "property": "Property Tax",
    "ai_review": "AI Review",
    "summary": "Summary & Export",
}

with st.sidebar:
    st.markdown("### TaxForge")
    st.caption("Ontario tax estimation workspace")
    st.markdown("---")
    selection = st.radio(
        "Navigate",
        options=list(PAGE_LABELS.keys()),
        format_func=lambda key: PAGE_LABELS[key],
        index=list(PAGE_LABELS.keys()).index(st.session_state.page)
        if st.session_state.page in PAGE_LABELS
        else 0,
        label_visibility="collapsed",
    )
    if selection != st.session_state.page:
        navigate(selection)
        st.rerun()

    st.markdown("---")
    st.markdown(
        """
        **Suggested flow**  
        1. Welcome / profile  
        2. Income & deductions  
        3. Property tax  
        4. AI review  
        5. Summary & PDF export
        """
    )
    st.caption("Demo roll: `1936040010123450000`")

render_header()
render_workflow_rail(st.session_state.page)

PAGES = {
    "welcome": page_welcome,
    "dashboard": page_dashboard,
    "profile": page_profile,
    "income": page_income,
    "property": page_property,
    "ai_review": page_ai_review,
    "summary": page_summary,
}

PAGES[st.session_state.page]()
render_footer()
