import os
import re
import httpx
from .config import MODEL  # importing config also loads .env

PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()
PRESETS = {  # base_url, default model
    "ollama": ("http://localhost:11434/v1", "qwen2.5-coder:7b"),
    "groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "gemini-2.5-flash"),
}

DIALECT_HINTS = {
    "sqlite": "SQLite: use strftime('%Y-%m', col) for months, date('now','start of month','-1 month') for date math. No DATE_TRUNC.",
    "postgresql": "PostgreSQL: use DATE_TRUNC('month', col), CURRENT_DATE, interval arithmetic.",
    "bigquery": "BigQuery: use DATE_TRUNC(col, MONTH), CURRENT_DATE(), DATE_SUB.",
}


def _chat(system: str, user: str, max_tokens: int) -> str:
    if PROVIDER == "anthropic":
        import anthropic
        resp = anthropic.Anthropic().messages.create(
            model=MODEL, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in resp.content if b.type == "text")
    if PROVIDER not in PRESETS:
        raise ValueError(f"Unknown LLM_PROVIDER '{PROVIDER}'. Use ollama, groq, gemini or anthropic.")
    base, default_model = PRESETS[PROVIDER]
    r = httpx.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('LLM_API_KEY', 'ollama')}"},
        json={"model": os.getenv("LLM_MODEL", default_model), "temperature": 0, "max_tokens": max_tokens,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
        timeout=180,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"{PROVIDER} API error {r.status_code}: {r.text[:300]}")
    return r.json()["choices"][0]["message"]["content"]


def generate_sql(question, context, dialect, today, previous_sql=None, error=None) -> str:
    system = (
        "You are a careful analytics engineer. Write exactly ONE read-only SQL query that answers the question.\n"
        f"Dialect: {dialect}. {DIALECT_HINTS.get(dialect, '')}\n"
        f"Today's date: {today}.\n"
        "Rules: use only tables/columns in the context; follow the metric definitions; give columns clear aliases; "
        "for time series put the date/month column first and order by it; for rankings order by the key metric; "
        "for 'dropped/declined/changed' questions return the compared periods and the % change per group. "
        "Return only the SQL inside a ```sql code block."
    )
    user = f"CONTEXT:\n{context}\n\nQUESTION: {question}"
    if previous_sql and error:
        user += f"\n\nYour previous query failed.\nSQL:\n{previous_sql}\nERROR: {error}\nFix it."
    out = _chat(system, user, 900)
    m = re.search(r"```(?:sql)?\s*(.*?)```", out, re.S | re.I)
    return (m.group(1) if m else out).strip()


def explain(question, preview_csv, insights) -> str:
    prompt = (
        f"Question: {question}\n\nResult preview (CSV):\n{preview_csv}\n\n"
        f"Computed facts:\n- " + "\n- ".join(insights or ["(none)"]) +
        "\n\nWrite a 2-4 sentence plain-English answer for a business user. Lead with the direct answer. "
        "Mention the most notable trend or outlier. Use only numbers present above; do not invent causes."
    )
    return _chat("You are a concise business data analyst.", prompt, 300).strip()