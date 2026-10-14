"""Trend / outlier summary computed with pandas (facts the LLM must stick to)."""
import pandas as pd


def _fmt(v):
    return f"{v:,.2f}" if abs(v) < 100 else f"{v:,.0f}"


def _outliers(labels, values, name):
    s = pd.Series(values, index=labels).dropna()
    if len(s) < 5 or s.std() == 0:
        return []
    z = (s - s.mean()) / s.std()
    return [f"Outlier in {name}: {k} = {_fmt(s[k])} (z={z[k]:.1f})" for k in z[abs(z) > 2].index]


def compute_insights(df: pd.DataFrame, chart: dict) -> list:
    out = []
    t = chart.get("type")
    if df.empty or t not in ("bar", "line"):
        return out
    x, y = chart["x"], chart["y"][0]
    d = df
    if chart.get("series"):
        d = df.groupby(x, as_index=False)[y].sum()
    d = d.dropna(subset=[y])
    if d.empty:
        return out
    if t == "bar":
        top, bot = d.loc[d[y].idxmax()], d.loc[d[y].idxmin()]
        out.append(f"Highest {y}: {top[x]} ({_fmt(top[y])}); lowest: {bot[x]} ({_fmt(bot[y])}).")
        total = d[y].sum()
        if total and (d[y] >= 0).all() and len(d) > 1:
            out.append(f"{top[x]} accounts for {top[y] / total:.0%} of the total.")
    else:
        d = d.sort_values(x)
        first, last = d[y].iloc[0], d[y].iloc[-1]
        if first:
            out.append(f"{y} moved from {_fmt(first)} to {_fmt(last)} ({(last - first) / abs(first):+.1%}) over the period.")
        if len(d) > 1 and d[y].iloc[-2]:
            prev = d[y].iloc[-2]
            out.append(f"Latest period vs previous: {(last - prev) / abs(prev):+.1%}.")
        pk = d.loc[d[y].idxmax()]
        out.append(f"Peak {y} was {_fmt(pk[y])} at {pk[x]}.")
    out += _outliers(d[x].astype(str).tolist(), d[y].tolist(), y)
    return out
