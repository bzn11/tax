import os
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# Ensure outputs folder exists
os.makedirs("outputs", exist_ok=True)

# ----------------------------
# Helper Functions
# ----------------------------
def fmt_money(x):
    return f"${x:,.2f}"

def fmt_rate(x):
    return f"{x * 100:.3f}%"

# ----------------------------
# Load CSS & Fonts
# ----------------------------
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap" rel="stylesheet">
    """,
    unsafe_allow_html=True
)

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("src/ui/styles.css")

# ----------------------------
# Streamlit Config
# ----------------------------
st.set_page_config(
    page_title="Ontario Tax Estimation Portal",
    layout="wide"
)

# ----------------------------
# Header
# ----------------------------
st.markdown(
    """
    <header>
        <h1>Ontario Tax Estimation Portal</h1>
        <p>Professional property and personal income tax estimation with downloadable client reports.</p>
    </header>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Sidebar
# ----------------------------
st.sidebar.header("Quick Instructions")
st.sidebar.write("""
1. Choose Property Tax or Income Tax  
2. Enter your inputs  
3. Click Calculate  
4. Download the report PDF
""")

analysis_type = st.sidebar.radio(
    "Choose analysis type",
    ["Property Tax", "Personal Income Tax"]
)

# ----------------------------
# PROPERTY TAX
# ----------------------------
if analysis_type == "Property Tax":
    st.header("Property Tax Estimate")

    rolls_input = st.text_area(
        "Enter Ontario Roll Number(s)",
        placeholder="One per line, with or without dashes"
    )

    include_education = st.checkbox(
        "Include education tax",
        value=True
    )

    tax_year = st.number_input(
        "Tax year",
        min_value=2020,
        max_value=2026,
        value=2024
    )

    if st.button("Calculate Property Tax"):
        from src.propertytax.rollnumber import normalize_roll_number, is_valid_roll_number
        from src.propertytax.assessment import load_assessments, select_most_recent_assessment
        from src.propertytax.taxrates import load_tax_rates, get_latest_tax_rate
        from src.propertytax.calcuator import calculate_estimated_tax
        from src.propertytax.report import generate_property_report

        rolls = [r.strip() for r in rolls_input.splitlines() if r.strip()]

        assessments_df = load_assessments()
        rates_df = load_tax_rates()

        results = []
        warnings = []

        for raw in rolls:
            roll = normalize_roll_number(raw)

            if not is_valid_roll_number(roll):
                warnings.append(f"Invalid roll number: {raw}")
                continue

            assessment = select_most_recent_assessment(assessments_df, roll, year=tax_year)
            if assessment is None:
                warnings.append(f"No assessment found for {roll}")
                continue

            rate = get_latest_tax_rate(
                rates_df,
                assessment["municipality"],
                assessment["property_class"],
                year=tax_year
            )

            if rate is None:
                warnings.append(f"No tax rate found for {roll}")
                continue

            edu_rate = rate["education_rate"] if include_education else 0.0

            estimated_tax = calculate_estimated_tax(
                assessment["cva"],
                rate["municipal_rate"],
                edu_rate
            )

            results.append({
                "roll_number": roll,
                "address": assessment["address"],
                "municipality": assessment["municipality"],
                "assessment_year": assessment["tax_year"],
                "assessment_value": assessment["cva"],
                "tax_rate_year": rate["year"],
                "municipal_rate": rate["municipal_rate"],
                "education_rate": edu_rate,
                "estimated_tax": estimated_tax
            })

        if warnings:
            st.warning("\n".join(warnings))

        if results:
            display_results = []
            for r in results:
                display_results.append({
                    "Roll Number": r["roll_number"],
                    "Address": r["address"],
                    "Municipality": r["municipality"],
                    "Assessment Year": r["assessment_year"],
                    "Assessment Value": fmt_money(r["assessment_value"]),
                    "Tax Rate Year": r["tax_rate_year"],
                    "Municipal Rate": fmt_rate(r["municipal_rate"]),
                    "Education Rate": fmt_rate(r["education_rate"]),
                    "Estimated Tax": fmt_money(r["estimated_tax"])
                })

            st.subheader("Results")
            st.dataframe(pd.DataFrame(display_results), use_container_width=True)

            total_tax = sum([r["estimated_tax"] for r in results])
            st.metric("Total Estimated Tax (All Properties)", fmt_money(total_tax))

            # Chart
            chart_data = pd.DataFrame([
                {
                    "Roll": r["roll_number"],
                    "Municipal": r["municipal_rate"] * r["assessment_value"],
                    "Education": r["education_rate"] * r["assessment_value"]
                }
                for r in results
            ])
            fig = px.bar(
                chart_data,
                x="Roll",
                y=["Municipal", "Education"],
                title="Tax Breakdown by Roll Number",
                labels={"value": "Tax ($)", "variable": "Tax Type"}
            )
            st.plotly_chart(fig, use_container_width=True)

            # PDF download
            pdf_path = f"outputs/property_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            generate_property_report(results, pdf_path)

            st.download_button(
                label="Download Property Tax Report (PDF)",
                data=open(pdf_path, "rb").read(),
                file_name="property_tax_report.pdf",
                mime="application/pdf"
            )

# ----------------------------
# INCOME TAX
# ----------------------------
elif analysis_type == "Personal Income Tax":
    st.header("Personal Income Tax Estimate")

    income_tax_year = st.selectbox(
        "Income tax year",
        [2022, 2023, 2024, 2025, 2026],
        index=2
    )

    income = st.number_input("Annual Income ($)", min_value=0, step=1000)
    rrsp = st.number_input("RRSP Contribution ($)", min_value=0, step=500)

    if st.button("Calculate Income Tax"):
        from src.incometax.calculator import calculate_income_tax
        from src.incometax.report import generate_income_report

        result = calculate_income_tax(income, rrsp)

        st.success("Income tax calculated successfully!")
        st.subheader("Results")
        st.json(result)

        st.metric("Total Estimated Tax", fmt_money(result["total_tax"]))

        # Chart
        fig = px.pie(
            names=["Federal", "Ontario"],
            values=[result["federal_tax"], result["ontario_tax"]],
            title="Tax Breakdown"
        )
        st.plotly_chart(fig, use_container_width=True)

        pdf_path = f"outputs/income_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        generate_income_report(result, pdf_path)

        st.download_button(
            label="Download Income Tax Report (PDF)",
            data=open(pdf_path, "rb").read(),
            file_name="income_tax_report.pdf",
            mime="application/pdf"
        )

# ----------------------------
# Footer
# ----------------------------
st.markdown(
    """
    <div class="footer">
        © 2026 Your Name • Built with Python & Streamlit • For portfolio/demo use only
    </div>
    """,
    unsafe_allow_html=True
)
