import { useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar, LineChart, Line, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";

const COLORS = ["#2f6fed", "#e8590c", "#2b8a3e", "#9c36b5", "#f08c00", "#0c8599"];
const EXAMPLES = [
  "Which region's sales dropped last month?",
  "Monthly revenue trend by category",
  "Top 5 products by revenue",
  "Average order value by channel",
  "What is the total revenue?",
];
const fmt = (v) => (typeof v === "number" ? v.toLocaleString(undefined, { maximumFractionDigits: 2 }) : v);

function pivot(rows, x, series, y) {
  const map = {};
  rows.forEach((r) => { (map[r[x]] ||= { [x]: r[x] })[r[series]] = r[y]; });
  const keys = [...new Set(rows.map((r) => r[series]))];
  return { data: Object.values(map), keys };
}

function Chart({ res }) {
  const { chart, rows, columns } = res;
  if (chart.type === "kpi")
    return (
      <div className="kpis">
        {chart.y.map((k) => (
          <div className="kpi" key={k}><span>{k.replace(/_/g, " ")}</span><b>{fmt(rows[0][k])}</b></div>
        ))}
      </div>
    );
  if (chart.type === "table") return <DataTable rows={rows} columns={columns} />;
  const axis = { stroke: "#8a94a6", fontSize: 12 };
  const common = (
    <>
      <CartesianGrid strokeDasharray="3 3" stroke="#e3e7ee" />
      <XAxis dataKey={chart.x} {...axis} />
      <YAxis {...axis} tickFormatter={fmt} />
      <Tooltip formatter={fmt} /><Legend />
    </>
  );
  return (
    <ResponsiveContainer width="100%" height={340}>
      {chart.type === "bar" ? (
        <BarChart data={rows}>{common}
          {chart.y.map((k, i) => <Bar key={k} dataKey={k} fill={COLORS[i]} radius={[4, 4, 0, 0]} />)}
        </BarChart>
      ) : chart.type === "line" ? (() => {
        const p = chart.series ? pivot(rows, chart.x, chart.series, chart.y[0]) : { data: rows, keys: chart.y };
        return (
          <LineChart data={p.data}>{common}
            {p.keys.map((k, i) => <Line key={k} type="monotone" dataKey={k} stroke={COLORS[i % 6]} strokeWidth={2.5} dot={false} />)}
          </LineChart>
        );
      })() : (
        <ScatterChart>{common}<Scatter data={rows} fill={COLORS[0]} /></ScatterChart>
      )}
    </ResponsiveContainer>
  );
}

function DataTable({ rows, columns }) {
  return (
    <div className="tablewrap">
      <table>
        <thead><tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>{rows.slice(0, 100).map((r, i) => (
          <tr key={i}>{columns.map((c) => <td key={c}>{fmt(r[c])}</td>)}</tr>
        ))}</tbody>
      </table>
    </div>
  );
}

export default function App() {
  const [q, setQ] = useState("");
  const [res, setRes] = useState(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);

  async function ask(question) {
    if (!question.trim()) return;
    setQ(question); setLoading(true); setErr("");
    try {
      const r = await fetch("/api/ask", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || "Request failed");
      setRes(j); setHistory((h) => [question, ...h.filter((x) => x !== question)].slice(0, 6));
    } catch (e) { setErr(e.message); } finally { setLoading(false); }
  }

  return (
    <main>
      <header>
        <h1>Ask Your Data</h1>
        <p>Ask a business question in plain English. Get SQL, a chart and a short explanation.</p>
      </header>

      <div className="askbar">
        <input value={q} placeholder="e.g. Which region's sales dropped last month?"
          onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && ask(q)} />
        <button onClick={() => ask(q)} disabled={loading}>{loading ? "Thinking…" : "Ask"}</button>
      </div>
      <div className="chips">
        {EXAMPLES.map((e) => <button key={e} className="chip" onClick={() => ask(e)}>{e}</button>)}
      </div>

      {err && <div className="card error">{err}</div>}

      {res && (
        <section className="card">
          <h2>{res.question}</h2>
          <p className="explain">{res.explanation}</p>
          <Chart res={res} />
          {res.insights.length > 0 && (
            <ul className="insights">{res.insights.map((i, k) => <li key={k}>{i}</li>)}</ul>
          )}
          <details><summary>SQL{res.retries ? " (auto-corrected once)" : ""}</summary><pre>{res.sql}</pre></details>
          <details><summary>Data ({res.rows.length} rows)</summary><DataTable rows={res.rows} columns={res.columns} /></details>
          <details><summary>Retrieved context (RAG)</summary>
            <pre>{res.context.join("\n---\n")}</pre></details>
        </section>
      )}

      {history.length > 1 && (
        <p className="hist">Recent: {history.map((h) => (
          <a key={h} onClick={() => ask(h)}>{h}</a>))}
        </p>
      )}
    </main>
  );
}
