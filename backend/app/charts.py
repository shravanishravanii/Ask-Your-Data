"""Rule-based automatic chart selection."""
import re
import pandas as pd

_TIME_NAME = re.compile(r"date|month|week|day|quarter|period|time", re.I)


def _is_temporal(s: pd.Series, name: str) -> bool:
    if pd.api.types.is_datetime64_any_dtype(s):
        return True
    if pd.api.types.is_numeric_dtype(s) or not _TIME_NAME.search(name):
        return False
    return pd.to_datetime(s, errors="coerce").notna().all()


def choose_chart(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"type": "table"}
    cols = list(df.columns)
    temporal = [c for c in cols if _is_temporal(df[c], c)]
    num = [c for c in cols if c not in temporal and pd.api.types.is_numeric_dtype(df[c])]
    cat = [c for c in cols if c not in temporal and c not in num]

    if len(df) == 1 and num and not cat and not temporal:
        return {"type": "kpi", "y": num[:3]}
    if temporal and num and len(df) > 1:
        if cat and len(num) == 1 and df[cat[0]].nunique() <= 8:
            return {"type": "line", "x": temporal[0], "y": num[:1], "series": cat[0]}
        return {"type": "line", "x": temporal[0], "y": num[:4]}
    if cat and num and df[cat[0]].nunique() <= 25:
        # prefer an absolute metric over helper columns like pct_change when multiple exist
        return {"type": "bar", "x": cat[0], "y": num[:3]}
    if len(num) >= 2 and not cat and not temporal:
        return {"type": "scatter", "x": num[0], "y": [num[1]]}
    return {"type": "table"}
