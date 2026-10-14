"""Creates a demo retail sales table (works on SQLite or Postgres via DATABASE_URL)."""
from pathlib import Path
import numpy as np
import pandas as pd
from .config import DATABASE_URL


def seed():
    from .db import engine
    if DATABASE_URL.startswith("sqlite:///./"):
        Path("data").mkdir(exist_ok=True)
    rng = np.random.default_rng(42)
    products = {
        "Electronics": [("Headphones", 80), ("Smart Speaker", 120), ("Webcam", 60)],
        "Home": [("Air Fryer", 90), ("Desk Lamp", 35), ("Blender", 70)],
        "Apparel": [("Jacket", 110), ("Sneakers", 95), ("T-Shirt", 25)],
        "Grocery": [("Coffee Beans", 18), ("Olive Oil", 15), ("Snack Box", 12)],
    }
    regions = {"North": 1.0, "South": 0.9, "East": 1.1, "West": 1.2, "Central": 0.8}
    today = pd.Timestamp.today().normalize()
    last_month_start = (today.replace(day=1) - pd.offsets.MonthBegin(1))
    rows, oid = [], 1
    for day in pd.date_range(today - pd.Timedelta(days=185), today):
        trend = 1 + 0.02 * (day - (today - pd.Timedelta(days=185))).days / 30
        for region, rw in regions.items():
            for cat, items in products.items():
                for prod, price in items:
                    if rng.random() < 0.45:
                        continue
                    units = max(1, int(rng.poisson(3 * rw * trend)))
                    # planted story: West collapses last month, South dips slightly
                    if last_month_start <= day < last_month_start + pd.offsets.MonthBegin(1):
                        if region == "West":
                            units = max(1, int(units * 0.55))
                        if region == "South":
                            units = max(1, int(units * 0.9))
                    disc = int(rng.choice([0, 0, 5, 10, 20, 30]))
                    rows.append((oid, day.strftime("%Y-%m-%d"), region, cat, prod,
                                 str(rng.choice(["Online", "Store", "Partner"], p=[.5, .4, .1])),
                                 units, price, disc, round(units * price * (1 - disc / 100), 2)))
                    oid += 1
    df = pd.DataFrame(rows, columns=["order_id", "order_date", "region", "category", "product",
                                     "channel", "units", "unit_price", "discount_pct", "revenue"])
    df.to_sql("sales", engine, if_exists="replace", index=False)
    print(f"Seeded {len(df):,} rows into 'sales'.")


if __name__ == "__main__":
    seed()
