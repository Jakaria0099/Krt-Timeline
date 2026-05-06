import streamlit as st
import json

from data_layer import load_data, save_data, has_gsheet_config, force_refresh

st.set_page_config(
    page_title="Chronograph",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Initial data load ─────────────────────────────────────────────────────────
# On every Streamlit rerun, fetch fresh data from sheet (cached for 60s).
# Read errors fall back to local file silently.
data, data_source, load_error = load_data()
st.session_state.data = data

# ── Handle pending sync (triggered by Push button via session_state flag) ────
# When user clicks Push, we can't read localStorage synchronously in the same
# rerun (streamlit-js-eval is async). The pattern is:
#   1st click: set sync_pending = True, rerun
#   2nd rerun: run streamlit_js_eval, get localStorage data, write to sheet,
#              clear flag, rerun
if "sync_pending" not in st.session_state:
    st.session_state.sync_pending = False
if "sync_status" not in st.session_state:
    st.session_state.sync_status = None  # tuple (kind, message)
if "sync_attempt" not in st.session_state:
    st.session_state.sync_attempt = 0
if "force_localstorage_overwrite" not in st.session_state:
    # When True, the canvas will ignore localStorage and use server data,
    # then overwrite localStorage to match. Set after Pull or successful Push.
    st.session_state.force_localstorage_overwrite = False

# Run the sync flow if pending
if st.session_state.sync_pending and has_gsheet_config():
    from streamlit_js_eval import streamlit_js_eval
    # Unique key per attempt so streamlit_js_eval re-evaluates
    js_key = f"read_local_{st.session_state.sync_attempt}"
    raw = streamlit_js_eval(
        js_expressions="localStorage.getItem('chronograph_v2')",
        key=js_key,
        want_output=True,
    )
    if raw is not None:
        # We got the value (possibly empty string or "null")
        try:
            if raw and raw not in ("null", ""):
                local_data = json.loads(raw)
                if isinstance(local_data, dict) and "branches" in local_data:
                    dest, err = save_data(local_data)
                    if err:
                        st.session_state.sync_status = ("error", err)
                    else:
                        st.session_state.sync_status = ("ok", f"Pushed {len(local_data['branches'])} branches to Google Sheet.")
                        # After a successful push, sheet now matches localStorage,
                        # but we set the flag so canvas re-syncs cleanly on rerun.
                        st.session_state.force_localstorage_overwrite = True
                else:
                    st.session_state.sync_status = ("error", "Local data invalid — could not push.")
            else:
                st.session_state.sync_status = ("error", "No local changes found to push.")
        except Exception as e:
            st.session_state.sync_status = ("error", f"Push failed: {e}")
        st.session_state.sync_pending = False
        st.rerun()
    # If raw is None, streamlit_js_eval is still resolving — page will rerun

# Read the force flag once and reset it (one-shot)
force_overwrite_now = st.session_state.force_localstorage_overwrite
if force_overwrite_now:
    st.session_state.force_localstorage_overwrite = False
force_overwrite_str = "true" if force_overwrite_now else "false"

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
  --fg:#f0eee2;
  --fg-mute:#a8a59a;
  --fg-faint:#6a6770;
  --fg-ghost:#3a3a44;
  --accent:#d4b27a;
  --accent-soft:#d4b27a55;
  --rule:#22223a;
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
  position:fixed;top:0;left:0;right:0;height:62px;
  display:flex;align-items:center;padding:0 28px;gap:18px;
  background:linear-gradient(180deg,#06060c 0%,#06060ce0 70%,transparent 100%);
  z-index:300;
}}
#brand{{
  font-family:var(--serif);font-style:italic;font-weight:400;
  font-size:22px;color:var(--fg);letter-spacing:.005em;
}}
#brand .glyph{{
  font-style:normal;color:var(--accent);margin-right:10px;
  font-family:var(--mono);font-size:17px;
}}
#brand .sub{{
  font-family:var(--mono);font-size:10.5px;font-style:normal;
  color:var(--fg-mute);letter-spacing:.18em;text-transform:uppercase;
  margin-left:16px;padding-left:16px;border-left:1px solid var(--rule);
}}
.tb-spacer{{flex:1}}
.tb-btn{{
  font-family:var(--mono);font-size:11.5px;letter-spacing:.1em;
  text-transform:uppercase;padding:9px 16px;border-radius:0;
  cursor:pointer;border:1px solid var(--rule);
  background:transparent;color:var(--fg-mute);
  transition:border-color .2s,color .2s,background .2s;
}}
.tb-btn:hover{{border-color:var(--accent);color:var(--fg);background:#12122a88}}
.tb-btn.primary{{
  border-color:var(--accent-soft);color:var(--accent);
}}
.tb-btn.primary:hover{{
  background:var(--accent);color:#06060c;border-color:var(--accent);
}}

/* ── 3D scene wrapper ── */
#scene{{
  position:fixed;top:62px;left:0;right:0;bottom:96px;
  perspective:2000px;perspective-origin:50% 50%;
  z-index:1;overflow:hidden;
}}
#stage{{
  position:absolute;inset:0;
  transform-style:preserve-3d;
  transform:none;
  transform-origin:50% 50%;
}}
#canvas{{
  position:absolute;inset:0;
  cursor:grab;
}}
#canvas.dragging{{cursor:grabbing}}

/* ── Event cards (3D float) ── */
.ecard{{
  position:absolute;background:#101020;
  border:1px solid #2a2a44;border-radius:3px;
  padding:22px 24px 20px;width:360px;
  font-family:var(--sans);font-size:13px;line-height:1.65;
  pointer-events:all;z-index:200;
  box-shadow:
    0 28px 70px -10px rgba(0,0,0,.8),
    0 6px 14px rgba(0,0,0,.5),
    inset 0 1px 0 rgba(255,255,255,.06);
  animation:cardIn .25s cubic-bezier(.34,1.56,.64,1);
  transform-origin:50% 0;
}}
.ecard::before{{
  content:'';position:absolute;left:0;top:0;width:3px;height:100%;
  background:var(--card-color,var(--accent));
  opacity:.95;
}}
@keyframes cardIn{{
  from{{opacity:0;transform:translateY(8px) scale(.96)}}
  to  {{opacity:1;transform:translateY(0)   scale(1)}}
}}
.card-h{{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}}
.card-eyebrow{{
  font-family:var(--mono);font-size:10.5px;letter-spacing:.18em;
  text-transform:uppercase;color:var(--card-color,var(--accent));
  opacity:.85;margin-bottom:8px;
  display:flex;align-items:center;gap:8px;flex-wrap:wrap;
}}
.card-title{{
  font-family:var(--serif);font-weight:500;font-size:19px;
  color:var(--fg);line-height:1.25;letter-spacing:-.005em;
}}
.card-meta{{
  font-family:var(--mono);font-size:11px;color:var(--fg-mute);
  letter-spacing:.05em;margin-top:7px;
}}
.card-desc{{
  font-size:13px;color:#c0bdb0;line-height:1.7;
  margin:16px 0 14px;font-weight:300;
}}
.card-link{{
  display:inline-flex;align-items:center;gap:8px;
  font-family:var(--mono);font-size:11px;
  color:var(--card-color,var(--accent));text-decoration:none;
  border:1px solid currentColor;padding:8px 12px;
  margin-top:6px;letter-spacing:.04em;
  transition:background .2s,color .2s;cursor:pointer;
  word-break:break-all;
}}
.card-link:hover{{background:var(--card-color,var(--accent));color:#06060c;}}
.card-x{{
  font-family:var(--mono);font-size:16px;cursor:pointer;
  color:var(--fg-faint);line-height:1;padding:3px 6px;
  transition:color .15s;
}}
.card-x:hover{{color:var(--fg)}}
.card-rule{{height:1px;background:var(--rule);margin:16px 0 14px}}

.card-field{{
  width:100%;background:#08081a;border:1px solid var(--rule);
  border-radius:0;color:var(--fg);font-family:var(--mono);
  font-size:12px;padding:9px 11px;margin-bottom:10px;
  resize:vertical;transition:border-color .2s;
}}
.card-field:focus{{outline:none;border-color:var(--card-color,var(--accent))}}
.card-field-l{{
  font-family:var(--mono);font-size:10px;letter-spacing:.15em;
  color:var(--fg-mute);margin-bottom:5px;text-transform:uppercase;
}}
.card-acts{{display:flex;gap:10px;margin-top:16px}}
.btn{{
  flex:1;font-family:var(--mono);font-size:11px;letter-spacing:.1em;
  padding:10px;cursor:pointer;text-transform:uppercase;
  border:1px solid var(--fg-ghost);background:transparent;color:var(--fg-mute);
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
  position:fixed;right:0;top:62px;bottom:96px;width:380px;
  background:linear-gradient(180deg,#0a0a1a 0%,#08081a 100%);
  border-left:1px solid var(--rule);
  padding:30px 26px;overflow-y:auto;z-index:280;
  transform:translateX(100%);
  transition:transform .35s cubic-bezier(.4,0,.2,1);
  box-shadow:-24px 0 60px rgba(0,0,0,.5);
}}
.panel.open{{transform:translateX(0)}}
.panel h2{{
  font-family:var(--serif);font-style:italic;font-weight:400;
  font-size:28px;color:var(--fg);margin-bottom:6px;letter-spacing:-.01em;
}}
.panel h2 + .sub{{
  font-family:var(--mono);font-size:10px;color:var(--fg-mute);
  letter-spacing:.18em;text-transform:uppercase;margin-bottom:26px;
}}
.panel-l{{
  font-family:var(--mono);font-size:10px;letter-spacing:.15em;
  color:var(--fg-mute);margin-bottom:6px;text-transform:uppercase;
}}
.panel-f{{
  width:100%;background:#06060c;border:1px solid var(--fg-ghost);
  color:var(--fg);font-family:var(--mono);font-size:13px;
  padding:11px 13px;margin-bottom:18px;border-radius:0;
  resize:vertical;transition:border-color .2s;
}}
.panel-f:focus{{outline:none;border-color:var(--accent)}}
select.panel-f{{cursor:pointer}}
.panel-btn{{
  width:100%;font-family:var(--mono);font-size:12px;letter-spacing:.1em;
  padding:14px;cursor:pointer;margin-top:6px;text-transform:uppercase;
  border-radius:0;transition:all .2s;
}}
.panel-btn.primary{{
  background:var(--accent);border:1px solid var(--accent);color:#06060c;font-weight:500;
}}
.panel-btn.primary:hover{{background:#e6c388;border-color:#e6c388}}
.panel-btn.cancel{{
  background:transparent;border:1px solid var(--fg-ghost);color:var(--fg-mute);
  margin-top:12px;
}}
.panel-btn.cancel:hover{{border-color:var(--fg-mute);color:var(--fg)}}

/* ── Bottom universal scale ── */
#scale{{
  position:fixed;left:0;right:0;bottom:0;height:96px;
  background:linear-gradient(0deg,#06060c 0%,#06060cee 70%,#06060cb0 100%);
  border-top:1px solid var(--rule);
  z-index:200;
  display:flex;flex-direction:column;
}}
#scale-rows{{
  flex:1;position:relative;
}}
#scale-controls{{
  height:32px;display:flex;align-items:center;
  padding:0 22px;gap:18px;
  border-top:1px solid var(--rule);background:#04040a;
}}
.zoom-label{{
  font-family:var(--mono);font-size:10px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--fg-mute);
}}
.zoom-track{{
  flex:1;height:1px;background:var(--fg-ghost);position:relative;
  max-width:300px;cursor:pointer;
}}
.zoom-stops{{
  display:flex;justify-content:space-between;
  position:absolute;top:-4px;left:0;right:0;height:9px;
}}
.zoom-stop{{
  width:9px;height:9px;border:1px solid var(--fg-ghost);
  background:var(--bg-deep);cursor:pointer;
  transition:all .2s;
}}
.zoom-stop.active{{
  background:var(--accent);border-color:var(--accent);
  transform:scale(1.3);
}}
.zoom-stop:hover{{border-color:var(--fg-mute)}}
.zoom-level-name{{
  font-family:var(--mono);font-size:10.5px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--accent);min-width:70px;
}}
#scale-info{{
  font-family:var(--mono);font-size:10px;letter-spacing:.08em;
  color:var(--fg-mute);margin-left:auto;
}}
.scale-row{{
  position:absolute;left:0;right:0;display:flex;
  pointer-events:none;
}}
.scale-tier-major{{top:6px;height:24px}}
.scale-tier-minor{{top:34px;height:22px}}
.scale-tick{{
  position:absolute;display:flex;align-items:center;
  white-space:nowrap;
}}
.scale-tick.major{{
  font-family:var(--serif);font-style:italic;font-size:17px;
  color:var(--fg);font-weight:400;
}}
.scale-tick.minor{{
  font-family:var(--mono);font-size:10.5px;letter-spacing:.08em;
  color:var(--fg-mute);text-transform:uppercase;
}}
.scale-tick-line{{
  position:absolute;width:1px;background:var(--rule);
  top:-100vh;height:100vh;
}}
.scale-tick-line.heavy{{background:#262640}}

#tt{{
  position:fixed;background:#101020;border:1px solid var(--rule);
  border-left:3px solid var(--accent);
  padding:9px 14px;font-family:var(--mono);font-size:11.5px;
  color:var(--fg);pointer-events:none;opacity:0;
  transition:opacity .12s;white-space:nowrap;z-index:500;
  box-shadow:0 10px 24px rgba(0,0,0,.6);letter-spacing:.04em;
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
const FORCE_OVERWRITE = {force_overwrite_str};

// localStorage policy:
//   - Default: localStorage wins so user's unsaved canvas edits survive Streamlit
//     reruns (clicking sync buttons, etc).
//   - When Python signals FORCE_OVERWRITE (after Pull, or after a successful Push):
//     server data wins, and we overwrite localStorage to match.
if (!FORCE_OVERWRITE) {{
  try {{
    const saved = localStorage.getItem('chronograph_v2');
    if (saved) {{ const p = JSON.parse(saved); if (p.branches) DATA = p; }}
  }} catch(e) {{}}
}}
// Always sync localStorage to current DATA so Push reads a fresh state
try {{ localStorage.setItem('chronograph_v2', JSON.stringify(DATA)); }} catch(e) {{}}

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
const NODE_R = 10;
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
  // For each branch compute the X span its SHELF will occupy (events + label)
  const enriched = branches.map((b, idx) => {{
    const evs = [...b.events].sort((a,c) => a.date.localeCompare(c.date));
    if (!evs.length) return null;
    const x0 = d2x(evs[0].date, dr, tw);
    const x1 = d2x(evs[evs.length-1].date, dr, tw);
    // Branch label width: longer of person + task_title
    const personW = b.person.length * 9;
    const taskW   = (b.task_title || '').length * 6.5;
    const labelW  = Math.max(180, personW, taskW) + 30;
    // Shelf must extend at least far enough to fit the label past the first event
    const shelfRight = Math.max(x1, x0 + labelW) + 50;
    return {{idx, branch: b, evs, x0, x1, xRange:[x0-40, shelfRight + 60]}};
  }}).filter(Boolean);

  // sort by x0 ascending — chronological packing
  enriched.sort((a,c) => a.x0 - c.x0);

  // Alternate up / down, packing into lanes per side with collision check
  const upLanes = []; const downLanes = [];
  enriched.forEach((e, i) => {{
    const side = (i % 2 === 0) ? 'up' : 'down';
    const lanes = side === 'up' ? upLanes : downLanes;
    let placed = false;
    for (let l = 0; l < lanes.length; l++) {{
      if (e.xRange[0] > lanes[l]) {{
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

  // Defs: glow filter, axis gradient
  const defs = se('defs', {{}}, svg);
  // axis glow
  const grad = se('linearGradient', {{id:'axisGlow', x1:'0%', y1:'0%', x2:'100%', y2:'0%'}}, defs);
  se('stop', {{offset:'0%', 'stop-color':'#d4b27a', 'stop-opacity':'0'}}, grad);
  se('stop', {{offset:'15%', 'stop-color':'#d4b27a', 'stop-opacity':'.5'}}, grad);
  se('stop', {{offset:'50%', 'stop-color':'#d4b27a', 'stop-opacity':'.8'}}, grad);
  se('stop', {{offset:'85%', 'stop-color':'#d4b27a', 'stop-opacity':'.5'}}, grad);
  se('stop', {{offset:'100%', 'stop-color':'#d4b27a', 'stop-opacity':'0'}}, grad);

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
  // Soft glow band — broader and stronger
  se('rect', {{
    x: panX, y: ay-5, width: tw, height: 10,
    fill: 'url(#axisGlow)', opacity: '.28'
  }}, svg);
  // Crisp main axis line — thicker & brighter
  se('line', {{
    x1: panX, y1: ay, x2: panX+tw, y2: ay,
    stroke: '#d4b27a', 'stroke-width': '2', opacity: '.85'
  }}, svg);

  // Today marker — bigger and bolder
  const todayX = d2x(today(), dr, tw);
  if (todayX > 0 && todayX < W) {{
    se('line', {{
      x1: todayX, y1: ay-28, x2: todayX, y2: ay+28,
      stroke: '#d4b27a', 'stroke-width': '2', opacity: '1'
    }}, svg);
    se('circle', {{cx: todayX, cy: ay, r: '6', fill:'#d4b27a', opacity:'1'}}, svg);
    se('circle', {{cx: todayX, cy: ay, r: '10', fill:'none', stroke:'#d4b27a', 'stroke-width':'1', opacity:'.4'}}, svg);
    const tlbl = se('text', {{
      x: todayX, y: ay+46,
      'font-family': "'JetBrains Mono',monospace",
      'font-size': '11', 'text-anchor':'middle', fill:'#d4b27a',
      'letter-spacing': '.18em', 'font-weight':'500'
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
  const BASE_OFFSET = 110;   // distance from axis to first lane
  const LANE_HEIGHT = 110;   // vertical space per lane
  const laneY = ay + dir * (BASE_OFFSET + lane * LANE_HEIGHT);
  const colorIdx = idx % COLORS.length;
  const col = branch.color || COLORS[colorIdx];

  const x0 = d2x(evs[0].date, dr, tw);
  const xLast = d2x(evs[evs.length-1].date, dr, tw);

  // Calculate shelf extent — must fit branch label past the events
  const personW = branch.person.length * 9;
  const taskW   = (branch.task_title || '').length * 6.5;
  const labelW  = Math.max(180, personW, taskW) + 20;
  const shelfRight = Math.max(xLast, x0 + labelW) + 30;

  // ── 1. Anchor on main axis ──
  // Outer ring
  se('circle', {{cx: x0, cy: ay, r: '9', fill: 'none', stroke: col, 'stroke-width': '1.5', opacity: '.5'}}, svg);
  // Inner solid dot
  se('circle', {{cx: x0, cy: ay, r: '4.5', fill: col, opacity: '1'}}, svg);

  // ── 2. Vertical connector from axis up/down to shelf ──
  const stemId = 'stem-' + idx;
  const stemGrad = se('linearGradient', {{
    id: stemId, x1: '0%', y1: dir<0 ? '100%' : '0%',
    x2: '0%', y2: dir<0 ? '0%' : '100%'
  }}, svg.querySelector('defs'));
  se('stop', {{offset: '0%', 'stop-color': col, 'stop-opacity': '.4'}}, stemGrad);
  se('stop', {{offset: '100%', 'stop-color': col, 'stop-opacity': '1'}}, stemGrad);
  se('line', {{
    x1: x0, y1: ay, x2: x0, y2: laneY,
    stroke: 'url(#' + stemId + ')', 'stroke-width': '2.5'
  }}, svg);

  // ── 3. Horizontal shelf line — runs from x0 to shelfRight ──
  se('line', {{
    x1: x0, y1: laneY, x2: shelfRight, y2: laneY,
    stroke: col, 'stroke-width': '2', opacity: '.85'
  }}, svg);
  // shelf end-cap tick
  se('line', {{
    x1: shelfRight, y1: laneY-7, x2: shelfRight, y2: laneY+7,
    stroke: col, 'stroke-width': '1.5', opacity: '.7'
  }}, svg);

  // ── 4. Branch labels OUTSIDE the shelf (away from axis) ──
  // For up-branches (dir=-1): labels above shelf; for down: below shelf
  const personY = laneY + dir * (-38);   // furthest from shelf
  const taskY   = laneY + dir * (-18);   // closer to shelf

  // Person name — italic serif, large
  const personEl = se('text', {{
    x: x0 + 14, y: personY,
    'font-family': "'Fraunces',serif", 'font-style': 'italic',
    'font-weight': '500', 'font-size': '20',
    'text-anchor': 'start', fill: col, 'letter-spacing': '-.005em',
  }}, svg);
  personEl.textContent = branch.person;
  // Task title — mono uppercase tracked
  const taskEl = se('text', {{
    x: x0 + 14, y: taskY,
    'font-family': "'JetBrains Mono',monospace",
    'font-size': '11', 'text-anchor': 'start',
    fill: col, opacity: '.75', 'letter-spacing': '.12em', 'font-weight':'500',
  }}, svg);
  taskEl.textContent = (branch.task_title || '').toUpperCase();

  // ── 5. Add-event "+" button at end of shelf ──
  const addBtnG = se('g', {{style: 'cursor:pointer'}}, svg);
  se('circle', {{
    cx: shelfRight + 18, cy: laneY, r: '11',
    fill: 'none', stroke: col, 'stroke-width': '1.5', opacity: '.5'
  }}, addBtnG);
  const plusEl = se('text', {{
    x: shelfRight + 18, y: laneY + 5,
    'font-family': "'JetBrains Mono',monospace",
    'font-size': '15', 'text-anchor': 'middle',
    fill: col, opacity: '.75', 'font-weight':'500'
  }}, addBtnG);
  plusEl.textContent = '+';
  addBtnG.addEventListener('mouseenter', () => {{
    addBtnG.querySelector('circle').setAttribute('opacity', '1');
    plusEl.setAttribute('opacity', '1');
  }});
  addBtnG.addEventListener('mouseleave', () => {{
    addBtnG.querySelector('circle').setAttribute('opacity', '.5');
    plusEl.setAttribute('opacity', '.75');
  }});
  addBtnG.addEventListener('click', e => {{
    e.stopPropagation();
    openNewEvent(branch.id);
  }});

  // ── 6. Event nodes on the shelf (spheres) ──
  evs.forEach((ev, ei) => {{
    const ex = d2x(ev.date, dr, tw);

    // Faint axis tick at this event's date (shows when on the timeline it occurred)
    if (ei > 0) {{
      se('line', {{
        x1: ex, y1: ay-4, x2: ex, y2: ay+4,
        stroke: col, 'stroke-width': '1.5', opacity: '.7'
      }}, svg);
    }}

    const isOpen = !!openCards[ev.id];
    const g = se('g', {{style: 'cursor:pointer'}}, svg);

    // Glow halo when card is open
    if (isOpen) {{
      se('circle', {{cx: ex, cy: laneY, r: NODE_R + 9, fill: col, opacity: '.12'}}, g);
      se('circle', {{cx: ex, cy: laneY, r: NODE_R + 5, fill: 'none', stroke: col, 'stroke-width': '1', opacity: '.45'}}, g);
    }}

    // Sphere body — radial gradient
    se('circle', {{
      cx: ex, cy: laneY, r: NODE_R,
      fill: 'url(#nodeR' + colorIdx + ')',
      stroke: lighten(col, 30), 'stroke-width': '1.5', opacity: '1'
    }}, g);
    // Highlight dot for 3D feel
    se('circle', {{cx: ex - 3, cy: laneY - 3, r: '2.5', fill: '#fff', opacity: '.5'}}, g);

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
      toggleCard(ev, branch, ex, laneY, dir, col);
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
    if (openCards[ev.id].connector) openCards[ev.id].connector.remove();
    openCards[ev.id].el.remove();
    delete openCards[ev.id];
    render(); return;
  }}

  const card = document.createElement('div');
  card.className = 'ecard';
  card.style.setProperty('--card-color', col);
  card.style.visibility = 'hidden';
  card.innerHTML = cardViewHTML(ev, branch, col);
  document.getElementById('scene').appendChild(card);

  // Now we know the card's actual rendered size — position it smartly
  const pos = computeCardPosition(nx, ny, dir, card.offsetWidth, card.offsetHeight);
  card.style.left = pos.left + 'px';
  card.style.top  = pos.top + 'px';
  card.style.visibility = 'visible';

  // If card was offset (clamped), draw a thin SVG connector back to the node
  let connector = null;
  if (pos.offset) connector = drawCardConnector(nx, ny, pos, col);

  openCards[ev.id] = {{el: card, branch, nx, ny, dir, col, pos, connector}};
  render();
}}

function computeCardPosition(nx, ny, dir, cardW, cardH) {{
  const margin = 18;
  const sceneEl = document.getElementById('scene');
  const W = sceneEl.clientWidth;
  const H = sceneEl.clientHeight;
  const GAP = 24;

  // Default ideal position: centered horizontally on node
  let idealLeft = nx - cardW / 2;
  let idealTop  = dir < 0 ? ny - cardH - GAP : ny + GAP;
  let offset = false;

  // Horizontal clamp
  let left = idealLeft;
  if (left < margin) {{
    left = margin;
    offset = true;
  }}
  if (left + cardW > W - margin) {{
    left = W - cardW - margin;
    offset = true;
  }}

  // Vertical: try preferred side first; if doesn't fit, flip
  let top = idealTop;
  if (dir < 0) {{
    // Preferred: above
    if (top < margin) {{
      const flipTop = ny + GAP;
      if (flipTop + cardH < H - margin) {{
        top = flipTop;  // place below instead
      }} else {{
        top = margin;   // doesn't fit either way, top-clamp
      }}
    }}
  }} else {{
    // Preferred: below
    if (top + cardH > H - margin) {{
      const flipTop = ny - cardH - GAP;
      if (flipTop > margin) {{
        top = flipTop;
      }} else {{
        top = H - cardH - margin;
      }}
    }}
  }}

  return {{left, top, offset}};
}}

function drawCardConnector(nx, ny, pos, col) {{
  // Create a thin curved SVG line from the node to the nearest edge of the card
  const sceneEl = document.getElementById('scene');
  const ns = 'http://www.w3.org/2000/svg';
  const svgEl = document.createElementNS(ns, 'svg');
  svgEl.style.position = 'absolute';
  svgEl.style.top = '0';
  svgEl.style.left = '0';
  svgEl.style.width = '100%';
  svgEl.style.height = '100%';
  svgEl.style.pointerEvents = 'none';
  svgEl.style.zIndex = '99';

  // Find nearest point on card edge
  const cardLeft = pos.left, cardTop = pos.top;
  const cardW = 360, cardH = 200;  // approximate; line will look fine
  let tx, ty;
  // Closest x
  if (nx < cardLeft) tx = cardLeft;
  else if (nx > cardLeft + cardW) tx = cardLeft + cardW;
  else tx = nx;
  // Closest y
  if (ny < cardTop) ty = cardTop;
  else if (ny > cardTop + cardH) ty = cardTop + cardH;
  else ty = ny;

  // Draw a curved path
  const dx = tx - nx, dy = ty - ny;
  const cx1 = nx + dx * 0.5, cy1 = ny;
  const cx2 = tx, cy2 = ty - dy * 0.5;
  const path = document.createElementNS(ns, 'path');
  path.setAttribute('d', `M ${{nx}} ${{ny}} C ${{cx1}} ${{cy1}}, ${{cx2}} ${{cy2}}, ${{tx}} ${{ty}}`);
  path.setAttribute('stroke', col);
  path.setAttribute('stroke-width', '1.5');
  path.setAttribute('fill', 'none');
  path.setAttribute('opacity', '.5');
  path.setAttribute('stroke-dasharray', '3 4');
  svgEl.appendChild(path);

  // Small dot at card-edge end
  const dot = document.createElementNS(ns, 'circle');
  dot.setAttribute('cx', tx); dot.setAttribute('cy', ty);
  dot.setAttribute('r', '3'); dot.setAttribute('fill', col);
  dot.setAttribute('opacity', '.7');
  svgEl.appendChild(dot);

  sceneEl.appendChild(svgEl);
  return svgEl;
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
  if (openCards[id]) {{
    if (openCards[id].connector) openCards[id].connector.remove();
    openCards[id].el.remove();
    delete openCards[id];
    render();
  }}
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
        Object.values(openCards).forEach(c => {{
          if (c.connector) c.connector.remove();
          c.el.remove();
        }});
        openCards = {{}};
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
  Object.values(openCards).forEach(c => {{
    if (c.connector) c.connector.remove();
    c.el.remove();
  }});
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

st.markdown("""
<style>
html,body,[data-testid="stAppViewContainer"]{background:#06060c !important}
[data-testid="stAppViewContainer"]>.main{background:#06060c !important;padding:0 !important}
.block-container{padding:0 !important;max-width:100% !important}
iframe{border:none !important;display:block}
header[data-testid="stHeader"]{display:none !important}
[data-testid="stDecoration"]{display:none !important}
footer{display:none !important}

/* Make the main canvas iframe fill the viewport below the sync strip */
[data-testid="stIFrame"] iframe {
  height: calc(100vh - 60px) !important;
  width: 100% !important;
}

/* Hide streamlit-js-eval's invisible component (it leaves a tiny space otherwise) */
.element-container:has(iframe[height="0"]),
.element-container:has(iframe[srcdoc*="streamlit_js_eval"]) {
  display: none !important;
  height: 0 !important;
}

/* Streamlit-side sync strip styling */
.sync-strip {
  background: #04040a;
  border-bottom: 1px solid #22223a;
  padding: 8px 24px;
  display: flex;
  align-items: center;
  gap: 18px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #a8a59a;
  letter-spacing: .04em;
}
.sync-strip .label { color: #6a6770; text-transform: uppercase; letter-spacing: .15em; font-size: 9.5px; }
.sync-strip .badge {
  padding: 4px 10px;
  border: 1px solid #22223a;
  border-radius: 0;
  font-size: 10.5px;
  letter-spacing: .08em;
}
.sync-strip .badge.cloud { color: #88a892; border-color: #88a89255; }
.sync-strip .badge.local { color: #c4a36a; border-color: #c4a36a55; }
.sync-strip .badge.error { color: #c4787d; border-color: #c4787d55; }
.sync-strip .ok { color: #88a892; }
.sync-strip .err { color: #c4787d; }
.sync-strip .spinner { color: #d4b27a; }

/* Streamlit button overrides for sync strip */
[data-testid="stButton"] > button {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10.5px !important;
  letter-spacing: .08em !important;
  text-transform: uppercase !important;
  background: transparent !important;
  border: 1px solid #22223a !important;
  color: #a8a59a !important;
  border-radius: 0 !important;
  padding: 6px 12px !important;
  height: auto !important;
  min-height: 0 !important;
  transition: border-color .2s, color .2s, background .2s !important;
  width: 100% !important;
}
[data-testid="stButton"] > button:hover:not(:disabled) {
  border-color: #d4b27a !important;
  color: #f0eee2 !important;
  background: #12122a !important;
}
[data-testid="stButton"] > button:disabled {
  opacity: 0.4 !important;
  cursor: not-allowed !important;
}
[data-testid="stHorizontalBlock"] {
  padding: 8px 22px !important;
  background: #04040a !important;
  border-bottom: 1px solid #22223a !important;
  gap: 14px !important;
  align-items: center !important;
  height: 60px !important;
}
[data-testid="stMarkdownContainer"] p { margin: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Streamlit-side sync strip ─────────────────────────────────────────────────
sync_cols = st.columns([3, 1.2, 1.2, 0.6, 5])

with sync_cols[0]:
    if has_gsheet_config():
        if data_source == "sheet":
            badge_html = '<span class="badge cloud">● GOOGLE SHEET</span>'
        else:
            badge_html = '<span class="badge error">⚠ SHEET ERROR — using local</span>'
    else:
        badge_html = '<span class="badge local">○ LOCAL ONLY (no cloud setup)</span>'

    n_branches = len(st.session_state.data.get("branches", []))
    n_events = sum(len(b.get("events", [])) for b in st.session_state.data.get("branches", []))
    info = f"{n_branches} branches · {n_events} events"

    if st.session_state.sync_status:
        kind, msg = st.session_state.sync_status
        cls = "ok" if kind == "ok" else "err"
        status_html = f'<span class="{cls}">{msg}</span>'
    elif load_error:
        status_html = f'<span class="err">{load_error}</span>'
    elif st.session_state.sync_pending:
        status_html = '<span class="spinner">syncing…</span>'
    else:
        status_html = f'<span class="label">{info}</span>'

    st.markdown(
        f'<div class="sync-strip" style="border:none;padding:0;background:transparent;">'
        f'<span class="label">storage</span>{badge_html}{status_html}</div>',
        unsafe_allow_html=True
    )

with sync_cols[1]:
    pull_disabled = not has_gsheet_config()
    if st.button("↻ Pull from Sheet", disabled=pull_disabled,
                 help="Refresh data from the Google Sheet (overwrites any unsaved canvas edits)"):
        force_refresh()
        st.session_state.force_localstorage_overwrite = True
        st.session_state.sync_status = ("ok", "Pulled latest from Google Sheet.")
        st.rerun()

with sync_cols[2]:
    push_disabled = not has_gsheet_config() or st.session_state.sync_pending
    if st.button("☁ Push to Sheet", disabled=push_disabled,
                 help="Save your current canvas state (in browser) to the Google Sheet"):
        st.session_state.sync_status = None
        st.session_state.sync_pending = True
        st.session_state.sync_attempt += 1
        st.rerun()

with sync_cols[3]:
    # Only show dismiss button when there's a status to dismiss
    if st.session_state.sync_status is not None:
        if st.button("✕", key="dismiss_status", help="Dismiss sync message"):
            st.session_state.sync_status = None
            st.rerun()

with sync_cols[4]:
    pass  # spacer

st.components.v1.html(HTML, height=820, scrolling=False)
