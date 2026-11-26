#!/usr/bin/env python3
"""
Generate a polished, self-contained Frontline triage dashboard.

Usage:
    python dashboard_generator.py
    python dashboard_generator.py --results results.json --output dashboard.html
"""

import argparse
import json
from pathlib import Path

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>Frontline | Support Intelligence</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
:root {
  --bg:#0b1020; --surface:#111a2e; --surface-2:#16223a; --surface-3:#1b2943;
  --line:rgba(148,163,184,.15); --text:#edf3ff; --muted:#91a0b9;
  --accent:#7c9cff; --accent-2:#5eead4; --danger:#fb7185; --warning:#fbbf24;
  --blue:#60a5fa; --slate:#94a3b8; --shadow:0 18px 50px rgba(0,0,0,.24);
}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at 12% 0%,rgba(70,101,190,.17),transparent 34%),radial-gradient(ellipse at 92% 8%,rgba(45,212,191,.08),transparent 28%),var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh}
button,input,select{font:inherit}
button{cursor:pointer}
.shell{max-width:1500px;margin:0 auto;padding:28px 34px 64px}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:42px}
.brand{display:flex;align-items:center;gap:13px}
.brand-mark{width:42px;height:42px;border-radius:14px;background:linear-gradient(145deg,#8aa5ff,#5eead4);display:grid;place-items:center;color:#0b1020;font-weight:900;font-size:19px;box-shadow:0 8px 28px rgba(124,156,255,.24)}
.brand-name{font:700 18px 'Space Grotesk',sans-serif;letter-spacing:.11em}
.brand-sub{font-size:11px;color:var(--muted);margin-top:3px;letter-spacing:.08em;text-transform:uppercase}
.top-actions{display:flex;align-items:center;gap:10px}
.live-pill{display:flex;align-items:center;gap:8px;padding:8px 12px;border:1px solid var(--line);border-radius:999px;color:#b7c5dc;font-size:12px;background:rgba(17,26,46,.7)}
.live-dot{width:7px;height:7px;background:var(--accent-2);border-radius:50%;box-shadow:0 0 0 4px rgba(94,234,212,.1)}
.icon-btn,.secondary-btn{border:1px solid var(--line);background:var(--surface);color:var(--text);border-radius:11px;padding:10px 13px;font-size:12px;font-weight:700;transition:.2s}
.icon-btn:hover,.secondary-btn:hover{border-color:rgba(124,156,255,.55);background:var(--surface-2);transform:translateY(-1px)}
.eyebrow{color:var(--accent-2);font-size:11px;text-transform:uppercase;letter-spacing:.16em;font-weight:800;margin-bottom:12px}
.hero{display:flex;justify-content:space-between;align-items:flex-end;gap:28px;margin-bottom:28px}
h1{font:700 clamp(30px,4vw,46px)/1.05 'Space Grotesk',sans-serif;letter-spacing:-.045em;margin:0}
.hero-copy{color:var(--muted);font-size:14px;margin:12px 0 0;max-width:620px;line-height:1.65}
.run-meta{text-align:right;color:var(--muted);font-size:12px;line-height:1.8;white-space:nowrap}
.run-meta strong{color:#dbe6fa;font-weight:600}
.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:18px}
.metric{position:relative;overflow:hidden;padding:19px 20px;background:linear-gradient(145deg,rgba(22,34,58,.96),rgba(17,26,46,.96));border:1px solid var(--line);border-radius:17px;box-shadow:var(--shadow)}
.metric:after{content:"";position:absolute;width:90px;height:90px;border-radius:50%;right:-30px;top:-35px;background:var(--glow,rgba(124,156,255,.10));filter:blur(3px)}
.metric-top{display:flex;align-items:center;justify-content:space-between;color:var(--muted);font-size:12px;font-weight:600}
.metric-icon{width:30px;height:30px;display:grid;place-items:center;border-radius:10px;background:rgba(124,156,255,.12);color:var(--accent);font-size:15px}
.metric-value{font:700 31px 'Space Grotesk',sans-serif;margin-top:13px;letter-spacing:-.04em}
.metric-foot{font-size:11px;color:var(--muted);margin-top:5px}
.content-grid{display:grid;grid-template-columns:280px minmax(0,1fr);gap:17px;align-items:start}
.panel{background:rgba(17,26,46,.88);border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow)}
.side-panel{padding:20px}
.panel-heading{font:700 15px 'Space Grotesk',sans-serif;margin:0}
.panel-sub{font-size:11px;color:var(--muted);margin-top:5px}
.priority-list{display:grid;gap:16px;margin-top:24px}
.priority-head{display:flex;justify-content:space-between;align-items:center;font-size:12px;margin-bottom:8px}
.priority-label{display:flex;align-items:center;gap:8px;font-weight:700}
.priority-count{color:var(--muted);font-variant-numeric:tabular-nums}
.priority-dot{width:8px;height:8px;border-radius:3px;background:var(--tone)}
.track{height:7px;border-radius:99px;background:rgba(148,163,184,.12);overflow:hidden}
.track-fill{height:100%;width:0;border-radius:99px;background:var(--tone);transition:width .45s ease}
.side-divider{height:1px;background:var(--line);margin:24px 0}
.category-list{display:flex;flex-wrap:wrap;gap:7px;margin-top:16px}
.category-tag{font-size:10px;color:#c1cde0;border:1px solid var(--line);background:rgba(148,163,184,.06);border-radius:7px;padding:6px 8px}
.category-tag span{color:var(--accent-2);font-weight:800;margin-left:5px}
.main-panel{min-width:0;overflow:hidden}
.toolbar{padding:19px 20px;border-bottom:1px solid var(--line)}
.toolbar-top{display:flex;justify-content:space-between;align-items:center;gap:14px;margin-bottom:17px}
.result-count{color:var(--muted);font-size:12px}
.result-count strong{color:var(--text)}
.controls{display:flex;gap:9px;align-items:center;flex-wrap:wrap}
.search-wrap{position:relative;flex:1;min-width:190px}
.search-wrap input{width:100%;height:39px;padding:0 13px 0 37px;background:var(--bg);border:1px solid var(--line);border-radius:10px;color:var(--text);outline:none;font-size:12px}
.search-wrap input:focus,select:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(124,156,255,.12)}
.search-icon{position:absolute;left:13px;top:11px;color:var(--muted);font-size:14px}
select{height:39px;padding:0 30px 0 11px;background:var(--bg);border:1px solid var(--line);border-radius:10px;color:#c9d5e8;font-size:12px;outline:none}
.filters{display:flex;gap:7px;flex-wrap:wrap}
.filter-btn{border:1px solid var(--line);background:transparent;color:var(--muted);padding:7px 11px;border-radius:8px;font-size:11px;font-weight:700;transition:.18s}
.filter-btn:hover{color:var(--text);background:rgba(148,163,184,.07)}
.filter-btn.active{background:rgba(124,156,255,.15);border-color:rgba(124,156,255,.38);color:#cbd8ff}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;min-width:790px}
thead{background:rgba(148,163,184,.035)}
th{text-align:left;padding:12px 15px;color:#7788a5;font-size:10px;letter-spacing:.1em;text-transform:uppercase;font-weight:800;white-space:nowrap}
td{padding:14px 15px;border-top:1px solid rgba(148,163,184,.09);font-size:12px;vertical-align:middle}
tbody tr{transition:background .16s}
tbody tr:hover{background:rgba(124,156,255,.045)}
.id-cell{color:#8090aa;font:600 11px 'Space Grotesk',sans-serif;white-space:nowrap}
.message-cell{max-width:245px}
.message-text{color:#dbe5f5;line-height:1.45;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.subtle{color:var(--muted);font-size:11px;line-height:1.45}
.category{display:inline-flex;max-width:145px;white-space:normal;line-height:1.3;color:#b9c9e5;background:rgba(148,163,184,.08);border:1px solid rgba(148,163,184,.12);border-radius:7px;padding:5px 7px;font-size:10px}
.priority{display:inline-flex;align-items:center;gap:6px;border-radius:7px;padding:6px 8px;font-size:10px;font-weight:800;white-space:nowrap}
.priority:before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor}
.priority.P0{color:var(--danger);background:rgba(251,113,133,.12)}
.priority.P1{color:var(--warning);background:rgba(251,191,36,.12)}
.priority.P2{color:var(--blue);background:rgba(96,165,250,.12)}
.priority.P3{color:var(--slate);background:rgba(148,163,184,.12)}
.human-flag{display:inline-flex;align-items:center;gap:5px;color:#fda4af;font-size:10px;font-weight:800;white-space:nowrap}
.auto-flag{color:#72d9c6;font-size:10px;font-weight:700}
.confidence{display:flex;align-items:center;gap:7px;color:#bdc9dc;font-size:11px;white-space:nowrap}
.conf-track{width:42px;height:4px;background:rgba(148,163,184,.15);border-radius:9px;overflow:hidden}
.conf-fill{height:100%;background:var(--accent-2);border-radius:9px}
.view-btn{background:transparent;border:1px solid var(--line);color:#aebde0;border-radius:7px;padding:6px 9px;font-size:10px;font-weight:700;white-space:nowrap}
.view-btn:hover{border-color:var(--accent);color:var(--text)}
.empty{padding:55px 20px;text-align:center;color:var(--muted);font-size:13px}
.empty strong{display:block;color:var(--text);font:700 16px 'Space Grotesk',sans-serif;margin-bottom:7px}
.table-footer{padding:13px 19px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:12px;color:var(--muted);font-size:11px}
.modal-backdrop{position:fixed;inset:0;background:rgba(3,7,18,.72);backdrop-filter:blur(7px);display:none;align-items:center;justify-content:center;padding:20px;z-index:10}
.modal-backdrop.open{display:flex}
.modal{width:min(650px,100%);max-height:85vh;overflow:auto;background:#111b30;border:1px solid rgba(148,163,184,.22);border-radius:18px;box-shadow:0 30px 100px rgba(0,0,0,.5)}
.modal-head{display:flex;justify-content:space-between;align-items:center;padding:19px 22px;border-bottom:1px solid var(--line)}
.modal-head h2{font:700 17px 'Space Grotesk',sans-serif;margin:0}
.close-btn{width:31px;height:31px;border-radius:9px;border:1px solid var(--line);background:transparent;color:var(--muted);font-size:18px}
.modal-body{padding:21px 22px}
.detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:13px;margin-bottom:17px}
.detail-box{padding:12px;border:1px solid var(--line);background:rgba(148,163,184,.035);border-radius:10px;min-width:0}
.detail-label{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;font-weight:800;margin-bottom:7px}
.detail-value{font-size:12px;color:#e0e9f8;line-height:1.55;overflow-wrap:anywhere;white-space:pre-wrap}
.detail-section{margin-top:17px}
.detail-section .detail-value{padding:13px;background:rgba(148,163,184,.045);border:1px solid var(--line);border-radius:10px}
.footer-note{text-align:center;color:#60718e;font-size:10px;margin-top:25px}
body.light{--bg:#f2f5fb;--surface:#fff;--surface-2:#f6f8fc;--surface-3:#edf1f8;--line:rgba(51,65,85,.13);--text:#17233b;--muted:#71809a;--shadow:0 12px 35px rgba(32,53,91,.07);background:radial-gradient(ellipse at 12% 0%,rgba(100,130,230,.11),transparent 34%),#f2f5fb;color:var(--text)}
body.light .metric,body.light .panel{background:rgba(255,255,255,.92)}
body.light .brand-mark{color:#fff}
body.light .live-pill,body.light .icon-btn,body.light .secondary-btn{background:#fff;color:#33415b}
body.light .search-wrap input,body.light select{background:#f7f9fd;color:#25334d}
body.light .message-text,body.light .detail-value{color:#263653}
body.light .modal{background:#fff}
body.light .detail-box,body.light .detail-section .detail-value{background:#f7f9fd}
@media(max-width:1050px){.content-grid{grid-template-columns:1fr}.side-panel{display:grid;grid-template-columns:1fr 1fr;gap:22px}.side-divider{display:none}.priority-list{margin-top:18px}.category-list{align-content:start}}
@media(max-width:760px){.shell{padding:20px 15px 42px}.topbar{margin-bottom:30px}.hero{display:block}.run-meta{text-align:left;margin-top:15px}.metrics{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.metric{padding:15px}.metric-value{font-size:26px}.toolbar-top{align-items:flex-start;flex-direction:column}.controls{width:100%}.search-wrap{min-width:100%}.controls select{flex:1}.side-panel{grid-template-columns:1fr}.top-actions .live-pill{display:none}}
@media(max-width:420px){.metrics{grid-template-columns:1fr 1fr}.metric-value{font-size:23px}.brand-name{font-size:15px}.detail-grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="shell">
  <header class="topbar">
    <div class="brand">
      <div class="brand-mark">F</div>
      <div><div class="brand-name">FRONTLINE</div><div class="brand-sub">Support intelligence</div></div>
    </div>
    <div class="top-actions">
      <div class="live-pill"><span class="live-dot"></span> TRIAGE REPORT READY</div>
      <button class="icon-btn" id="theme-toggle" type="button" aria-label="Toggle light and dark theme">◐&nbsp; Theme</button>
      <button class="secondary-btn" id="export-btn" type="button">↓&nbsp; Export CSV</button>
    </div>
  </header>

  <section class="hero">
    <div>
      <div class="eyebrow">Customer operations / Overview</div>
      <h1>Message triage<br>at a glance.</h1>
      <p class="hero-copy">A clear view of incoming customer conversations, urgency levels and cases that need a human touch. Review, search and prioritise from one place.</p>
    </div>
    <div class="run-meta">
      <div>MODEL&nbsp; <strong id="model-name">__MODEL__</strong></div>
      <div>GENERATED&nbsp; <strong id="generated-at">__GENERATED_AT__</strong></div>
    </div>
  </section>

  <section class="metrics" aria-label="Triage summary">
    <article class="metric" style="--glow:rgba(124,156,255,.13)"><div class="metric-top">Total messages <span class="metric-icon">▤</span></div><div class="metric-value" id="stat-total">0</div><div class="metric-foot">Messages processed in this run</div></article>
    <article class="metric" style="--glow:rgba(251,113,133,.13)"><div class="metric-top">Human review <span class="metric-icon" style="color:#fb9aaa;background:rgba(251,113,133,.12)">◎</span></div><div class="metric-value" id="stat-human">0</div><div class="metric-foot" id="human-rate">Cases flagged for attention</div></article>
    <article class="metric" style="--glow:rgba(251,191,36,.13)"><div class="metric-top">Critical · P0 <span class="metric-icon" style="color:#fbbf24;background:rgba(251,191,36,.12)">!</span></div><div class="metric-value" id="stat-p0">0</div><div class="metric-foot">Highest urgency cases</div></article>
    <article class="metric" style="--glow:rgba(96,165,250,.13)"><div class="metric-top">High · P1 <span class="metric-icon" style="color:#60a5fa;background:rgba(96,165,250,.12)">↗</span></div><div class="metric-value" id="stat-p1">0</div><div class="metric-foot">High-priority cases</div></article>
  </section>

  <section class="content-grid">
    <aside class="panel side-panel">
      <div>
        <h2 class="panel-heading">Priority distribution</h2>
        <div class="panel-sub">How the workload is distributed</div>
        <div class="priority-list" id="priority-breakdown"></div>
      </div>
      <div>
        <div class="side-divider"></div>
        <h2 class="panel-heading">Detected categories</h2>
        <div class="panel-sub">Message topics in this run</div>
        <div class="category-list" id="category-breakdown"></div>
      </div>
    </aside>

    <main class="panel main-panel">
      <div class="toolbar">
        <div class="toolbar-top">
          <div><h2 class="panel-heading">Triage inbox</h2><div class="panel-sub">Explore individual decisions and recommended next steps</div></div>
          <div class="result-count"><strong id="visible-count">0</strong> results</div>
        </div>
        <div class="controls">
          <div class="search-wrap"><span class="search-icon">⌕</span><input id="search" type="search" placeholder="Search messages, IDs, categories..." autocomplete="off"></div>
          <select id="sort" aria-label="Sort results"><option value="original">Original order</option><option value="priority">Priority: highest first</option><option value="confidence-low">Confidence: lowest first</option><option value="confidence-high">Confidence: highest first</option></select>
        </div>
        <div class="filters" id="filters" style="margin-top:13px">
          <button class="filter-btn active" data-filter="all">All messages</button>
          <button class="filter-btn" data-filter="P0">P0 · Critical</button>
          <button class="filter-btn" data-filter="P1">P1 · High</button>
          <button class="filter-btn" data-filter="P2">P2 · Normal</button>
          <button class="filter-btn" data-filter="P3">P3 · Low</button>
          <button class="filter-btn" data-filter="human">Needs human</button>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Reference</th><th>Customer message</th><th>Category</th><th>Priority</th><th>Confidence</th><th>Review</th><th></th></tr></thead>
          <tbody id="rows"></tbody>
        </table>
        <div class="empty" id="empty" hidden><strong>No matching messages</strong>Try a different search term or filter.</div>
      </div>
      <div class="table-footer"><span id="footer-left">Showing 0 messages</span><span>Frontline triage console</span></div>
    </main>
  </section>
  <div class="footer-note">FRONTLINE &nbsp;·&nbsp; AI-ASSISTED CUSTOMER MESSAGE TRIAGE</div>
</div>

<div class="modal-backdrop" id="detail-modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <section class="modal">
    <header class="modal-head"><h2 id="modal-title">Message details</h2><button class="close-btn" id="close-modal" aria-label="Close details">×</button></header>
    <div class="modal-body" id="modal-content"></div>
  </section>
</div>

<script>
const DATA = __DATA_JSON__;
const PRIORITIES = ["P0", "P1", "P2", "P3"];
const PRIORITY_RANK = {P0:0, P1:1, P2:2, P3:3};
const PRIORITY_TONES = {P0:"#fb7185", P1:"#fbbf24", P2:"#60a5fa", P3:"#94a3b8"};
let activeFilter = "all";
let visibleRows = [];

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}
function decision(row) { return row && row.decision ? row.decision : {}; }
function confidence(row) {
  const n = Number(decision(row).confidence);
  return Number.isFinite(n) ? Math.max(0, Math.min(1, n)) : 0;
}
function priority(row) {
  const p = String(decision(row).priority || "P3").toUpperCase();
  return PRIORITY_RANK[p] === undefined ? "P3" : p;
}
function isHuman(row) { return decision(row).needs_human === true; }
function safeText(value) { return value === undefined || value === null ? "" : String(value); }

function updateOverview() {
  const total = DATA.length;
  const human = DATA.filter(isHuman).length;
  document.getElementById("stat-total").textContent = total;
  document.getElementById("stat-human").textContent = human;
  document.getElementById("stat-p0").textContent = DATA.filter(r => priority(r) === "P0").length;
  document.getElementById("stat-p1").textContent = DATA.filter(r => priority(r) === "P1").length;
  document.getElementById("human-rate").textContent = total ? Math.round(human / total * 100) + "% of all messages flagged" : "No messages in this run";

  const breakdown = document.getElementById("priority-breakdown");
  breakdown.replaceChildren();
  PRIORITIES.forEach(p => {
    const count = DATA.filter(r => priority(r) === p).length;
    const wrap = el("div");
    const head = el("div", "priority-head");
    const label = el("span", "priority-label");
    const dot = el("span", "priority-dot"); dot.style.setProperty("--tone", PRIORITY_TONES[p]);
    label.append(dot, document.createTextNode(p + (p === "P0" ? " · Critical" : p === "P1" ? " · High" : p === "P2" ? " · Normal" : " · Low")));
    head.append(label, el("span", "priority-count", count));
    const track = el("div", "track");
    const fill = el("div", "track-fill");
    fill.style.setProperty("--tone", PRIORITY_TONES[p]);
    fill.style.width = total ? (count / total * 100) + "%" : "0%";
    track.append(fill); wrap.append(head, track); breakdown.append(wrap);
  });

  const categories = {};
  DATA.forEach(r => {
    const c = safeText(decision(r).category || "other");
    categories[c] = (categories[c] || 0) + 1;
  });
  const categoryBox = document.getElementById("category-breakdown");
  categoryBox.replaceChildren();
  Object.entries(categories).sort((a,b) => b[1] - a[1]).forEach(([name,count]) => {
    const tag = el("div", "category-tag");
    tag.append(document.createTextNode(name.replaceAll("_", " ")));
    tag.append(el("span", "", count));
    categoryBox.append(tag);
  });
  if (!Object.keys(categories).length) categoryBox.append(el("span", "subtle", "No categories available"));
}

function matches(row, query) {
  const d = decision(row);
  const haystack = [row.id, row.input_text, d.category, d.summary, d.suggested_action, d.priority]
    .map(safeText).join(" ").toLowerCase();
  return haystack.includes(query);
}
function getFilteredRows() {
  const query = document.getElementById("search").value.trim().toLowerCase();
  let rows = DATA.filter(row => {
    const filterMatch = activeFilter === "all" || (activeFilter === "human" ? isHuman(row) : priority(row) === activeFilter);
    return filterMatch && matches(row, query);
  });
  const sort = document.getElementById("sort").value;
  if (sort === "priority") rows = rows.slice().sort((a,b) => PRIORITY_RANK[priority(a)] - PRIORITY_RANK[priority(b)]);
  if (sort === "confidence-low") rows = rows.slice().sort((a,b) => confidence(a) - confidence(b));
  if (sort === "confidence-high") rows = rows.slice().sort((a,b) => confidence(b) - confidence(a));
  return rows;
}
function render() {
  visibleRows = getFilteredRows();
  const tbody = document.getElementById("rows");
  tbody.replaceChildren();
  visibleRows.forEach(row => {
    const d = decision(row);
    const tr = el("tr");
    tr.append(el("td", "id-cell", row.id || "—"));
    const messageCell = el("td", "message-cell");
    messageCell.append(el("div", "message-text", row.input_text || "No message text"));
    tr.append(messageCell);
    const categoryCell = el("td"); categoryCell.append(el("span", "category", safeText(d.category || "other").replaceAll("_", " "))); tr.append(categoryCell);
    const pCell = el("td"); pCell.append(el("span", "priority " + priority(row), priority(row))); tr.append(pCell);
    const cCell = el("td");
    const cWrap = el("div", "confidence");
    const cTrack = el("span", "conf-track");
    const cFill = el("span", "conf-fill"); cFill.style.width = Math.round(confidence(row) * 100) + "%";
    cTrack.append(cFill); cWrap.append(cTrack, el("span", "", Math.round(confidence(row) * 100) + "%"));
    cCell.append(cWrap); tr.append(cCell);
    const humanCell = el("td", "", "");
    humanCell.append(isHuman(row) ? el("span", "human-flag", "● REVIEW") : el("span", "auto-flag", "✓ AUTO"));
    tr.append(humanCell);
    const actionCell = el("td");
    const view = el("button", "view-btn", "View details ↗");
    view.type = "button"; view.addEventListener("click", () => showDetails(row));
    actionCell.append(view); tr.append(actionCell);
    tbody.append(tr);
  });
  document.getElementById("empty").hidden = visibleRows.length !== 0;
  document.getElementById("visible-count").textContent = visibleRows.length;
  document.getElementById("footer-left").textContent = "Showing " + visibleRows.length + " of " + DATA.length + " messages";
}
function showDetails(row) {
  const d = decision(row);
  const content = document.getElementById("modal-content");
  content.replaceChildren();
  const grid = el("div", "detail-grid");
  const fields = [
    ["Reference", row.id], ["Category", safeText(d.category || "other").replaceAll("_", " ")],
    ["Priority", priority(row)], ["Confidence", Math.round(confidence(row) * 100) + "%"],
    ["Human review", isHuman(row) ? "Required" : "Not flagged"], ["Processing attempts", row.attempts]
  ];
  fields.forEach(([label,value]) => {
    const box = el("div", "detail-box");
    box.append(el("div", "detail-label", label), el("div", "detail-value", value === undefined || value === null ? "—" : value));
    grid.append(box);
  });
  content.append(grid);
  [["Original customer message", row.input_text], ["AI summary", d.summary], ["Suggested next action", d.suggested_action], ["Processing note", row.error]]
    .filter(item => item[1] !== undefined && item[1] !== null && item[1] !== "")
    .forEach(([label,value]) => {
      const section = el("section", "detail-section");
      section.append(el("div", "detail-label", label), el("div", "detail-value", value));
      content.append(section);
    });
  document.getElementById("detail-modal").classList.add("open");
}
function exportCSV() {
  const headers = ["id","input_text","category","priority","summary","suggested_action","needs_human","confidence"];
  const quote = value => '"' + safeText(value).replace(/"/g, '""') + '"';
  const lines = [headers.join(",")];
  visibleRows.forEach(row => {
    const d = decision(row);
    lines.push([row.id,row.input_text,d.category,d.priority,d.summary,d.suggested_action,d.needs_human,confidence(row)].map(quote).join(","));
  });
  const blob = new Blob(["\uFEFF" + lines.join("\r\n")], {type:"text/csv;charset=utf-8;"});
  const url = URL.createObjectURL(blob);
  const link = el("a"); link.href = url; link.download = "frontline-triage-export.csv";
  document.body.append(link); link.click(); link.remove(); URL.revokeObjectURL(url);
}

document.getElementById("filters").addEventListener("click", event => {
  const button = event.target.closest("button[data-filter]");
  if (!button) return;
  activeFilter = button.dataset.filter;
  document.querySelectorAll(".filter-btn").forEach(item => item.classList.toggle("active", item === button));
  render();
});
document.getElementById("search").addEventListener("input", render);
document.getElementById("sort").addEventListener("change", render);
document.getElementById("export-btn").addEventListener("click", exportCSV);
document.getElementById("theme-toggle").addEventListener("click", () => document.body.classList.toggle("light"));
document.getElementById("close-modal").addEventListener("click", () => document.getElementById("detail-modal").classList.remove("open"));
document.getElementById("detail-modal").addEventListener("click", event => {
  if (event.target.id === "detail-modal") event.currentTarget.classList.remove("open");
});
document.addEventListener("keydown", event => {
  if (event.key === "Escape") document.getElementById("detail-modal").classList.remove("open");
});
updateOverview();
render();
</script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Generate the Frontline triage dashboard.")
    parser.add_argument("--results", default="results.json", help="Path to triage results JSON")
    parser.add_argument("--output", default="dashboard.html", help="Output HTML file")
    args = parser.parse_args()

    with open(args.results, "r", encoding="utf-8") as file:
        payload = json.load(file)

    results = payload.get("results", [])
    if not isinstance(results, list):
        raise ValueError("The 'results' field must be a JSON array.")

    safe_json = json.dumps(results, ensure_ascii=False)
    # Prevent customer-controlled text from terminating the embedded script tag.
    safe_json = safe_json.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

    html = TEMPLATE
    html = html.replace("__DATA_JSON__", safe_json)
    html = html.replace("__MODEL__", str(payload.get("model", "Unknown model")))
    html = html.replace("__GENERATED_AT__", str(payload.get("generated_at", "Unknown")))
    output_path = Path(args.output)
    output_path.write_text(html, encoding="utf-8")
    print(f"Dashboard generated: {output_path.resolve()}")


if __name__ == "__main__":
    main()
