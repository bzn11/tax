import pandas as pd

def load_assessments(path="data/mpac.csv"):
    return pd.read_csv(path, dtype={"roll_number": str})

def select_most_recent_assessment(df, roll_number, year=None):
    records = df[df["roll_number"] == roll_number]

    if records.empty:
        return None

    if year:
        year_records = records[records["tax_year"] == year]
        if not year_records.empty:
            return year_records.iloc[0]

    return records.sort_values("tax_year", ascending=False).iloc[0]
