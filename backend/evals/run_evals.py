"""SQL execution-accuracy eval: generated SQL and gold SQL must return the same result set."""
import json
from pathlib import Path
import pandas as pd
from app import db, rag, service


def norm(df: pd.DataFrame):
    rows = [tuple(round(float(v), 2) if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v)
                  for v in r) for r in df.itertuples(index=False)]
    return sorted(rows, key=str)


def main():
    rag.build_index()
    cases = json.loads((Path(__file__).parent / "eval_set.json").read_text())
    results, ok = [], 0
    for c in cases:
        rec = {"id": c["id"], "question": c["question"]}
        try:
            sql, df, _, retries = service.generate_and_run(c["question"])
            gold = db.run_query(c["gold_sql"])
            rec.update(sql=sql, retries=retries, correct=norm(df) == norm(gold))
        except Exception as e:
            rec.update(correct=False, error=str(e))
        ok += rec["correct"]
        print(("PASS " if rec["correct"] else "FAIL ") + c["id"])
        results.append(rec)
    acc = ok / len(cases)
    print(f"\nExecution accuracy: {ok}/{len(cases)} = {acc:.0%}")
    (Path(__file__).parent / "last_run.json").write_text(json.dumps({"accuracy": acc, "results": results}, indent=2))


if __name__ == "__main__":
    main()
