from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from . import service, db, rag
from .config import DATABASE_URL

app = FastAPI(title="Ask Your Data")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class Ask(BaseModel):
    question: str


@app.on_event("startup")
def startup():
    if DATABASE_URL.startswith("sqlite") and not db.introspect():
        from .seed import seed
        seed()
    rag.build_index()


@app.get("/api/health")
def health():
    return {"ok": True, "dialect": db.dialect()}


@app.get("/api/schema")
def schema():
    return db.introspect()


@app.post("/api/ask")
def ask(body: Ask):
    q = body.question.strip()
    if not q:
        raise HTTPException(400, "Please enter a question.")
    try:
        return service.ask(q)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Could not answer that: {e}")


STATIC = Path(__file__).resolve().parent.parent / "static"
if STATIC.exists():
    app.mount("/assets", StaticFiles(directory=STATIC / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        f = STATIC / path
        return FileResponse(f if f.is_file() else STATIC / "index.html")
