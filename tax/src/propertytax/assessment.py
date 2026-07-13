"""Assessment data access."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from src.common.paths import data_path


@lru_cache(maxsize=4)
def _read_assessments(path: str) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"roll_number": str})


def load_assessments(path: str | None = None):
    csv_path = path or str(data_path("mpac.csv"))
    # Return a copy so callers cannot mutate the cached frame.
    return _read_assessments(csv_path).copy()


def select_most_recent_assessment(df, roll_number, year=None):
    records = df[df["roll_number"] == roll_number]

    if records.empty:
        return None

    if year is not None:
        year_records = records[records["tax_year"] == year]
        if not year_records.empty:
            return year_records.iloc[0]

    return records.sort_values("tax_year", ascending=False).iloc[0]
