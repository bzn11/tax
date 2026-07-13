"""PDF report generation for income tax estimates."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from src.common.formatting import fmt_money, fmt_pct


def generate_income_report(
    result: dict[str, Any],
    filename: str,
    *,
    client_name: str | None = None,
    ai_summary: str | None = None,
) -> str:
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    left = 1 * inch
    y = height - 1 * inch

    c.setFont("Helvetica-Bold", 16)
    c.drawString(left, y, "Ontario Personal Income Tax Estimate")
    y -= 0.35 * inch

    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    year = result.get("tax_year", "—")
    name = client_name or "Client"
    c.drawString(left, y, f"Prepared for: {name}  |  Tax year: {year}  |  Generated: {stamp}")
    c.setFillColorRGB(0, 0, 0)
    y -= 0.4 * inch

    c.setFont("Helvetica-Bold", 12)
    c.drawString(left, y, "Summary")
    y -= 0.28 * inch
    c.setFont("Helvetica", 11)

    rows = [
        ("Gross income", fmt_money(result["income"])),
        ("RRSP contribution", fmt_money(result["rrsp"])),
        ("Other deductions", fmt_money(result.get("other_deductions", 0))),
        ("Taxable income", fmt_money(result["taxable_income"])),
        ("Federal tax", fmt_money(result["federal_tax"])),
        ("Ontario tax", fmt_money(result["ontario_tax"])),
        ("Total estimated tax", fmt_money(result["total_tax"])),
        ("Net income (after tax)", fmt_money(result.get("net_income", 0))),
        ("Effective tax rate", fmt_pct(result.get("effective_rate", 0) * 100)),
        ("Combined marginal rate", fmt_pct(result.get("marginal_rate", 0) * 100)),
    ]
    for label, value in rows:
        c.drawString(left, y, f"{label}:")
        c.drawRightString(width - inch, y, value)
        y -= 16

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left, y, "Narrative")
    y -= 0.25 * inch
    c.setFont("Helvetica", 10)

    narrative = (
        f"Based on an annual income of {fmt_money(result['income'])} and total deductions of "
        f"{fmt_money(result.get('total_deductions', result['rrsp']))}, the estimated total tax "
        f"for {year} is {fmt_money(result['total_tax'])} "
        f"(effective rate {fmt_pct(result.get('effective_rate', 0) * 100)})."
    )
    y = _draw_wrapped(c, narrative, left, y, max_width=width - 2 * inch)

    if ai_summary:
        y -= 0.2 * inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left, y, "AI Insights")
        y -= 0.25 * inch
        c.setFont("Helvetica", 10)
        y = _draw_wrapped(c, ai_summary, left, y, max_width=width - 2 * inch)

    y = min(y, 1.4 * inch)
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColorRGB(0.45, 0.45, 0.45)
    disclaimer = (
        "Disclaimer: Simplified estimate for portfolio/demo purposes only. "
        "Not tax advice. Verify figures with CRA-compliant software or a qualified professional."
    )
    _draw_wrapped(c, disclaimer, left, y, max_width=width - 2 * inch)

    c.save()
    return filename


def _draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, max_width: float) -> float:
    words = text.split()
    line = ""
    for word in words:
        trial = f"{line} {word}".strip()
        if c.stringWidth(trial, "Helvetica", 10) <= max_width:
            line = trial
        else:
            c.drawString(x, y, line)
            y -= 13
            line = word
            if y < 1 * inch:
                c.showPage()
                y = letter[1] - 1 * inch
                c.setFont("Helvetica", 10)
    if line:
        c.drawString(x, y, line)
        y -= 13
    return y
