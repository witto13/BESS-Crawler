"""
Parquet export using pandas/pyarrow.
"""
from typing import List, Dict
import pandas as pd


def export_procedures(rows: List[Dict], path: str) -> None:
    if not rows:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(rows)
    df.to_parquet(path, index=False, engine="pyarrow")

