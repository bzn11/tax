from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def generate_property_report(rows, filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "Ontario Property Tax Estimate Report")

    y = height - 1.5*inch
    c.setFont("Helvetica", 12)

    for r in rows:
        c.drawString(1*inch, y, f"Address: {r['address']}")
        y -= 15
        c.drawString(1*inch, y, f"Roll Number: {r['roll_number']}")
        y -= 15
        c.drawString(1*inch, y, f"Municipality: {r['municipality']}")
        y -= 15
        c.drawString(1*inch, y, f"Assessment Year: {r['assessment_year']}")
        y -= 15
        c.drawString(1*inch, y, f"Assessment Value: ${r['assessment_value']:,}")
        y -= 15
        c.drawString(1*inch, y, f"Tax Rate Year: {r['tax_rate_year']}")
        y -= 15
        c.drawString(1*inch, y, f"Municipal Rate: {r['municipal_rate']*100:.3f}%")
        y -= 15
        c.drawString(1*inch, y, f"Education Rate: {r['education_rate']*100:.3f}%")
        y -= 15
        c.drawString(1*inch, y, f"Estimated Taxes: ${r['estimated_tax']:,}")
        y -= 20

        # Narrative line
        narrative = (
            f"The property located at {r['address']} (Roll: {r['roll_number']}) "
            f"is located in {r['municipality']} and is currently assessed at "
            f"${r['assessment_value']:,}, which equates to estimated taxes of "
            f"${r['estimated_tax']:,}."
        )
        c.drawString(1*inch, y, narrative)
        y -= 30

        # Page break if needed
        if y < 2*inch:
            c.showPage()
            y = height - 1*inch

    c.save()
