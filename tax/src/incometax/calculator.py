def calculate_income_tax(income, rrsp=0):
    """
    Simple Canada Federal + Ontario tax estimate.
    This is a simplified model (not 100% accurate), but realistic.
    """
    taxable_income = max(0, income - rrsp)

    # Federal brackets (2024 simplified)
    federal = 0
    if taxable_income > 0:
        federal += min(taxable_income, 55300) * 0.15
    if taxable_income > 55300:
        federal += min(taxable_income - 55300, 55300) * 0.205
    if taxable_income > 110000:
        federal += min(taxable_income - 110000,  110000) * 0.26
    if taxable_income > 221000:
        federal += min(taxable_income - 221000,  160000) * 0.29
    if taxable_income > 381000:
        federal += (taxable_income - 381000) * 0.33

    # Ontario brackets (2024 simplified)
    ontario = 0
    if taxable_income > 0:
        ontario += min(taxable_income, 50197) * 0.0505
    if taxable_income > 50197:
        ontario += min(taxable_income - 50197, 50198) * 0.0915
    if taxable_income > 100395:
        ontario += min(taxable_income - 100395, 70373) * 0.1116
    if taxable_income > 170768:
        ontario += min(taxable_income - 170768, 120000) * 0.1216
    if taxable_income > 290000:
        ontario += (taxable_income - 290000) * 0.1316

    total_tax = federal + ontario
    return {
        "income": income,
        "rrsp": rrsp,
        "taxable_income": taxable_income,
        "federal_tax": round(federal, 2),
        "ontario_tax": round(ontario, 2),
        "total_tax": round(total_tax, 2)
    }