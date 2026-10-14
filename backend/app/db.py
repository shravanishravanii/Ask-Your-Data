import re
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from .config import DATABASE_URL, MAX_ROWS

engine = create_engine(DATABASE_URL, future=True)

_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|attach|pragma|merge|copy|call|exec)\b", re.I
)


def dialect() -> str:
    return engine.dialect.name


def validate_sql(sql: str) -> str:
    s = sql.strip().rstrip(";").strip()
    if ";" in s:
        raise ValueError("Only a single SQL statement is allowed.")
    if not re.match(r"^(select|with)\b", s, re.I):
        raise ValueError("Only SELECT queries are allowed.")
    if _FORBIDDEN.search(s):
        raise ValueError("Query contains a forbidden keyword.")
    return s


def run_query(sql: str) -> pd.DataFrame:
    s = validate_sql(sql)
    with engine.connect() as conn:
        res = conn.execute(text(f"SELECT * FROM ({s}) AS q LIMIT {MAX_ROWS}"))
        return pd.DataFrame(res.fetchall(), columns=list(res.keys()))


def introspect() -> dict:
    insp = inspect(engine)
    out = {}
    for t in insp.get_table_names():
        out[t] = [(c["name"], str(c["type"])) for c in insp.get_columns(t)]
    return out


def sample_values(table: str, col: str, limit: int = 12):
    with engine.connect() as conn:
        rows = conn.execute(text(f'SELECT DISTINCT "{col}" FROM "{table}" LIMIT {limit + 1}')).fetchall()
    vals = [r[0] for r in rows]
    return vals if len(vals) <= limit else None  # None = high cardinality
