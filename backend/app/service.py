import datetime as dt
import json
import pandas as pd
from . import db, rag, llm, charts, insights


def generate_and_run(question: str):
    ctx = rag.retrieve(question)
    context_text = "\n\n".join(c["text"] for c in ctx)
    today = dt.date.today().isoformat()
    sql = llm.generate_sql(question, context_text, db.dialect(), today)
    retries = 0
    try:
        df = db.run_query(sql)
    except Exception as e:  # one self-repair attempt using the DB error
        retries = 1
        sql = llm.generate_sql(question, context_text, db.dialect(), today, previous_sql=sql, error=str(e))
        df = db.run_query(sql)
    return sql, df, ctx, retries


def ask(question: str) -> dict:
    sql, df, ctx, retries = generate_and_run(question)
    chart = charts.choose_chart(df)
    facts = insights.compute_insights(df, chart)
    explanation = llm.explain(question, df.head(30).to_csv(index=False), facts) if not df.empty \
        else "The query returned no rows."
    return {
        "question": question,
        "sql": sql,
        "retries": retries,
        "columns": list(df.columns),
        "rows": json.loads(df.to_json(orient="records", date_format="iso")),
        "chart": chart,
        "insights": facts,
        "explanation": explanation,
        "context": [c["text"][:200] for c in ctx],
    }
