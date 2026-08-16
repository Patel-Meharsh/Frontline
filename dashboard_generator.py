#!/usr/bin/env python3
"""
Builds a single self-contained dashboard.html from results.json (data embedded inline,
so it opens directly in a browser with no server needed).

Usage:
    python dashboard_generator.py
    python dashboard_generator.py --results results.json --output dashboard.html
"""

import json
import argparse

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FRONTLINE — Triage Console</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

  :root {
    --bg: #14181c;
    --panel: #1b2126;
    --panel-border: #2a3238;
    --text: #e7edf1;
    --text-dim: #8996a1;
    --accent: #4fd1c5;
    --p0: #ef5350;
    --p1: #ffa94d;
    --p2: #4fa3ff;
    --p3: #6b7680;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: 'IBM Plex Mono', monospace;
    padding: 32px 40px 80px;
  }
  h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 28px;
    letter-spacing: -0.02em;
    margin: 0 0 2px;
  }
  .subtitle { color: var(--text-dim); font-size: 13px; margin-bottom: 28px; }
  .stats {
    display: flex;
    gap: 14px;
    margin-bottom: 28px;
    flex-wrap: wrap;
  }
  .stat {
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 10px;
    padding: 14px 20px;
    min-width: 120px;
  }
  .stat .num { font-family: 'Space Grotesk', sans-serif; font-size: 24px; font-weight: 700; }
  .stat .label { font-size: 11px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.06em; margin-top: 2px; }
  .filters { display: flex; gap: 8px; margin-bottom: 18px; flex-wrap: wrap; }
  .filters button {
    background: var(--panel);
    border: 1px solid var(--panel-border);
    color: var(--text-dim);
    padding: 7px 14px;
    border-radius: 999px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    cursor: pointer;
  }
  .filters button.active { color: var(--bg); background: var(--accent); border-color: var(--accent); font-weight: 600; }
  table { width: 100%; border-collapse: collapse; background: var(--panel); border-radius: 10px; overflow: hidden; border: 1px solid var(--panel-border); }
  th {
    text-align: left;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-dim);
    padding: 12px 14px;
    border-bottom: 1px solid var(--panel-border);
  }
  td { padding: 12px 14px; border-bottom: 1px solid var(--panel-border); font-size: 13px; vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #202830; }
  .id { color: var(--text-dim); }
  .msg { color: var(--text); max-width: 320px; }
  .pill { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; }
  .p0 { background: rgba(239,83,80,0.15); color: var(--p0); }
  .p1 { background: rgba(255,169,77,0.15); color: var(--p1); }
  .p2 { background: rgba(79,163,255,0.15); color: var(--p2); }
  .p3 { background: rgba(107,118,128,0.2); color: var(--p3); }
  .human { color: var(--accent); font-size: 11px; font-weight: 600; }
  .conf { color: var(--text-dim); font-size: 11px; }
  .cat { color: var(--text-dim); font-size: 12px; }
</style>
</head>
<body>
  <h1>FRONTLINE</h1>
  <div class="subtitle">Triage console — %(count)s messages processed — model: %(model)s — generated %(generated_at)s</div>

  <div class="stats">
    <div class="stat"><div class="num" id="stat-total">0</div><div class="label">Total</div></div>
    <div class="stat"><div class="num" id="stat-human">0</div><div class="label">Needs human</div></div>
    <div class="stat"><div class="num" id="stat-p0">0</div><div class="label">P0</div></div>
    <div class="stat"><div class="num" id="stat-p1">0</div><div class="label">P1</div></div>
  </div>

  <div class="filters" id="filters">
    <button data-f="all" class="active">All</button>
    <button data-f="P0">P0</button>
    <button data-f="P1">P1</button>
    <button data-f="P2">P2</button>
    <button data-f="P3">P3</button>
    <button data-f="human">Needs human</button>
  </div>

  <table>
    <thead>
      <tr>
        <th>ID</th><th>Message</th><th>Category</th><th>Priority</th><th>Summary</th><th>Suggested action</th><th>Human?</th><th>Conf.</th>
      </tr>
    </thead>
    <tbody id="rows"></tbody>
  </table>

<script>
const DATA = %(data_json)s;

function esc(s) {
  return (s || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

function render(filter) {
  const tbody = document.getElementById("rows");
  tbody.innerHTML = "";
  let shown = DATA.filter(r => {
    if (filter === "all") return true;
    if (filter === "human") return r.decision.needs_human;
    return r.decision.priority === filter;
  });
  for (const r of shown) {
    const d = r.decision;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="id">${esc(r.id)}</td>
      <td class="msg">${esc(r.input_text).slice(0,140)}${r.input_text.length>140?"…":""}</td>
      <td class="cat">${esc(d.category)}</td>
      <td><span class="pill ${d.priority.toLowerCase()}">${d.priority}</span></td>
      <td class="msg">${esc(d.summary)}</td>
      <td class="msg">${esc(d.suggested_action)}</td>
      <td>${d.needs_human ? '<span class="human">● HUMAN</span>' : ''}</td>
      <td class="conf">${(d.confidence*100).toFixed(0)}%</td>
    `;
    tbody.appendChild(tr);
  }
}

function updateStats() {
  document.getElementById("stat-total").textContent = DATA.length;
  document.getElementById("stat-human").textContent = DATA.filter(r=>r.decision.needs_human).length;
  document.getElementById("stat-p0").textContent = DATA.filter(r=>r.decision.priority==="P0").length;
  document.getElementById("stat-p1").textContent = DATA.filter(r=>r.decision.priority==="P1").length;
}

document.getElementById("filters").addEventListener("click", (e) => {
  if (e.target.tagName !== "BUTTON") return;
  document.querySelectorAll("#filters button").forEach(b=>b.classList.remove("active"));
  e.target.classList.add("active");
  render(e.target.dataset.f);
});

updateStats();
render("all");
</script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results.json")
    parser.add_argument("--output", default="dashboard.html")
    args = parser.parse_args()

    with open(args.results, "r", encoding="utf-8") as f:
        data = json.load(f)

    html = TEMPLATE
    html = html.replace("%(count)s", str(data["count"]))
    html = html.replace("%(model)s", str(data["model"]))
    html = html.replace("%(generated_at)s", str(data["generated_at"]))
    html = html.replace("%(data_json)s", json.dumps(data["results"], ensure_ascii=False))
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {args.output} — open it directly in a browser.")


if __name__ == "__main__":
    main()
