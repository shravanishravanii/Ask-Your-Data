# Ask Your Data

Ask a business question in plain English. The app retrieves schema + metric definitions (RAG), generates SQL with an LLM, runs it safely, auto-picks a chart, and writes a short explanation with trends and outliers.

```
React (Vite + Recharts) ──► FastAPI ──► RAG (TF-IDF over schema + metrics)
                                   ├─► Claude → SQL (validated, read-only, 1 auto-retry)
                                   ├─► Warehouse (SQLite demo / Postgres / BigQuery via SQLAlchemy)
                                   └─► Chart chooser + insights (pandas) + LLM summary
```

## Run in VS Code (no Docker)

Prereqs: Python 3.10+, Node 18+, an Anthropic API key.

**Terminal 1 – backend**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then put your ANTHROPIC_API_KEY in .env
python -m app.seed                 # creates demo SQLite DB (6 months of retail sales)
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 – frontend**
```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

Try: *"Which region's sales dropped last month?"*, *"Monthly revenue trend by category"*, *"Top 5 products by revenue this year"*.

## Run with Docker
```bash
cp backend/.env.example backend/.env   # add your key
docker compose up --build              # http://localhost:8080
# with Postgres instead of SQLite:
docker compose --profile pg up --build
```

## Evaluate SQL execution accuracy
```bash
cd backend
python -m evals.run_evals
```
Each question in `evals/eval_set.json` has a gold SQL. The runner executes generated vs gold SQL and compares result sets (order-insensitive, rounded). It prints accuracy and saves `evals/last_run.json`. Add your own cases as you add data.

## Use your own data
1. Set `DATABASE_URL` in `backend/.env` (e.g. `postgresql+psycopg2://user:pass@host:5432/db`).
2. Edit `backend/app/semantic_layer.yaml`: describe tables, columns and **metric definitions** (this is what makes answers match your business logic).
3. Restart. Use a **read-only DB user** in production.

**BigQuery:** `pip install sqlalchemy-bigquery`, set `DATABASE_URL=bigquery://PROJECT/DATASET`, and authenticate with `gcloud auth application-default login` (or the Cloud Run service account).

## Deploy to GCP Cloud Run
```bash
gcloud run deploy ask-your-data --source . --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=...,ANTHROPIC_MODEL=claude-sonnet-5-5 \
  --set-secrets ANTHROPIC_API_KEY=anthropic-key:latest
```
(Remove `--allow-unauthenticated` and put IAP/auth in front for real data.) For AWS, push the same image to ECR and run on App Runner or ECS Fargate.

## Safety notes
Only a single `SELECT`/`WITH` statement is allowed, DDL/DML keywords are rejected, results are capped at 1000 rows. This is defence in depth, not a substitute for a read-only database role.

## Layout
```
backend/app/   main.py (API) · service.py (pipeline) · llm.py · rag.py · db.py
               charts.py · insights.py · seed.py · semantic_layer.yaml
backend/evals/ eval_set.json · run_evals.py
frontend/src/  App.jsx · styles.css
Dockerfile · docker-compose.yml
```
