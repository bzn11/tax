"""Session-scoped profile and workflow state helpers for Streamlit."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.common.validation import TaxProfile

WORKFLOW_STEPS = [
    ("welcome", "Welcome"),
    ("dashboard", "Dashboard"),
    ("profile", "Tax Profile"),
    ("income", "Income"),
    ("property", "Property"),
    ("ai_review", "AI Review"),
    ("summary", "Summary"),
]


def init_session() -> None:
    defaults: dict[str, Any] = {
        "page": "welcome",
        "profile": TaxProfile().model_dump(),
        "income_result": None,
        "income_input": None,
        "property_result": None,
        "property_input": None,
        "ai_income_review": None,
        "ai_property_review": None,
        "authenticated": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_profile() -> dict[str, Any]:
    return st.session_state.get("profile") or TaxProfile().model_dump()


def save_profile(data: dict[str, Any]) -> TaxProfile:
    profile = TaxProfile(**data)
    st.session_state.profile = profile.model_dump()
    return profile


def navigate(page: str) -> None:
    st.session_state.page = page


def workflow_index(page: str | None = None) -> int:
    current = page or st.session_state.get("page", "welcome")
    for idx, (key, _) in enumerate(WORKFLOW_STEPS):
        if key == current:
            return idx
    return 0


def completion_status() -> dict[str, bool]:
    profile = get_profile()
    return {
        "profile": bool(profile.get("display_name") and profile.get("display_name") != "Guest")
        or st.session_state.get("authenticated", False),
        "income": st.session_state.get("income_result") is not None,
        "property": st.session_state.get("property_result") is not None,
        "ai_review": bool(
            st.session_state.get("ai_income_review") or st.session_state.get("ai_property_review")
        ),
    }
