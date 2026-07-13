"""PDF report generation for property tax estimates."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from src.common.formatting import fmt_money, fmt_rate


def generate_property_report(
    rows: list[dict[str, Any]],
    filename: str,
    *,
    client_name: str | None = None,
    ai_summary: str | None = None,
    total_tax: float | None = None,
) -> str:
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    left = 1 * inch
    y = height - 1 * inch

    c.setFont("Helvetica-Bold", 16)
    c.drawString(left, y, "Ontario Property Tax Estimate Report")
    y -= 0.35 * inch

    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    name = client_name or "Client"
    total = total_tax if total_tax is not None else sum(r["estimated_tax"] for r in rows)
    c.drawString(
        left,
        y,
        f"Prepared for: {name}  |  Properties: {len(rows)}  |  "
        f"Total: {fmt_money(total)}  |  Generated: {stamp}",
    )
    c.setFillColorRGB(0, 0, 0)
    y -= 0.4 * inch

    for idx, r in enumerate(rows, start=1):
        if y < 2.5 * inch:
            c.showPage()
            y = height - 1 * inch

        c.setFont("Helvetica-Bold", 12)
        c.drawString(left, y, f"Property {idx}")
        y -= 0.28 * inch
        c.setFont("Helvetica", 10)

        lines = [
            f"Address: {r['address']}",
            f"Roll Number: {r['roll_number']}",
            f"Municipality: {r['municipality']}",
            f"Assessment Year: {r['assessment_year']}",
            f"Assessment Value (CVA): {fmt_money(r['assessment_value'])}",
            f"Tax Rate Year: {r['tax_rate_year']}",
            f"Municipal Rate: {fmt_rate(r['municipal_rate'])}",
            f"Education Rate: {fmt_rate(r['education_rate'])}",
            f"Estimated Taxes: {fmt_money(r['estimated_tax'])}",
        ]
        for line in lines:
            c.drawString(left, y, line)
            y -= 14

        narrative = (
            f"The property at {r['address']} (Roll: {r['roll_number']}) in "
            f"{r['municipality']} is assessed at {fmt_money(r['assessment_value'])}, "
            f"equating to estimated annual taxes of {fmt_money(r['estimated_tax'])}."
        )
        y = _draw_wrapped(c, narrative, left, y, max_width=width - 2 * inch)
        y -= 12

    if ai_summary:
        if y < 2 * inch:
            c.showPage()
            y = height - 1 * inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left, y, "AI Insights")
        y -= 0.25 * inch
        c.setFont("Helvetica", 10)
        y = _draw_wrapped(c, ai_summary, left, y, max_width=width - 2 * inch)

    c.showPage()
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColorRGB(0.45, 0.45, 0.45)
    disclaimer = (
        "Disclaimer: Estimates use sample MPAC and tax-rate data for portfolio/demo purposes. "
        "Not an official municipal bill. Confirm with your municipality or a licensed professional."
    )
    _draw_wrapped(c, disclaimer, left, height - 1 * inch, max_width=width - 2 * inch)
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
