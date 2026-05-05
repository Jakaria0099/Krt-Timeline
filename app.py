import streamlit as st
import json
import os

st.set_page_config(
    page_title="Chronograph",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DATA_FILE = "timeline_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"branches": []}

if "data" not in st.session_state:
    st.session_state.data = load_data()

timeline_json = json.dumps(st.session_state.data)

# Jewel-toned, desaturated palette — cohesive across the page
BRANCH_COLORS = [
    "#88a892",  # sage
    "#c4a36a",  # ochre
    "#9d7da3",  # plum
    "#7d8db5",  # slate blue
    "#c08580",  # dusty rose
    "#b8856b",  # terracotta
    "#6ba39c",  # teal-sage
    "#a89478",  # taupe
    "#c4787d",  # rose-red
    "#8b9bc4",  # periwinkle
]

HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,400&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&family=JetBrains+Mono:ital,wght@0,300;0,400;0,500;1,300&display=swap');

*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}

:root{{
  --bg-deep:#06060c;
  --bg-mid:#0c0c1a;
  --bg-soft:#12122a;
  --fg:#e8e6dc;
  --fg-mute:#8a8780;
  --fg-faint:#48464a;
  --fg-ghost:#28282e;
  --accent:#c4a36a;
  --accent-soft:#c4a36a44;
  --rule:#1a1a28;
  --serif:'Fraunces',Georgia,serif;
  --sans:'DM Sans',system-ui,sans-serif;
  --mono:'JetBrains Mono',monospace;
}}

body{{
  background:var(--bg-deep);
  color:var(--fg);
  font-family:var(--sans);
  overflow:hidden;
  width:100vw;height:100vh;
  -webkit-font-smoothing:antialiased;
}}

/* ── Atmospheric background — soft radial + faint grain ── */
#atmosphere{{
  position:fixed;inset:0;
  background:
    radial-gradient(ellipse 90% 60% at 50% 45%, #14142a 0%, #0a0a18 50%, #06060c 100%);
  pointer-events:none;
  z-index:0;
}}
#atmosphere::after{{
  content:'';position:absolute;inset:0;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.08'/%3E%3C/svg%3E");
  mix-blend-mode:overlay;opacity:.4;
}}

/* ── Header strip ── */
#header{{
  position:fixed;top:0;left:0;right:0;height:54px;
  display:flex;align-items:center;padding:0 24px;gap:16px;
  background:linear-gradient(180deg,#06060c 0%,#06060ce0 70%,transparent 100%);
  z-index:300;
}}
#brand{{
  font-family:var(--serif);font-style:italic;font-weight:400;
  font-size:18px;color:var(--fg);letter-spacing:.005em;
}}
#brand .glyph{{
  font-style:normal;color:var(--accent);margin-right:8px;
  font-family:var(--mono);font-size:14px;
}}
#brand .sub{{
  font-family:var(--mono);font-size:9px;font-style:normal;
  color:var(--fg-mute);letter-spacing:.18em;text-transform:uppercase;
  margin-left:14px;padding-left:14px;border-left:1px solid var(--rule);
}}
.tb-spacer{{flex:1}}
.tb-btn{{
  font-family:var(--mono);font-size:10px;letter-spacing:.1em;
  text-transform:uppercase;padding:7px 14px;border-radius:0;
  cursor:pointer;border:1px solid var(--rule);
  background:transparent;color:var(--fg-mute);
  transition:border-color .2s,color .2s,background .2s;
}}
.tb-btn:hover{{border-color:var(--accent-soft);color:var(--fg);background:#12122a55}}
.tb-btn.primary{{
  border-color:var(--accent-soft);color:var(--accent);
}}
.tb-btn.primary:hover{{
  background:var(--accent);color:#06060c;border-color:var(--accent);
}}

/* ── 3D scene wrapper ── */
#scene{{
  position:fixed;top:54px;left:0;right:0;bottom:88px;
  perspective:2000px;perspective-origin:50% 50%;
  z-index:1;overflow:hidden;
}}
#stage{{
  position:absolute;inset:0;
  transform-style:preserve-3d;
  transform:rotateX(6deg);
  transform-origin:50% 50%;
}}
#canvas{{
  position:absolute;inset:0;
  cursor:grab;
}}
#canvas.dragging{{cursor:grabbing}}

/* ── Empty state ── */
#empty{{
  position:absolute;left:50%;top:50%;
  transform:translate(-50%,-50%);
  text-align:center;pointer-events:none;
  z-index:50;
}}
#empty .glyph{{
  font-family:var(--mono);color:var(--accent);font-size:11px;
  letter-spacing:.4em;margin-bottom:14px;opacity:.6;
}}
#empty .title{{
  font-family:var(--serif);font-style:italic;font-weight:300;
  font-size:34px;color:var(--fg);letter-spacing:-.01em;
  line-height:1.1;margin-bottom:10px;
}}
#empty .sub{{
  font-family:var(--sans);font-size:12px;color:var(--fg-mute);
  letter-spacing:.04em;line-height:1.7;max-width:380px;margin:0 auto;
}}
#empty .arrow{{
  font-family:var(--mono);color:var(--fg-faint);font-size:10px;
  letter-spacing:.15em;margin-top:24px;
}}

/* ── Event cards (3D float) ── */
.ecard{{
  position:absolute;background:#0d0d1c;
  border:1px solid #20203a;border-radius:2px;
  padding:18px 20px 16px;width:320px;
  font-family:var(--sans);font-size:12px;line-height:1.65;
  pointer-events:all;z-index:200;
  box-shadow:
    0 24px 60px -12px rgba(0,0,0,.7),
    0 4px 10px rgba(0,0,0,.4),
    inset 0 1px 0 rgba(255,255,255,.04);
  animation:cardIn .25s cubic-bezier(.34,1.56,.64,1);
  transform-origin:50% 0;
}}
.ecard::before{{
  content:'';position:absolute;left:0;top:0;width:2px;height:100%;
  background:var(--card-color,var(--accent));
  opacity:.85;
}}
@keyframes cardIn{{
  from{{opacity:0;transform:translateY(8px) scale(.96)}}
  to  {{opacity:1;transform:translateY(0)   scale(1)}}
}}
.card-h{{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}}
.card-eyebrow{{
  font-family:var(--mono);font-size:9px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--card-color,var(--accent));
  opacity:.7;margin-bottom:6px;
  display:flex;align-items:center;gap:8px;flex-wrap:wrap;
}}
.card-title{{
  font-family:var(--serif);font-weight:400;font-size:17px;
  color:var(--fg);line-height:1.2;letter-spacing:-.01em;
}}
.card-meta{{
  font-family:var(--mono);font-size:10px;color:var(--fg-mute);
  letter-spacing:.06em;margin-top:6px;
}}
.card-desc{{
  font-size:12px;color:#a8a6a0;line-height:1.7;
  margin:14px 0 12px;font-weight:300;
}}
.card-link{{
  display:inline-flex;align-items:center;gap:7px;
  font-family:var(--mono);font-size:10px;
  color:var(--card-color,var(--accent));text-decoration:none;
  border:1px solid currentColor;padding:7px 11px;
  margin-top:6px;letter-spacing:.04em;
  transition:background .2s,color .2s;cursor:pointer;
  word-break:break-all;
}}
.card-link:hover{{background:var(--card-color,var(--accent));color:#06060c;}}
.card-x{{
  font-family:var(--mono);font-size:14px;cursor:pointer;
  color:var(--fg-faint);line-height:1;padding:2px 4px;
  transition:color .15s;
}}
.card-x:hover{{color:var(--fg)}}
.card-rule{{height:1px;background:var(--rule);margin:14px 0 12px}}

.card-field{{
  width:100%;background:#08081a;border:1px solid var(--rule);
  border-radius:0;color:var(--fg);font-family:var(--mono);
  font-size:11px;padding:7px 9px;margin-bottom:8px;
  resize:vertical;transition:border-color .2s;
}}
.card-field:focus{{outline:none;border-color:var(--card-color,var(--accent))}}
.card-field-l{{
  font-family:var(--mono);font-size:9px;letter-spacing:.16em;
  color:var(--fg-faint);margin-bottom:4px;text-transform:uppercase;
}}
.card-acts{{display:flex;gap:8px;margin-top:14px}}
.btn{{
  flex:1;font-family:var(--mono);font-size:10px;letter-spacing:.1em;
  padding:8px;cursor:pointer;text-transform:uppercase;
  border:1px solid var(--rule);background:transparent;color:var(--fg-mute);
  transition:all .2s;border-radius:0;
}}
.btn:hover{{border-color:var(--fg-mute);color:var(--fg)}}
.btn.primary{{
  border-color:var(--card-color,var(--accent));
  color:var(--card-color,var(--accent));
}}
.btn.primary:hover{{
  background:var(--card-color,var(--accent));color:#06060c;
}}
.btn.danger{{color:#c4787d;border-color:#c4787d44}}
.btn.danger:hover{{background:#c4787d;color:#06060c;border-color:#c4787d}}

/* ── Side panels ── */
.panel{{
  position:fixed;right:0;top:54px;bottom:88px;width:340px;
  background:linear-gradient(180deg,#0a0a1a 0%,#08081a 100%);
  border-left:1px solid var(--rule);
  padding:28px 24px;overflow-y:auto;z-index:280;
  transform:translateX(100%);
  transition:transform .35s cubic-bezier(.4,0,.2,1);
  box-shadow:-24px 0 60px rgba(0,0,0,.5);
}}
.panel.open{{transform:translateX(0)}}
.panel h2{{
  font-family:var(--serif);font-style:italic;font-weight:300;
  font-size:24px;color:var(--fg);margin-bottom:6px;letter-spacing:-.01em;
}}
.panel h2 + .sub{{
  font-family:var(--mono);font-size:9px;color:var(--fg-mute);
  letter-spacing:.18em;text-transform:uppercase;margin-bottom:24px;
}}
.panel-l{{
  font-family:var(--mono);font-size:9px;letter-spacing:.16em;
  color:var(--fg-faint);margin-bottom:5px;text-transform:uppercase;
}}
.panel-f{{
  width:100%;background:#06060c;border:1px solid var(--rule);
  color:var(--fg);font-family:var(--mono);font-size:12px;
  padding:10px 12px;margin-bottom:16px;border-radius:0;
  resize:vertical;transition:border-color .2s;
}}
.panel-f:focus{{outline:none;border-color:var(--accent)}}
select.panel-f{{cursor:pointer}}
.panel-btn{{
  width:100%;font-family:var(--mono);font-size:11px;letter-spacing:.1em;
  padding:12px;cursor:pointer;margin-top:6px;text-transform:uppercase;
  border-radius:0;transition:all .2s;
}}
.panel-btn.primary{{
  background:var(--accent);border:1px solid var(--accent);color:#06060c;font-weight:500;
}}
.panel-btn.primary:hover{{background:#d4b27a;border-color:#d4b27a}}
.panel-btn.cancel{{
  background:transparent;border:1px solid var(--rule);color:var(--fg-mute);
  margin-top:10px;
}}
.panel-btn.cancel:hover{{border-color:var(--fg-mute);color:var(--fg)}}

/* ── Bottom universal scale ── */
#scale{{
  position:fixed;left:0;right:0;bottom:0;height:88px;
  background:linear-gradient(0deg,#06060c 0%,#06060cdd 80%,transparent 100%);
  border-top:1px solid var(--rule);
  z-index:200;
  display:flex;flex-direction:column;
}}
#scale-rows{{
  flex:1;position:relative;
}}
#scale-controls{{
  height:30px;display:flex;align-items:center;
  padding:0 20px;gap:16px;
  border-top:1px solid var(--rule);background:#04040a;
}}
.zoom-label{{
  font-family:var(--mono);font-size:9px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--fg-faint);
}}
.zoom-track{{
  flex:1;height:1px;background:var(--rule);position:relative;
  max-width:280px;cursor:pointer;
}}
.zoom-stops{{
  display:flex;justify-content:space-between;
  position:absolute;top:-3px;left:0;right:0;height:7px;
}}
.zoom-stop{{
  width:7px;height:7px;border:1px solid var(--rule);
  background:var(--bg-deep);cursor:pointer;
  transition:all .2s;
}}
.zoom-stop.active{{
  background:var(--accent);border-color:var(--accent);
  transform:scale(1.3);
}}
.zoom-stop:hover{{border-color:var(--fg-mute)}}
.zoom-level-name{{
  font-family:var(--mono);font-size:9px;letter-spacing:.18em;
  text-transform:uppercase;color:var(--fg-mute);min-width:60px;
}}
#scale-info{{
  font-family:var(--mono);font-size:9px;letter-spacing:.1em;
  color:var(--fg-faint);margin-left:auto;
}}
.scale-row{{
  position:absolute;left:0;right:0;display:flex;
  pointer-events:none;
}}
.scale-tier-major{{top:8px;height:22px}}
.scale-tier-minor{{top:32px;height:22px}}
.scale-tick{{
  position:absolute;display:flex;align-items:center;
  white-space:nowrap;
}}
.scale-tick.major{{
  font-family:var(--serif);font-style:italic;font-size:14px;
  color:var(--fg);font-weight:300;
}}
.scale-tick.minor{{
  font-family:var(--mono);font-size:9px;letter-spacing:.1em;
  color:var(--fg-mute);text-transform:uppercase;
}}
.scale-tick-line{{
  position:absolute;width:1px;background:var(--rule);
  top:-100vh;height:100vh;
}}
.scale-tick-line.heavy{{background:#262640}}

#tt{{
  position:fixed;background:#0d0d1c;border:1px solid var(--rule);
  border-left:2px solid var(--accent);
  padding:7px 12px;font-family:var(--mono);font-size:10px;
  color:var(--fg);pointer-events:none;opacity:0;
  transition:opacity .12s;white-space:nowrap;z-index:500;
  box-shadow:0 8px 20px rgba(0,0,0,.5);letter-spacing:.04em;
}}
</style>
</head>
<body>

<div id="atmosphere"></div>

<!-- Header -->
<div id="header">
  <div id="brand">
    <span class="glyph">◈</span>Chronograph<span class="sub">task timeline</span>
  </div>
  <div class="tb-spacer"></div>
  <button class="tb-btn primary" onclick="openNewBranch()">＋ New branch</button>
  <button class="tb-btn" onclick="openNewEvent(null)">＋ Add event</button>
  <button class="tb-btn" onclick="exportData()">⬇ Export</button>
  <button class="tb-btn" onclick="document.getElementById('import-file').click()">⬆ Import</button>
  <input type="file" id="import-file" accept=".json" style="display:none" onchange="importData(this)">
</div>

<!-- 3D Scene -->
<div id="scene">
  <div id="stage">
    <svg id="canvas" xmlns="http://www.w3.org/2000/svg"></svg>
    <div id="empty">
      <div class="glyph">◈</div>
      <div class="title">An empty timeline</div>
      <div class="sub">A horizontal axis of time, awaiting your first task. Each branch you add becomes a thread of work — extend it as updates arrive.</div>
      <div class="arrow">↑ begin with «new branch»</div>
    </div>
  </div>
</div>

<!-- Bottom universal time scale -->
<div id="scale">
  <div id="scale-rows"></div>
  <div id="scale-controls">
    <span class="zoom-label">scale</span>
    <span class="zoom-level-name" id="zoom-name">months</span>
    <div class="zoom-track">
      <div class="zoom-stops" id="zoom-stops"></div>
    </div>
    <span id="scale-info"></span>
  </div>
</div>

<!-- New Branch Panel -->
<div class="panel" id="panel-branch">
  <h2>New branch</h2>
  <div class="sub">a new task thread</div>
  <div class="panel-l">Person</div>
  <input class="panel-f" id="nb-person" placeholder="e.g. Prof. Al-Hassan">
  <div class="panel-l">Task title</div>
  <input class="panel-f" id="nb-title" placeholder="e.g. Coding system for forms">
  <div class="panel-l">Date</div>
  <input class="panel-f" id="nb-date" type="date">
  <div class="panel-l">Form of request</div>
  <select class="panel-f" id="nb-form">
    <option>Email</option><option>Teams Call</option><option>Meeting</option>
    <option>In Person</option><option>Team Message</option><option>Other</option>
  </select>
  <div class="panel-l">Priority</div>
  <select class="panel-f" id="nb-priority">
    <option value="">—</option><option>High</option><option>Medium</option><option>Low</option>
  </select>
  <div class="panel-l">Description</div>
  <textarea class="panel-f" id="nb-desc" rows="3" placeholder="What was requested?"></textarea>
  <div class="panel-l">SharePoint link</div>
  <input class="panel-f" id="nb-link" placeholder="https://…">
  <div class="panel-l">Link label</div>
  <input class="panel-f" id="nb-linklabel" placeholder="e.g. document-v1.xlsx">
  <div class="panel-l">Time taken</div>
  <input class="panel-f" id="nb-time" placeholder="e.g. 30 mins">
  <button class="panel-btn primary" onclick="submitNewBranch()">Create branch</button>
  <button class="panel-btn cancel" onclick="closePanel('panel-branch')">Cancel</button>
</div>

<!-- New Event Panel -->
<div class="panel" id="panel-event">
  <h2>Add event</h2>
  <div class="sub">extend an existing branch</div>
  <div class="panel-l">Branch</div>
  <select class="panel-f" id="ne-branch"></select>
  <div class="panel-l">Date</div>
  <input class="panel-f" id="ne-date" type="date">
  <div class="panel-l">Form / type</div>
  <select class="panel-f" id="ne-form">
    <option>Email</option><option>Teams Call</option><option>Meeting</option>
    <option>In Person</option><option>Team Message</option>
    <option>Follow-up</option><option>Completed</option><option>Note</option><option>Other</option>
  </select>
  <div class="panel-l">Priority</div>
  <select class="panel-f" id="ne-priority">
    <option value="">—</option><option>High</option><option>Medium</option><option>Low</option>
  </select>
  <div class="panel-l">Title</div>
  <input class="panel-f" id="ne-title" placeholder="Short summary">
  <div class="panel-l">Notes</div>
  <textarea class="panel-f" id="ne-desc" rows="3" placeholder="Details…"></textarea>
  <div class="panel-l">SharePoint link</div>
  <input class="panel-f" id="ne-link" placeholder="https://…">
  <div class="panel-l">Link label</div>
  <input class="panel-f" id="ne-linklabel" placeholder="e.g. minutes.docx">
  <div class="panel-l">Time taken</div>
  <input class="panel-f" id="ne-time" placeholder="e.g. 1.5 hours">
  <button class="panel-btn primary" onclick="submitNewEvent()">Add event</button>
  <button class="panel-btn cancel" onclick="closePanel('panel-event')">Cancel</button>
</div>

<div id="tt"></div>

<script>
const COLORS = {json.dumps(BRANCH_COLORS)};
let DATA = {timeline_json};

// Restore from localStorage
try{{
  const saved = localStorage.getItem('chronograph_v2');
  if(saved){{const p = JSON.parse(saved); if(p.branches) DATA = p;}}
}}catch(e){{}}

const SVG_NS = 'http://www.w3.org/2000/svg';
const svg = document.getElementById('canvas');
const stage = document.getElementById('stage');

// ── State ─────────────────────────────────────────────────────────────────────
let panX = 0;
let isDragging = false, dragStart = {{x:0,y:0}}, panStart = 0;
let openCards = {{}};
let zoomLevel = 2;          // 0=year, 1=quarter, 2=month, 3=week, 4=day
const ZOOM_LEVELS = [
  {{name:'years',  pxPerDay: 1.5, majorUnit:'year',  minorUnit:'quarter'}},
  {{name:'quarters', pxPerDay: 4,  majorUnit:'year',  minorUnit:'quarter'}},
  {{name:'months', pxPerDay: 12, majorUnit:'year',  minorUnit:'month'}},
  {{name:'weeks',  pxPerDay: 32, majorUnit:'month', minorUnit:'week'}},
  {{name:'days',   pxPerDay: 80, majorUnit:'month', minorUnit:'day'}},
];

const AXIS_FRAC = 0.50;     // axis sits in middle of 3D scene
const NODE_R = 7;
const MARGIN = 200;

// ── Date helpers ──────────────────────────────────────────────────────────────
const parse = s => new Date(s + 'T12:00:00');
const today = () => new Date().toISOString().slice(0,10);
const fmtDate = d => d.toLocaleDateString('en-GB',{{day:'numeric',month:'short',year:'numeric'}});

function dateRange() {{
  const all = DATA.branches.flatMap(b => b.events.map(e => parse(e.date)));
  const today_ = new Date();
  if (!all.length) {{
    return {{
      min: new Date(today_.getFullYear(), today_.getMonth()-3, 1),
      max: new Date(today_.getFullYear(), today_.getMonth()+3, 1),
    }};
  }}
  const mn = new Date(Math.min(...all)), mx = new Date(Math.max(...all));
  mn.setMonth(mn.getMonth()-2); mx.setMonth(mx.getMonth()+2);
  return {{min: mn, max: mx}};
}}

function pxPerDay() {{ return ZOOM_LEVELS[zoomLevel].pxPerDay; }}
function totalW(dr) {{
  const days = (dr.max - dr.min) / 864e5;
  return Math.max(window.innerWidth*1.5, days * pxPerDay() + MARGIN*2);
}}
function d2x(dateStr, dr, tw) {{
  const days = (parse(dateStr) - dr.min) / 864e5;
  return MARGIN + days * pxPerDay() + panX;
}}

// ── SVG helper ────────────────────────────────────────────────────────────────
function se(tag, a, p) {{
  const e = document.createElementNS(SVG_NS, tag);
  Object.entries(a).forEach(([k,v]) => e.setAttribute(k, v));
  p && p.appendChild(e);
  return e;
}}

// ── Lane assignment (anti-overlap) ───────────────────────────────────────────
function assignLanes(branches, dr, tw) {{
  // For each branch compute its date span (first → last event x)
  const enriched = branches.map((b, idx) => {{
    const evs = [...b.events].sort((a,c) => a.date.localeCompare(c.date));
    if (!evs.length) return null;
    const x0 = d2x(evs[0].date, dr, tw);
    const x1 = d2x(evs[evs.length-1].date, dr, tw);
    // label width estimate: longest of person + task_title
    const labelW = Math.max(120, (b.person.length + 4) * 8);
    return {{idx, branch: b, evs, x0, x1, xRange:[x0-20, Math.max(x1, x0+labelW)+40]}};
  }}).filter(Boolean);

  // sort by x0 ascending
  enriched.sort((a,c) => a.x0 - c.x0);

  // Alternate up / down, packing into lanes per side
  const upLanes = []; const downLanes = [];
  enriched.forEach((e, i) => {{
    const side = (i % 2 === 0) ? 'up' : 'down';
    const lanes = side === 'up' ? upLanes : downLanes;
    let placed = false;
    for (let l = 0; l < lanes.length; l++) {{
      const lastX = lanes[l];
      if (e.xRange[0] > lastX) {{
        lanes[l] = e.xRange[1];
        e.lane = l; e.side = side; placed = true; break;
      }}
    }}
    if (!placed) {{
      lanes.push(e.xRange[1]);
      e.lane = lanes.length - 1; e.side = side;
    }}
  }});

  return enriched;
}}

// ── Render ────────────────────────────────────────────────────────────────────
function render() {{
  const W = window.innerWidth, H = document.getElementById('scene').clientHeight;
  svg.setAttribute('width', W);
  svg.setAttribute('height', H);
  while (svg.firstChild) svg.removeChild(svg.firstChild);

  const dr = dateRange(), tw = totalW(dr);
  const ay = H * AXIS_FRAC;

  // Empty state visibility
  document.getElementById('empty').style.display = DATA.branches.length ? 'none' : 'block';

  // Defs: glow filter, axis gradient
  const defs = se('defs', {{}}, svg);
  // axis glow
  const grad = se('linearGradient', {{id:'axisGlow', x1:'0%', y1:'0%', x2:'100%', y2:'0%'}}, defs);
  se('stop', {{offset:'0%', 'stop-color':'#c4a36a', 'stop-opacity':'0'}}, grad);
  se('stop', {{offset:'15%', 'stop-color':'#c4a36a', 'stop-opacity':'.5'}}, grad);
  se('stop', {{offset:'50%', 'stop-color':'#c4a36a', 'stop-opacity':'.8'}}, grad);
  se('stop', {{offset:'85%', 'stop-color':'#c4a36a', 'stop-opacity':'.5'}}, grad);
  se('stop', {{offset:'100%', 'stop-color':'#c4a36a', 'stop-opacity':'0'}}, grad);

  // node radial (3D sphere effect)
  COLORS.forEach((c, i) => {{
    const rg = se('radialGradient', {{id:'nodeR'+i, cx:'30%', cy:'30%', r:'70%'}}, defs);
    se('stop', {{offset:'0%', 'stop-color':lighten(c, 35)}}, rg);
    se('stop', {{offset:'60%', 'stop-color':c}}, rg);
    se('stop', {{offset:'100%', 'stop-color':darken(c, 30)}}, rg);
  }});

  // Background grid lines (from scale ticks) — drawn first, behind everything
  drawGridLines(W, H, ay, dr, tw);

  // Main timeline axis — soft glowing ribbon
  drawAxis(W, H, ay, dr, tw);

  // Branches
  const lanes = assignLanes(DATA.branches, dr, tw);
  lanes.forEach(le => drawBranch(le, ay, H, dr, tw));

  // Update bottom scale
  renderScale(W, dr, tw);
  updateZoomStops();
}}

function drawAxis(W, H, ay, dr, tw) {{
  // soft glow band
  se('rect', {{
    x: panX, y: ay-3, width: tw, height: 6,
    fill: 'url(#axisGlow)', opacity: '.18'
  }}, svg);
  // crisp line
  se('line', {{
    x1: panX, y1: ay, x2: panX+tw, y2: ay,
    stroke: '#c4a36a', 'stroke-width': '1', opacity: '.55'
  }}, svg);
  // tick marks every period (drawn by scale, but we add small marks here)

  // Today marker
  const todayX = d2x(today(), dr, tw);
  if (todayX > 0 && todayX < W) {{
    se('line', {{
      x1: todayX, y1: ay-22, x2: todayX, y2: ay+22,
      stroke: '#c4a36a', 'stroke-width': '1.5', opacity: '.9'
    }}, svg);
    se('circle', {{cx: todayX, cy: ay, r: '4', fill:'#c4a36a', opacity:'.9'}}, svg);
    const tlbl = se('text', {{
      x: todayX, y: ay+38,
      'font-family': "'JetBrains Mono',monospace",
      'font-size': '9', 'text-anchor':'middle', fill:'#c4a36a',
      'letter-spacing': '.15em'
    }}, svg);
    tlbl.textContent = 'TODAY';
  }}
}}

function drawGridLines(W, H, ay, dr, tw) {{
  // Major and minor ticks aligned with the bottom scale
  const z = ZOOM_LEVELS[zoomLevel];
  const ticks = computeTicks(dr, z);
  ticks.major.forEach(t => {{
    const x = d2x(t.iso, dr, tw);
    if (x > -10 && x < W + 10) {{
      se('line', {{
        x1: x, y1: 0, x2: x, y2: H,
        stroke: '#1a1a30', 'stroke-width': '1', opacity: '.6'
      }}, svg);
    }}
  }});
  ticks.minor.forEach(t => {{
    const x = d2x(t.iso, dr, tw);
    if (x > -10 && x < W + 10) {{
      se('line', {{
        x1: x, y1: 0, x2: x, y2: H,
        stroke: '#0e0e1e', 'stroke-width': '1', 'stroke-dasharray': '2 6'
      }}, svg);
    }}
  }});
}}

function drawBranch(le, ay, H, dr, tw) {{
  const {{idx, branch, evs, side, lane}} = le;
  const dir = side === 'up' ? -1 : 1;
  const baseGap = 70;
  const laneGap = 60;
  const stem = baseGap + lane * laneGap + Math.min(evs.length * 6, 30);
  const nodeY = ay + dir * stem;
  const colorIdx = idx % COLORS.length;
  const col = branch.color || COLORS[colorIdx];

  const x0 = d2x(evs[0].date, dr, tw);
  const xLast = d2x(evs[evs.length-1].date, dr, tw);

  // Vertical stem from axis (subtle gradient: opaque near node, fading to axis)
  const stemId = 'stem-' + idx;
  const stemGrad = se('linearGradient', {{
    id: stemId, x1:'0%', y1: dir<0?'100%':'0%', x2:'0%', y2: dir<0?'0%':'100%'
  }}, svg.querySelector('defs'));
  se('stop', {{offset:'0%', 'stop-color':col, 'stop-opacity':'.15'}}, stemGrad);
  se('stop', {{offset:'100%', 'stop-color':col, 'stop-opacity':'.65'}}, stemGrad);

  se('line', {{
    x1: x0, y1: ay, x2: x0, y2: nodeY,
    stroke: 'url(#'+stemId+')', 'stroke-width': '1.5'
  }}, svg);

  // Horizontal run if multiple events
  if (evs.length > 1) {{
    se('line', {{
      x1: x0, y1: nodeY, x2: xLast, y2: nodeY,
      stroke: col, 'stroke-width': '1', opacity: '.55'
    }}, svg);
  }}

  // Branch label group — placed on the FAR side of the nodes (away from axis)
  const labelY = nodeY + dir * 30;
  // anchor tick connecting label to branch
  se('line', {{
    x1: x0, y1: nodeY + dir*8, x2: x0, y2: labelY - dir*4,
    stroke: col, 'stroke-width': '0.5', opacity: '.4'
  }}, svg);

  const lg = se('g', {{style:'cursor:pointer'}}, svg);
  // person — serif italic
  const personEl = se('text', {{
    x: x0, y: labelY,
    'font-family': "'Fraunces',serif", 'font-style':'italic',
    'font-weight': '400', 'font-size': '15',
    'text-anchor': 'middle', fill: col, 'letter-spacing':'-.005em',
  }}, lg);
  personEl.textContent = branch.person;
  // task title — mono small
  const taskEl = se('text', {{
    x: x0, y: labelY + dir * 16,
    'font-family': "'JetBrains Mono',monospace",
    'font-size': '9', 'text-anchor':'middle',
    fill: col, opacity: '.55', 'letter-spacing':'.08em',
  }}, lg);
  taskEl.textContent = (branch.task_title || '').slice(0, 36).toUpperCase();
  // small + button to add event
  const addBtn = se('text', {{
    x: x0, y: labelY + dir * 32,
    'font-family': "'JetBrains Mono',monospace",
    'font-size': '13', 'text-anchor':'middle',
    fill: col, opacity: '.4', style: 'cursor:pointer'
  }}, lg);
  addBtn.textContent = '＋';
  addBtn.addEventListener('mouseenter', () => addBtn.setAttribute('opacity', '1'));
  addBtn.addEventListener('mouseleave', () => addBtn.setAttribute('opacity', '.4'));
  addBtn.addEventListener('click', e => {{ e.stopPropagation(); openNewEvent(branch.id); }});

  // Event nodes
  evs.forEach((ev, ei) => {{
    const nx = d2x(ev.date, dr, tw);
    const ny = nodeY;

    // Drop line from axis to subbranch node (for events after first)
    if (ei > 0) {{
      se('line', {{
        x1: nx, y1: ay, x2: nx, y2: ny,
        stroke: col, 'stroke-width': '0.5',
        opacity: '.18', 'stroke-dasharray': '1 4'
      }}, svg);
    }}

    // Tiny axis-tick where the branch meets the timeline
    if (ei === 0) {{
      se('circle', {{cx: nx, cy: ay, r: '2.5', fill: col, opacity: '.55'}}, svg);
    }}

    const isOpen = !!openCards[ev.id];
    const g = se('g', {{style:'cursor:pointer'}}, svg);
    if (isOpen) {{
      // glow halo
      se('circle', {{
        cx: nx, cy: ny, r: NODE_R + 8,
        fill: col, opacity: '.12'
      }}, g);
      se('circle', {{
        cx: nx, cy: ny, r: NODE_R + 4,
        fill: 'none', stroke: col, 'stroke-width': '1', opacity: '.4'
      }}, g);
    }}

    // Node — radial gradient for 3D sphere
    se('circle', {{
      cx: nx, cy: ny, r: NODE_R,
      fill: 'url(#nodeR' + colorIdx + ')',
      stroke: lighten(col, 20), 'stroke-width': '1', opacity: '.95'
    }}, g);
    // tiny inner highlight
    se('circle', {{cx: nx-2, cy: ny-2, r: '1.5', fill:'#fff', opacity:'.3'}}, g);

    g.addEventListener('mouseenter', e => {{
      const tt = document.getElementById('tt');
      tt.textContent = ev.title + '  ·  ' + fmtDate(parse(ev.date));
      tt.style.left = (e.clientX + 14) + 'px';
      tt.style.top = (e.clientY - 12) + 'px';
      tt.style.opacity = '1';
    }});
    g.addEventListener('mouseleave', () => {{
      document.getElementById('tt').style.opacity = '0';
    }});
    g.addEventListener('click', e => {{
      e.stopPropagation();
      toggleCard(ev, branch, nx, ny, dir, col);
    }});
  }});
}}

// ── Bottom universal scale ────────────────────────────────────────────────────
function computeTicks(dr, z) {{
  const major = [], minor = [];
  const start = new Date(dr.min), end = new Date(dr.max);

  function addMajor(d, label) {{
    major.push({{iso: d.toISOString().slice(0,10), date: new Date(d), label}});
  }}
  function addMinor(d, label) {{
    minor.push({{iso: d.toISOString().slice(0,10), date: new Date(d), label}});
  }}

  // Major ticks
  if (z.majorUnit === 'year') {{
    let d = new Date(start.getFullYear(), 0, 1);
    while (d <= end) {{
      if (d >= start) addMajor(d, d.getFullYear().toString());
      d.setFullYear(d.getFullYear() + 1);
    }}
  }} else if (z.majorUnit === 'month') {{
    let d = new Date(start.getFullYear(), start.getMonth(), 1);
    while (d <= end) {{
      if (d >= start) addMajor(d, d.toLocaleDateString('en-GB',{{month:'long',year:'numeric'}}));
      d.setMonth(d.getMonth() + 1);
    }}
  }}

  // Minor ticks
  if (z.minorUnit === 'quarter') {{
    let d = new Date(start.getFullYear(), 0, 1);
    while (d <= end) {{
      if (d >= start) addMinor(d, 'Q' + (Math.floor(d.getMonth()/3)+1));
      d.setMonth(d.getMonth() + 3);
    }}
  }} else if (z.minorUnit === 'month') {{
    let d = new Date(start.getFullYear(), start.getMonth(), 1);
    while (d <= end) {{
      if (d >= start) addMinor(d, d.toLocaleDateString('en-GB',{{month:'short'}}));
      d.setMonth(d.getMonth() + 1);
    }}
  }} else if (z.minorUnit === 'week') {{
    let d = new Date(start);
    d.setDate(d.getDate() - d.getDay() + 1);  // Monday
    while (d <= end) {{
      if (d >= start) addMinor(d, d.getDate().toString());
      d.setDate(d.getDate() + 7);
    }}
  }} else if (z.minorUnit === 'day') {{
    let d = new Date(start);
    while (d <= end) {{
      if (d >= start) addMinor(d, d.getDate().toString());
      d.setDate(d.getDate() + 1);
    }}
  }}

  return {{major, minor}};
}}

function renderScale(W, dr, tw) {{
  const rows = document.getElementById('scale-rows');
  rows.innerHTML = '';
  const z = ZOOM_LEVELS[zoomLevel];
  const ticks = computeTicks(dr, z);

  // Major row
  ticks.major.forEach(t => {{
    const x = d2x(t.iso, dr, tw);
    if (x > -120 && x < W + 120) {{
      const el = document.createElement('div');
      el.className = 'scale-tick major';
      el.style.left = (x - 6) + 'px';
      el.style.top = '8px';
      el.textContent = t.label;
      rows.appendChild(el);
    }}
  }});

  // Minor row — collision detection: only render if there's space
  let lastRight = -Infinity;
  ticks.minor.forEach(t => {{
    const x = d2x(t.iso, dr, tw);
    if (x > -60 && x < W + 60) {{
      const labelW = t.label.length * 7 + 14;
      if (x - 4 > lastRight + 4) {{
        const el = document.createElement('div');
        el.className = 'scale-tick minor';
        el.style.left = (x + 4) + 'px';
        el.style.top = '34px';
        el.textContent = t.label;
        rows.appendChild(el);
        lastRight = x + labelW;
      }}
    }}
  }});

  // Update info readout
  document.getElementById('zoom-name').textContent = z.name;
  const dr_ = dateRange();
  document.getElementById('scale-info').textContent =
    fmtDate(dr_.min).toLowerCase() + '  →  ' + fmtDate(dr_.max).toLowerCase();
}}

function updateZoomStops() {{
  const stops = document.getElementById('zoom-stops');
  stops.innerHTML = '';
  ZOOM_LEVELS.forEach((z, i) => {{
    const s = document.createElement('div');
    s.className = 'zoom-stop' + (i === zoomLevel ? ' active' : '');
    s.title = z.name;
    s.onclick = () => {{ zoomLevel = i; render(); }};
    stops.appendChild(s);
  }});
}}

// ── Cards ─────────────────────────────────────────────────────────────────────
function toggleCard(ev, branch, nx, ny, dir, col) {{
  if (openCards[ev.id]) {{
    openCards[ev.id].el.remove();
    delete openCards[ev.id];
    render(); return;
  }}
  const card = document.createElement('div');
  card.className = 'ecard';
  card.style.setProperty('--card-color', col);
  card.style.left = (nx - 160) + 'px';
  // place above for up branches, below for down
  card.style.top = (dir < 0 ? ny - 280 : ny + 28) + 'px';
  card.innerHTML = cardViewHTML(ev, branch, col);
  document.getElementById('scene').appendChild(card);
  openCards[ev.id] = {{el: card, branch, nx, ny, dir, col}};
  render();
}}

function escapeHTML(s){{return (s||'').replace(/[&<>"']/g, c=>({{
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
}}[c]));}}

function cardViewHTML(ev, branch, col) {{
  const pri = ev.priority;
  const priHTML = pri ? `<span style="font-family:'JetBrains Mono',monospace;font-size:8px;
    padding:2px 6px;letter-spacing:.15em;
    color:${{pri==='High'?'#c4787d':pri==='Medium'?'#c4a36a':'#88a892'}};
    border:1px solid ${{pri==='High'?'#c4787d44':pri==='Medium'?'#c4a36a44':'#88a89244'}}">
    ${{pri.toUpperCase()}}</span>` : '';

  const linkHtml = ev.sharepoint_url
    ? `<a class="card-link" href="${{escapeHTML(ev.sharepoint_url)}}" target="_blank">
        ↗ ${{escapeHTML(ev.sharepoint_label || 'View document')}}</a>` : '';

  return `<div class="card-h">
    <div style="flex:1;min-width:0">
      <div class="card-eyebrow">${{escapeHTML(ev.form || ev.type || 'event')}}${{priHTML}}</div>
      <div class="card-title">${{escapeHTML(ev.title)}}</div>
      <div class="card-meta">${{fmtDate(parse(ev.date))}}${{ev.time_taken?'  ·  '+escapeHTML(ev.time_taken):''}}</div>
    </div>
    <span class="card-x" onclick="closeCard('${{ev.id}}')">✕</span>
  </div>
  ${{ev.description ? `<div class="card-desc">${{escapeHTML(ev.description)}}</div>` : '<div style="height:6px"></div>'}}
  ${{linkHtml}}
  <div class="card-rule"></div>
  <div class="card-acts">
    <button class="btn primary" onclick="startEdit('${{ev.id}}','${{branch.id}}')">Edit</button>
    <button class="btn danger"  onclick="deleteEvent('${{ev.id}}','${{branch.id}}')">Delete</button>
  </div>`;
}}

function cardEditHTML(ev, col) {{
  return `<div class="card-h">
    <div class="card-title" style="color:${{col}};font-size:14px">Edit event</div>
    <span class="card-x" onclick="cancelEdit('${{ev.id}}')">✕</span>
  </div>
  <div style="height:8px"></div>
  <div class="card-field-l">Date</div>
  <input class="card-field" id="ef-date-${{ev.id}}" value="${{ev.date}}" type="date">
  <div class="card-field-l">Form / type</div>
  <input class="card-field" id="ef-form-${{ev.id}}" value="${{escapeHTML(ev.form||ev.type||'')}}">
  <div class="card-field-l">Priority</div>
  <select class="card-field" id="ef-pri-${{ev.id}}">
    <option value="" ${{!ev.priority?'selected':''}}>—</option>
    <option ${{ev.priority==='High'?'selected':''}}>High</option>
    <option ${{ev.priority==='Medium'?'selected':''}}>Medium</option>
    <option ${{ev.priority==='Low'?'selected':''}}>Low</option>
  </select>
  <div class="card-field-l">Title</div>
  <input class="card-field" id="ef-title-${{ev.id}}" value="${{escapeHTML(ev.title||'')}}">
  <div class="card-field-l">Notes</div>
  <textarea class="card-field" id="ef-desc-${{ev.id}}" rows="3">${{escapeHTML(ev.description||'')}}</textarea>
  <div class="card-field-l">SharePoint link</div>
  <input class="card-field" id="ef-link-${{ev.id}}" value="${{escapeHTML(ev.sharepoint_url||'')}}">
  <div class="card-field-l">Link label</div>
  <input class="card-field" id="ef-linklabel-${{ev.id}}" value="${{escapeHTML(ev.sharepoint_label||'')}}">
  <div class="card-field-l">Time taken</div>
  <input class="card-field" id="ef-time-${{ev.id}}" value="${{escapeHTML(ev.time_taken||'')}}">
  <div class="card-acts">
    <button class="btn primary" onclick="saveEdit('${{ev.id}}')">Save</button>
    <button class="btn" onclick="cancelEdit('${{ev.id}}')">Cancel</button>
  </div>`;
}}

window.closeCard = id => {{
  if (openCards[id]) {{ openCards[id].el.remove(); delete openCards[id]; render(); }}
}};
window.startEdit = (evId, branchId) => {{
  const oc = openCards[evId]; if (!oc) return;
  const ev = oc.branch.events.find(e => e.id === evId);
  oc.el.innerHTML = cardEditHTML(ev, oc.col);
}};
window.cancelEdit = evId => {{
  const oc = openCards[evId]; if (!oc) return;
  const ev = oc.branch.events.find(e => e.id === evId);
  oc.el.innerHTML = cardViewHTML(ev, oc.branch, oc.col);
}};
window.saveEdit = evId => {{
  const oc = openCards[evId]; if (!oc) return;
  const ev = oc.branch.events.find(e => e.id === evId);
  const get = s => document.getElementById('ef-' + s + '-' + evId)?.value;
  ev.date = get('date') || ev.date;
  ev.form = get('form') || ev.form;
  ev.priority = get('pri') || '';
  ev.title = get('title') || ev.title;
  ev.description = get('desc') || '';
  ev.sharepoint_url = get('link') || '';
  ev.sharepoint_label = get('linklabel') || '';
  ev.time_taken = get('time') || '';
  oc.branch.events.sort((a,b) => a.date.localeCompare(b.date));
  persist(); render();
  oc.el.innerHTML = cardViewHTML(ev, oc.branch, oc.col);
}};
window.deleteEvent = (evId, branchId) => {{
  if (!confirm('Delete this event?')) return;
  const branch = DATA.branches.find(b => b.id === branchId);
  if (!branch) return;
  branch.events = branch.events.filter(e => e.id !== evId);
  // if branch has no events, also delete the branch (or keep — let's keep)
  if (openCards[evId]) {{ openCards[evId].el.remove(); delete openCards[evId]; }}
  persist(); render();
}};

// ── Panels ────────────────────────────────────────────────────────────────────
function togglePanel(id) {{
  ['panel-branch','panel-event'].forEach(p => {{
    const el = document.getElementById(p);
    if (p === id) el.classList.toggle('open');
    else el.classList.remove('open');
  }});
}}
window.closePanel = id => document.getElementById(id).classList.remove('open');

window.openNewBranch = () => {{
  document.getElementById('nb-date').value = today();
  ['nb-person','nb-title','nb-desc','nb-link','nb-linklabel','nb-time'].forEach(id => document.getElementById(id).value = '');
  togglePanel('panel-branch');
}};
window.openNewEvent = (branchId) => {{
  if (!DATA.branches.length) {{
    alert('Create a branch first.');
    return;
  }}
  const sel = document.getElementById('ne-branch'); sel.innerHTML = '';
  DATA.branches.forEach(b => {{
    const o = document.createElement('option');
    o.value = b.id; o.textContent = b.person + ' — ' + b.task_title;
    if (branchId && b.id === branchId) o.selected = true;
    sel.appendChild(o);
  }});
  document.getElementById('ne-date').value = today();
  ['ne-title','ne-desc','ne-link','ne-linklabel','ne-time'].forEach(id => document.getElementById(id).value = '');
  togglePanel('panel-event');
}};

window.submitNewBranch = () => {{
  const person = document.getElementById('nb-person').value.trim();
  const title  = document.getElementById('nb-title').value.trim();
  const d      = document.getElementById('nb-date').value;
  if (!person || !title || !d) {{ alert('Person, title and date required.'); return; }}
  DATA.branches.push({{
    id: uid(), person, task_title: title,
    color: COLORS[DATA.branches.length % COLORS.length],
    events: [{{
      id: uid(), date: d,
      form: document.getElementById('nb-form').value,
      priority: document.getElementById('nb-priority').value,
      title,
      description: document.getElementById('nb-desc').value.trim(),
      sharepoint_url: document.getElementById('nb-link').value.trim(),
      sharepoint_label: document.getElementById('nb-linklabel').value.trim() || 'View document',
      time_taken: document.getElementById('nb-time').value.trim()
    }}]
  }});
  closePanel('panel-branch'); persist(); render();
}};

window.submitNewEvent = () => {{
  const branchId = document.getElementById('ne-branch').value;
  const branch = DATA.branches.find(b => b.id === branchId);
  if (!branch) return;
  const d = document.getElementById('ne-date').value;
  const title = document.getElementById('ne-title').value.trim();
  if (!d || !title) {{ alert('Date and title required.'); return; }}
  branch.events.push({{
    id: uid(), date: d,
    form: document.getElementById('ne-form').value,
    priority: document.getElementById('ne-priority').value,
    title,
    description: document.getElementById('ne-desc').value.trim(),
    sharepoint_url: document.getElementById('ne-link').value.trim(),
    sharepoint_label: document.getElementById('ne-linklabel').value.trim() || 'View document',
    time_taken: document.getElementById('ne-time').value.trim()
  }});
  branch.events.sort((a,b) => a.date.localeCompare(b.date));
  closePanel('panel-event'); persist(); render();
}};

// ── Persist & I/O ─────────────────────────────────────────────────────────────
function persist() {{
  try {{ localStorage.setItem('chronograph_v2', JSON.stringify(DATA)); }} catch(e) {{}}
}}

window.exportData = () => {{
  const blob = new Blob([JSON.stringify(DATA, null, 2)], {{type:'application/json'}});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = 'timeline_data.json'; a.click();
}};

window.importData = (input) => {{
  const f = input.files[0]; if (!f) return;
  const r = new FileReader();
  r.onload = () => {{
    try {{
      const p = JSON.parse(r.result);
      if (p.branches) {{
        DATA = p; persist(); render();
        Object.values(openCards).forEach(c => c.el.remove()); openCards = {{}};
      }}
    }} catch (e) {{ alert('Invalid JSON'); }}
  }};
  r.readAsText(f);
  input.value = '';
}};

// ── Color helpers ─────────────────────────────────────────────────────────────
function hexToRgb(h) {{
  const m = h.replace('#','').match(/.{{1,2}}/g);
  return [parseInt(m[0],16), parseInt(m[1],16), parseInt(m[2],16)];
}}
function rgbToHex(r,g,b) {{
  return '#' + [r,g,b].map(v => Math.max(0,Math.min(255,Math.round(v))).toString(16).padStart(2,'0')).join('');
}}
function lighten(h, p) {{
  const [r,g,b] = hexToRgb(h);
  return rgbToHex(r + (255-r)*p/100, g + (255-g)*p/100, b + (255-b)*p/100);
}}
function darken(h, p) {{
  const [r,g,b] = hexToRgb(h);
  return rgbToHex(r * (1-p/100), g * (1-p/100), b * (1-p/100));
}}

// ── Pan & zoom ────────────────────────────────────────────────────────────────
svg.addEventListener('mousedown', e => {{
  if (e.button !== 0) return;
  Object.values(openCards).forEach(c => c.el.remove());
  openCards = {{}};
  isDragging = true;
  dragStart = {{x: e.clientX}};
  panStart = panX;
  svg.classList.add('dragging');
}});
window.addEventListener('mousemove', e => {{
  if (!isDragging) return;
  panX = panStart + (e.clientX - dragStart.x);
  clampPan(); render();
}});
window.addEventListener('mouseup', () => {{ isDragging = false; svg.classList.remove('dragging'); }});

svg.addEventListener('wheel', e => {{
  e.preventDefault();
  if (e.ctrlKey || e.metaKey) {{
    // pinch-zoom
    if (e.deltaY < 0 && zoomLevel < ZOOM_LEVELS.length - 1) zoomLevel++;
    else if (e.deltaY > 0 && zoomLevel > 0) zoomLevel--;
    render();
  }} else {{
    panX -= (e.deltaX || e.deltaY) * 0.8;
    clampPan(); render();
  }}
}}, {{passive: false}});

function clampPan() {{
  const dr = dateRange(), tw = totalW(dr);
  panX = Math.min(MARGIN, Math.max(-(tw - window.innerWidth + MARGIN), panX));
}}

window.addEventListener('resize', render);

function uid() {{ return Math.random().toString(36).slice(2,10); }}

// ── Init ──────────────────────────────────────────────────────────────────────
render();
</script>
</body>
</html>"""

st.components.v1.html(HTML, height=900, scrolling=False)

st.markdown("""
<style>
html,body,[data-testid="stAppViewContainer"]{background:#06060c !important}
[data-testid="stAppViewContainer"]>.main{background:#06060c !important;padding:0 !important}
.block-container{padding:0 !important;max-width:100% !important}
iframe{border:none !important;display:block;height:100vh !important}
header[data-testid="stHeader"]{display:none !important}
[data-testid="stDecoration"]{display:none !important}
footer{display:none !important}
</style>
""", unsafe_allow_html=True)
