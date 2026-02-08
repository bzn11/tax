import pandas as pd

def load_tax_rates(path="data/tr.csv"):
    return pd.read_csv(path)

def get_latest_tax_rate(df, municipality, property_class, year=None):
    rates = df[
        (df["municipality"] == municipality) &
        (df["property_class"] == property_class)
    ]

    if rates.empty:
        return None

    if year:
        year_rates = rates[rates["year"] == year]
        if not year_rates.empty:
            return year_rates.iloc[0]

    return rates.sort_values("year", ascending=False).iloc[0]
