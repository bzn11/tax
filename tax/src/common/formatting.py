"""Currency and rate display helpers."""


def fmt_money(value: float | int | None) -> str:
    """Format a numeric value as CAD currency."""
    if value is None:
        return "—"
    return f"${float(value):,.2f}"


def fmt_rate(rate: float | None) -> str:
    """Format a decimal rate as a percentage string."""
    if rate is None:
        return "—"
    return f"{float(rate) * 100:.3f}%"


def fmt_pct(value: float | None, digits: int = 1) -> str:
    """Format an already-percentage value (e.g. 24.5 → '24.5%')."""
    if value is None:
        return "—"
    return f"{float(value):.{digits}f}%"
