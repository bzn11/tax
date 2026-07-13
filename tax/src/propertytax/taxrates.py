"""Municipal tax rate data access."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from src.common.paths import data_path


@lru_cache(maxsize=4)
def _read_tax_rates(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def load_tax_rates(path: str | None = None):
    csv_path = path or str(data_path("tr.csv"))
    return _read_tax_rates(csv_path).copy()


def get_latest_tax_rate(df, municipality, property_class, year=None):
    rates = df[
        (df["municipality"] == municipality) & (df["property_class"] == property_class)
    ]

    if rates.empty:
        return None

    if year is not None:
        year_rates = rates[rates["year"] == year]
        if not year_rates.empty:
            return year_rates.iloc[0]

    return rates.sort_values("year", ascending=False).iloc[0]
