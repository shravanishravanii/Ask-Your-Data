"""Lightweight RAG: schema + metric definitions are chunked and retrieved with TF-IDF."""
from pathlib import Path
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from . import db

_LAYER = Path(__file__).parent / "semantic_layer.yaml"
_chunks, _vec, _matrix = [], None, None


def build_index():
    global _chunks, _vec, _matrix
    layer = yaml.safe_load(_LAYER.read_text())
    docs = layer.get("tables", {})
    chunks = []
    for table, cols in db.introspect().items():
        meta = docs.get(table, {})
        cdesc = meta.get("columns", {})
        lines = [f"TABLE {table}: {meta.get('description', '')}"]
        for name, typ in cols:
            extra = ""
            if "CHAR" in typ.upper() or "TEXT" in typ.upper():
                vals = db.sample_values(table, name)
                if vals:
                    extra = f" values: {vals}"
            lines.append(f"  - {name} ({typ}): {cdesc.get(name, '')}{extra}")
        chunks.append({"kind": "table", "text": "\n".join(lines)})
    for m in layer.get("metrics", []):
        chunks.append({"kind": "metric", "text": f"METRIC {m['name']}: {m['definition']}"})
    _chunks = chunks
    _vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    _matrix = _vec.fit_transform([c["text"] for c in chunks])


def retrieve(question: str, k: int = 5):
    if _vec is None:
        build_index()
    sims = cosine_similarity(_vec.transform([question]), _matrix)[0]
    ranked = sorted(range(len(_chunks)), key=lambda i: -sims[i])[:k]
    picked = [_chunks[i] for i in ranked]
    # always include table schemas: the model must never guess columns
    for c in _chunks:
        if c["kind"] == "table" and c not in picked:
            picked.insert(0, c)
    return picked
