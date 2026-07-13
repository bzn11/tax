"""Property tax calculation helpers."""


def calculate_estimated_tax(
    assessment_value: float,
    municipal_rate: float,
    education_rate: float,
) -> float:
    """Estimate annual property tax from CVA and combined rates."""
    total_rate = float(municipal_rate) + float(education_rate)
    return round(float(assessment_value) * total_rate, 2)
