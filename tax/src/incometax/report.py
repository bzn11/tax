from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def generate_income_report(result, filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "Ontario Personal Income Tax Estimate Report")

    y = height - 1.5*inch
    c.setFont("Helvetica", 12)

    c.drawString(1*inch, y, f"Income: ${result['income']:,}")
    y -= 15
    c.drawString(1*inch, y, f"RRSP Contribution: ${result['rrsp']:,}")
    y -= 15
    c.drawString(1*inch, y, f"Taxable Income: ${result['taxable_income']:,}")
    y -= 15
    c.drawString(1*inch, y, f"Federal Tax: ${result['federal_tax']:,}")
    y -= 15
    c.drawString(1*inch, y, f"Ontario Tax: ${result['ontario_tax']:,}")
    y -= 15
    c.drawString(1*inch, y, f"Total Tax: ${result['total_tax']:,}")
    y -= 30

    narrative = (
        f"Based on an annual income of ${result['income']:,} and RRSP contribution "
        f"of ${result['rrsp']:,}, the estimated total tax is ${result['total_tax']:,}."
    )
    c.drawString(1*inch, y, narrative)

    c.save()
