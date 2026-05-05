import streamlit as st
import json
import os
from datetime import datetime, date
import uuid

st.set_page_config(
    page_title="Task Timeline",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "timeline_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"branches": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def init_session():
    if "data" not in st.session_state:
        st.session_state.data = load_data()
    if "show_add_branch" not in st.session_state:
        st.session_state.show_add_branch = False
    if "show_add_event" not in st.session_state:
        st.session_state.show_add_event = None

data = st.session_state.data if "data" in st.session_state else load_data()
init_session()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700&display=swap');
    section[data-testid="stSidebar"] { background: #0a0a0f; border-right: 1px solid #1e1e2e; }
    section[data-testid="stSidebar"] * { color: #c4c4d4 !important; font-family: 'DM Mono', monospace !important; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #f0f0ff !important; }
    div[data-testid="stForm"] { background: #12121a; border: 1px solid #2a2a3e; border-radius: 8px; padding: 12px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("### ◈ Task Timeline")
    st.markdown("*For Prof. Al-Hassan*")
    st.divider()

    # Branch list
    st.markdown("**Branches**")
    branches = st.session_state.data.get("branches", [])
    if branches:
        for b in branches:
            col1, col2 = st.columns([5, 1])
            with col1:
                ev_count = len(b.get("events", []))
                st.markdown(f"**{b['person']}** · {ev_count} event{'s' if ev_count != 1 else ''}")
                st.caption(b.get("task_title", "")[:40])
            with col2:
                if st.button("＋", key=f"addev_{b['id']}", help="Add event"):
                    st.session_state.show_add_event = b["id"]
                    st.session_state.show_add_branch = False
    else:
        st.caption("No branches yet. Create one below.")

    st.divider()

    if st.button("＋ New branch", use_container_width=True):
        st.session_state.show_add_branch = not st.session_state.show_add_branch
        st.session_state.show_add_event = None

    if st.session_state.show_add_branch:
        with st.form("new_branch_form", clear_on_submit=True):
            person = st.text_input("Person name", placeholder="e.g. Prof. Al-Hassan")
            task_title = st.text_input("Task title", placeholder="e.g. Enrolment spreadsheet")
            task_date = st.date_input("Date", value=date.today())
            description = st.text_area("Initial note", placeholder="What was requested?", height=80)
            sp_link = st.text_input("SharePoint link (optional)", placeholder="https://...")
            sp_label = st.text_input("Link label (optional)", placeholder="e.g. enrolment-v1.xlsx")
            submitted = st.form_submit_button("Create branch", use_container_width=True)

            if submitted and person and task_title:
                new_branch = {
                    "id": str(uuid.uuid4())[:8],
                    "person": person,
                    "task_title": task_title,
                    "color": ["#5b8dee", "#e8734a", "#52c97e", "#c97de8", "#e8c34a", "#4ac9c9"][len(branches) % 6],
                    "events": [{
                        "id": str(uuid.uuid4())[:8],
                        "date": task_date.isoformat(),
                        "type": "Initial request",
                        "title": task_title,
                        "description": description,
                        "sharepoint_url": sp_link,
                        "sharepoint_label": sp_label or "View document",
                    }]
                }
                st.session_state.data["branches"].append(new_branch)
                save_data(st.session_state.data)
                st.session_state.show_add_branch = False
                st.rerun()

    if st.session_state.show_add_event:
        branch_id = st.session_state.show_add_event
        branch = next((b for b in branches if b["id"] == branch_id), None)
        if branch:
            st.markdown(f"**Add event to:** {branch['person']}")
            with st.form("new_event_form", clear_on_submit=True):
                ev_date = st.date_input("Date", value=date.today())
                ev_type = st.selectbox("Type", ["Email", "Follow-up", "Created document", "Meeting", "Submitted", "Completed", "Note"])
                ev_title = st.text_input("Title", placeholder="Short description")
                ev_desc = st.text_area("Details", placeholder="What happened?", height=80)
                sp_link = st.text_input("SharePoint link", placeholder="https://...")
                sp_label = st.text_input("Link label", placeholder="e.g. minutes-jan20.docx")
                submitted = st.form_submit_button("Add event", use_container_width=True)
                cancelled = st.form_submit_button("Cancel")

                if submitted and ev_title:
                    new_event = {
                        "id": str(uuid.uuid4())[:8],
                        "date": ev_date.isoformat(),
                        "type": ev_type,
                        "title": ev_title,
                        "description": ev_desc,
                        "sharepoint_url": sp_link,
                        "sharepoint_label": sp_label or "View document",
                    }
                    for b in st.session_state.data["branches"]:
                        if b["id"] == branch_id:
                            b["events"].append(new_event)
                            b["events"].sort(key=lambda e: e["date"])
                    save_data(st.session_state.data)
                    st.session_state.show_add_event = None
                    st.rerun()
                if cancelled:
                    st.session_state.show_add_event = None
                    st.rerun()

    st.divider()
    if st.button("Export JSON", use_container_width=True):
        st.download_button(
            "Download timeline_data.json",
            data=json.dumps(st.session_state.data, indent=2),
            file_name="timeline_data.json",
            mime="application/json",
            use_container_width=True
        )

# ── Main timeline canvas ───────────────────────────────────────────────────────
timeline_data = json.dumps(st.session_state.data)

TIMELINE_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700;800&display=swap');

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: #07070e;
    color: #d0d0e8;
    font-family: 'DM Mono', monospace;
    overflow: hidden;
    width: 100vw;
    height: 100vh;
    cursor: default;
    user-select: none;
  }}

  #canvas-wrap {{
    position: relative;
    width: 100%;
    height: 100%;
    overflow: hidden;
  }}

  #timeline-svg {{
    position: absolute;
    top: 0; left: 0;
    width: 100%;
    height: 100%;
    cursor: grab;
  }}
  #timeline-svg.dragging {{ cursor: grabbing; }}

  /* Event card popup */
  .event-card {{
    position: absolute;
    background: #0f0f1c;
    border: 1px solid #2a2a42;
    border-radius: 10px;
    padding: 16px 18px;
    width: 280px;
    font-size: 11px;
    line-height: 1.7;
    pointer-events: all;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.03);
    animation: cardIn 0.18s cubic-bezier(0.34,1.56,0.64,1);
    z-index: 100;
  }}
  @keyframes cardIn {{
    from {{ opacity: 0; transform: scale(0.88) translateY(6px); }}
    to   {{ opacity: 1; transform: scale(1)    translateY(0); }}
  }}
  .card-type {{
    font-size: 9px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    opacity: 0.45;
    margin-bottom: 5px;
  }}
  .card-title {{
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 13px;
    color: #f0f0ff;
    margin-bottom: 6px;
    line-height: 1.3;
  }}
  .card-date {{
    font-size: 9px;
    letter-spacing: 0.08em;
    opacity: 0.35;
    margin-bottom: 8px;
  }}
  .card-desc {{
    font-size: 11px;
    color: #9090b8;
    line-height: 1.65;
    margin-bottom: 10px;
  }}
  .card-link {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 10px;
    color: #5b8dee;
    text-decoration: none;
    border: 1px solid #5b8dee44;
    border-radius: 6px;
    padding: 5px 10px;
    transition: background 0.15s, border-color 0.15s;
    pointer-events: all;
  }}
  .card-link:hover {{
    background: #5b8dee18;
    border-color: #5b8dee88;
  }}
  .card-close {{
    float: right;
    font-size: 14px;
    cursor: pointer;
    opacity: 0.3;
    line-height: 1;
    margin-left: 8px;
    transition: opacity 0.15s;
  }}
  .card-close:hover {{ opacity: 0.8; }}

  /* Axis date labels */
  .date-label {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    fill: #3a3a58;
    letter-spacing: 0.06em;
  }}

  /* Empty state */
  #empty-state {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -60%);
    text-align: center;
    pointer-events: none;
  }}
  #empty-state h2 {{
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: #2a2a42;
    margin-bottom: 8px;
  }}
  #empty-state p {{
    font-size: 11px;
    color: #28283c;
    letter-spacing: 0.05em;
  }}

  /* Tooltip on hover */
  #node-tooltip {{
    position: absolute;
    background: #1a1a2e;
    border: 1px solid #2a2a42;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 10px;
    color: #c0c0e0;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.1s;
    white-space: nowrap;
    z-index: 200;
  }}
</style>
</head>
<body>
<div id="canvas-wrap">
  <svg id="timeline-svg"></svg>
  <div id="node-tooltip"></div>
  <div id="empty-state" style="display:none">
    <h2>No tasks yet</h2>
    <p>Use the sidebar to create your first branch</p>
  </div>
</div>

<script>
const RAW_DATA = {timeline_data};

const svg = document.getElementById('timeline-svg');
const NS = 'http://www.w3.org/2000/svg';

let W = window.innerWidth;
let H = window.innerHeight;

// Pan state
let panX = 0, panY = 0;
let isDragging = false;
let dragStart = {{x:0, y:0}};
let panStart = {{x:0, y:0}};

// Open cards
let openCards = {{}};  // nodeId -> card element

const AXIS_Y_FRAC = 0.58;
const BRANCH_SPACING = 160;
const MARGIN = 80;
const NODE_R = 5;
const BRANCH_STROKE = 1.5;

function axisY() {{ return H * AXIS_Y_FRAC; }}

// ── Date math ─────────────────────────────────────────────────────────────────
function allDates() {{
  const dates = [];
  for (const b of RAW_DATA.branches) {{
    for (const e of b.events) dates.push(new Date(e.date));
  }}
  return dates;
}}

function dateRange() {{
  const dates = allDates();
  if (!dates.length) return {{ min: new Date(), max: new Date(), span: 1 }};
  const min = new Date(Math.min(...dates));
  const max = new Date(Math.max(...dates));
  // pad 30 days each side
  min.setDate(min.getDate() - 30);
  max.setDate(max.getDate() + 30);
  return {{ min, max, span: (max - min) / 86400000 }};
}}

let DR = dateRange();

function totalWidth() {{
  return Math.max(W * 2, DR.span * 28 + MARGIN * 2);
}}

function dateToX(dateStr) {{
  const d = new Date(dateStr);
  const tw = totalWidth();
  const frac = (d - DR.min) / (DR.max - DR.min);
  return MARGIN + frac * (tw - MARGIN * 2);
}}

function xToDate(x) {{
  const tw = totalWidth();
  const frac = (x - MARGIN) / (tw - MARGIN * 2);
  const ms = DR.min.getTime() + frac * (DR.max.getTime() - DR.min.getTime());
  return new Date(ms);
}}

// ── SVG helpers ───────────────────────────────────────────────────────────────
function el(tag, attrs, parent) {{
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
}}

// ── Render ────────────────────────────────────────────────────────────────────
function render() {{
  W = window.innerWidth;
  H = window.innerHeight;
  svg.setAttribute('width', W);
  svg.setAttribute('height', H);

  // Clear SVG children (keep defs if any)
  while (svg.firstChild) svg.removeChild(svg.firstChild);

  const branches = RAW_DATA.branches;
  const emptyState = document.getElementById('empty-state');

  if (!branches.length) {{
    emptyState.style.display = 'block';
    drawAxis();
    return;
  }}
  emptyState.style.display = 'none';

  drawAxis();
  drawBranches(branches);
}}

function drawAxis() {{
  const tw = totalWidth();
  const ay = axisY();

  // Axis line
  el('line', {{
    x1: panX, y1: ay,
    x2: panX + tw, y2: ay,
    stroke: '#1e1e38', 'stroke-width': '1',
  }}, svg);

  // Month ticks
  const d = new Date(DR.min);
  d.setDate(1);
  while (d <= DR.max) {{
    const x = dateToX(d.toISOString().slice(0,10)) + panX;
    if (x >= -10 && x <= W + 10) {{
      el('line', {{
        x1: x, y1: ay - 5,
        x2: x, y2: ay + 5,
        stroke: '#2a2a44', 'stroke-width': '1'
      }}, svg);
      const lbl = el('text', {{
        x: x, y: ay + 18,
        class: 'date-label',
        'text-anchor': 'middle'
      }}, svg);
      lbl.textContent = d.toLocaleDateString('en-GB', {{month:'short', year:'2-digit'}});

      // Subtle vertical guide
      el('line', {{
        x1: x, y1: 0,
        x2: x, y2: H,
        stroke: '#12122a', 'stroke-width': '1',
        'stroke-dasharray': '3 6'
      }}, svg);
    }}
    d.setMonth(d.getMonth() + 1);
  }}

  // Today marker
  const today = new Date().toISOString().slice(0,10);
  const tx = dateToX(today) + panX;
  el('line', {{
    x1: tx, y1: ay - 12,
    x2: tx, y2: ay + 12,
    stroke: '#5b8dee', 'stroke-width': '1.5'
  }}, svg);
  const todayLbl = el('text', {{
    x: tx, y: ay + 26,
    class: 'date-label',
    'text-anchor': 'middle',
    fill: '#5b8dee'
  }}, svg);
  todayLbl.textContent = 'today';
}}

function drawBranches(branches) {{
  const ay = axisY();

  branches.forEach((branch, bi) => {{
    const events = [...branch.events].sort((a,b) => a.date.localeCompare(b.date));
    if (!events.length) return;

    const color = branch.color || '#5b8dee';
    const colorFaint = color + '30';

    // Determine branch direction: alternate up/down
    const goUp = bi % 2 === 0;
    const dir = goUp ? -1 : 1;

    // Branch height: scale with number of events, min 80
    const branchH = Math.max(80, 50 + events.length * 32);

    // Branch X centre: first event date
    const firstX = dateToX(events[0].date) + panX;
    const lastX  = dateToX(events[events.length-1].date) + panX;

    // Label at branch root
    const labelY = ay + dir * (branchH + 28);
    const labelEl = el('text', {{
      x: firstX,
      y: labelY,
      fill: color,
      'font-family': "'Syne', sans-serif",
      'font-size': '11',
      'font-weight': '600',
      'letter-spacing': '0.04em',
      opacity: '0.85',
      'text-anchor': 'middle',
    }}, svg);
    labelEl.textContent = branch.person;

    const taskLabelEl = el('text', {{
      x: firstX,
      y: labelY + dir * 16,
      fill: color,
      'font-family': "'DM Mono', monospace",
      'font-size': '8.5',
      opacity: '0.4',
      'text-anchor': 'middle',
    }}, svg);
    taskLabelEl.textContent = branch.task_title?.slice(0, 30) || '';

    // Vertical stem from axis to top/bottom of branch
    el('line', {{
      x1: firstX, y1: ay,
      x2: firstX, y2: ay + dir * branchH,
      stroke: color, 'stroke-width': BRANCH_STROKE,
      opacity: '0.3'
    }}, svg);

    // Horizontal run connecting all event nodes
    if (events.length > 1) {{
      el('line', {{
        x1: firstX, y1: ay + dir * branchH,
        x2: lastX,  y2: ay + dir * branchH,
        stroke: color, 'stroke-width': BRANCH_STROKE,
        opacity: '0.5'
      }}, svg);
    }}

    // Event nodes
    events.forEach((ev, ei) => {{
      const nx = dateToX(ev.date) + panX;
      const ny = ay + dir * branchH;

      // Drop line from horizontal run to axis (only if not first)
      if (ei > 0) {{
        el('line', {{
          x1: nx, y1: ay,
          x2: nx, y2: ny,
          stroke: color, 'stroke-width': '1',
          opacity: '0.2',
          'stroke-dasharray': '3 4'
        }}, svg);
      }}

      // Axis intercept dot
      const axisDot = el('circle', {{
        cx: nx, cy: ay,
        r: '3',
        fill: color,
        opacity: '0.4'
      }}, svg);

      // Main node
      const nodeGroup = el('g', {{'cursor': 'pointer'}}, svg);
      const isOpen = !!openCards[ev.id];

      // Glow ring when open
      if (isOpen) {{
        el('circle', {{
          cx: nx, cy: ny,
          r: NODE_R + 5,
          fill: 'none',
          stroke: color,
          'stroke-width': '1',
          opacity: '0.3'
        }}, nodeGroup);
      }}

      el('circle', {{
        cx: nx, cy: ny,
        r: NODE_R,
        fill: isOpen ? color : '#07070e',
        stroke: color,
        'stroke-width': '2',
        opacity: '0.95'
      }}, nodeGroup);

      // Event type micro-label
      const typeLbl = el('text', {{
        x: nx,
        y: ny + dir * (-NODE_R - 6),
        fill: color,
        'font-family': "'DM Mono', monospace",
        'font-size': '7.5',
        opacity: '0.45',
        'text-anchor': 'middle',
        'letter-spacing': '0.06em',
      }}, nodeGroup);
      typeLbl.textContent = ev.type?.toUpperCase().slice(0, 6) || '';

      // Hover tooltip & click
      nodeGroup.addEventListener('mouseenter', (e) => {{
        const tt = document.getElementById('node-tooltip');
        tt.textContent = ev.title + ' · ' + ev.date;
        tt.style.left = (e.clientX + 12) + 'px';
        tt.style.top  = (e.clientY - 10) + 'px';
        tt.style.opacity = '1';
      }});
      nodeGroup.addEventListener('mouseleave', () => {{
        document.getElementById('node-tooltip').style.opacity = '0';
      }});
      nodeGroup.addEventListener('click', (e) => {{
        e.stopPropagation();
        toggleCard(ev, nx, ny, dir, color);
      }});
    }});
  }});
}}

// ── Event cards ───────────────────────────────────────────────────────────────
function toggleCard(ev, nx, ny, dir, color) {{
  if (openCards[ev.id]) {{
    openCards[ev.id].remove();
    delete openCards[ev.id];
    render();
    return;
  }}

  const card = document.createElement('div');
  card.className = 'event-card';
  card.style.borderColor = color + '55';
  card.style.left = (nx - 140) + 'px';

  const CARD_H_EST = 160;
  if (dir < 0) {{
    // branch goes up → card above node
    card.style.top = (ny - CARD_H_EST - 24) + 'px';
  }} else {{
    // branch goes down → card below node
    card.style.top = (ny + 18) + 'px';
  }}

  const closeBtn = `<span class="card-close" onclick="closeCard('${{ev.id}}')">✕</span>`;
  const linkHtml = ev.sharepoint_url
    ? `<a class="card-link" href="${{ev.sharepoint_url}}" target="_blank">
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M2 2h4v1H3v6h6V8h1v2a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z" fill="#5b8dee"/>
          <path d="M7 2h3v3h-1V3.7L5.35 7.35l-.7-.7L8.3 3H7V2z" fill="#5b8dee"/>
        </svg>
        ${{ev.sharepoint_label || 'View document'}}
      </a>`
    : '';

  card.innerHTML = `
    ${{closeBtn}}
    <div class="card-type" style="color:${{color}}">${{ev.type || 'Event'}}</div>
    <div class="card-title">${{ev.title}}</div>
    <div class="card-date">${{ev.date}}</div>
    ${{ev.description ? `<div class="card-desc">${{ev.description}}</div>` : ''}}
    ${{linkHtml}}
  `;

  document.getElementById('canvas-wrap').appendChild(card);
  openCards[ev.id] = card;
  render();
}}

window.closeCard = function(id) {{
  if (openCards[id]) {{
    openCards[id].remove();
    delete openCards[id];
    render();
  }}
}};

// ── Pan ───────────────────────────────────────────────────────────────────────
svg.addEventListener('mousedown', (e) => {{
  if (e.button !== 0) return;
  isDragging = true;
  dragStart = {{x: e.clientX, y: e.clientY}};
  panStart = {{x: panX, y: panY}};
  svg.classList.add('dragging');
}});

window.addEventListener('mousemove', (e) => {{
  if (!isDragging) return;
  panX = panStart.x + (e.clientX - dragStart.x);
  panY = panStart.y + (e.clientY - dragStart.y);
  // Clamp pan
  const tw = totalWidth();
  panX = Math.min(MARGIN, Math.max(-(tw - W + MARGIN), panX));

  // Move open cards
  const dx = panX - panStart.x;
  for (const card of Object.values(openCards)) {{
    const l = parseFloat(card.style.left);
    card.style.left = (l + (e.clientX - dragStart.x) - (panStart.x === panX ? 0 : 0)) + 'px';
  }}
  // Re-render incrementally  
  render();
  // Re-position cards relative to new pan
  positionOpenCards();
}});

window.addEventListener('mouseup', () => {{
  isDragging = false;
  svg.classList.remove('dragging');
}});

function positionOpenCards() {{
  // Cards are positioned absolutely — on pan we rebuild
  // simpler: just re-render clears them, so close all on pan start
}}

svg.addEventListener('mousedown', () => {{
  // Close all cards when starting a drag
  panStart = {{x: panX, y: panY}};
}});

// Close cards on pan
svg.addEventListener('mousedown', () => {{
  for (const [id, card] of Object.entries(openCards)) {{
    card.remove();
  }}
  openCards = {{}};
}});

// Wheel scroll → pan horizontally
svg.addEventListener('wheel', (e) => {{
  e.preventDefault();
  panX -= e.deltaX || e.deltaY;
  const tw = totalWidth();
  panX = Math.min(MARGIN, Math.max(-(tw - W + MARGIN), panX));
  render();
}}, {{passive: false}});

window.addEventListener('resize', () => {{ render(); }});

render();
</script>
</body>
</html>
"""

st.components.v1.html(TIMELINE_HTML, height=700, scrolling=False)

# Global CSS for the main Streamlit page
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #07070e !important;
    font-family: 'DM Mono', monospace !important;
}
[data-testid="stAppViewContainer"] > .main {
    background: #07070e !important;
    padding: 0 !important;
}
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}
iframe {
    border: none !important;
    display: block;
}
header[data-testid="stHeader"] { background: transparent !important; }
</style>
""", unsafe_allow_html=True)
