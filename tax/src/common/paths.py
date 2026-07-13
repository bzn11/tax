"""Filesystem path helpers with safe defaults."""

from __future__ import annotations

from pathlib import Path

# `tax/` package root (parent of `src/`)
PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data"
OUTPUTS_DIR = PACKAGE_ROOT / "outputs"
UI_DIR = PACKAGE_ROOT / "src" / "ui"


def ensure_outputs_dir() -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUTS_DIR


def data_path(filename: str) -> Path:
    return DATA_DIR / filename


def ui_css_path() -> Path:
    return UI_DIR / "styles.css"


def safe_output_path(filename: str) -> Path:
    """Resolve a PDF filename under outputs/, rejecting path traversal."""
    ensure_outputs_dir()
    candidate = (OUTPUTS_DIR / Path(filename).name).resolve()
    if not str(candidate).startswith(str(OUTPUTS_DIR.resolve())):
        raise ValueError("Invalid output path")
    return candidate
