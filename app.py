import streamlit as st
import json
import os

st.set_page_config(
    page_title="Task Timeline · Zakaria",
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

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

if "data" not in st.session_state:
    st.session_state.data = load_data()

timeline_json = json.dumps(st.session_state.data)

COLORS = ["#5b8dee", "#e8734a", "#52c97e", "#c97de8", "#e8c34a", "#4ac9c9",
          "#ee5b8d", "#8dee5b", "#ee5b5b", "#5beedb"]

TIMELINE_HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Syne:wght@400;600;700;800&display=swap');
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#07070e;color:#d0d0e8;font-family:'DM Mono',monospace;overflow:hidden;width:100vw;height:100vh}}
#wrap{{position:relative;width:100%;height:100%;overflow:hidden}}
#svg{{position:absolute;top:0;left:0;width:100%;height:100%;cursor:grab}}
#svg.dragging{{cursor:grabbing}}

.ecard{{
  position:absolute;background:#0d0d1a;border:1px solid #252538;border-radius:12px;
  padding:18px 20px 16px;width:300px;font-size:11px;line-height:1.75;pointer-events:all;
  box-shadow:0 12px 40px rgba(0,0,0,.7),0 0 0 1px rgba(255,255,255,.04);
  animation:cardIn .18s cubic-bezier(.34,1.56,.64,1);z-index:100
}}
@keyframes cardIn{{from{{opacity:0;transform:scale(.88) translateY(6px)}}to{{opacity:1;transform:scale(1) translateY(0)}}}}
.card-header{{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:10px}}
.card-type{{font-size:8.5px;letter-spacing:.14em;text-transform:uppercase;opacity:.45;margin-bottom:4px}}
.card-title{{font-family:'Syne',sans-serif;font-weight:700;font-size:13px;color:#f0f0ff;line-height:1.3}}
.card-meta{{font-size:9px;opacity:.3;margin-top:3px;letter-spacing:.06em}}
.card-desc{{font-size:11px;color:#8888aa;line-height:1.7;margin:10px 0}}
.card-link{{
  display:inline-flex;align-items:center;gap:5px;font-size:10px;color:#5b8dee;
  text-decoration:none;border:1px solid #5b8dee44;border-radius:6px;padding:5px 10px;
  margin-top:4px;transition:background .15s,border-color .15s;cursor:pointer;
  background:transparent;width:100%;word-break:break-all
}}
.card-link:hover{{background:#5b8dee18;border-color:#5b8dee88}}
.card-close{{font-size:13px;cursor:pointer;opacity:.25;line-height:1;transition:opacity .15s;flex-shrink:0;margin-left:8px;padding:2px}}
.card-close:hover{{opacity:.7}}
.card-divider{{height:1px;background:#1e1e32;margin:12px 0}}
.card-field{{
  width:100%;background:#0a0a16;border:1px solid #1e1e30;border-radius:6px;
  color:#d0d0e8;font-family:'DM Mono',monospace;font-size:11px;padding:6px 8px;
  margin-bottom:6px;resize:vertical;transition:border-color .15s
}}
.card-field:focus{{outline:none;border-color:#5b8dee66}}
.card-field-label{{font-size:9px;letter-spacing:.1em;opacity:.35;margin-bottom:3px;text-transform:uppercase}}
.card-actions{{display:flex;gap:8px;margin-top:12px}}
.btn{{
  flex:1;font-family:'DM Mono',monospace;font-size:10px;padding:7px;border-radius:6px;
  cursor:pointer;border:1px solid #2a2a40;background:#0f0f1e;color:#9090b8;
  transition:background .15s,border-color .15s,color .15s;letter-spacing:.05em
}}
.btn:hover{{background:#1a1a2e;border-color:#3a3a58;color:#d0d0e8}}
.btn.primary{{background:#5b8dee22;border-color:#5b8dee55;color:#5b8dee}}
.btn.primary:hover{{background:#5b8dee33;border-color:#5b8dee}}
.btn.danger{{color:#ee5b5b;border-color:#ee5b5b33}}
.btn.danger:hover{{background:#ee5b5b18;border-color:#ee5b5b66}}

#toolbar{{
  position:fixed;top:0;left:0;right:0;height:48px;
  background:#090914cc;backdrop-filter:blur(12px);border-bottom:1px solid #1a1a2a;
  display:flex;align-items:center;padding:0 20px;gap:14px;z-index:300;font-size:12px
}}
#toolbar-title{{font-family:'Syne',sans-serif;font-weight:700;font-size:15px;color:#f0f0ff;letter-spacing:.02em;margin-right:4px}}
#toolbar-sub{{font-size:10px;opacity:.28;letter-spacing:.06em}}
.tb-sep{{width:1px;height:20px;background:#1e1e30;flex-shrink:0}}
.tb-btn{{
  font-family:'DM Mono',monospace;font-size:10px;padding:5px 12px;border-radius:6px;
  cursor:pointer;border:1px solid #2a2a40;background:transparent;color:#9090b8;
  transition:background .15s,border-color .15s,color .15s;white-space:nowrap;letter-spacing:.05em
}}
.tb-btn:hover{{background:#1a1a2e;border-color:#3a3a58;color:#d0d0e8}}
.tb-btn.accent{{background:#5b8dee18;border-color:#5b8dee44;color:#5b8dee}}
.tb-btn.accent:hover{{background:#5b8dee28;border-color:#5b8dee}}
#tb-spacer{{flex:1}}

.panel{{
  position:fixed;right:0;top:48px;bottom:0;width:300px;background:#09091a;
  border-left:1px solid #1a1a2a;padding:22px 18px;overflow-y:auto;z-index:250;
  transform:translateX(100%);transition:transform .25s cubic-bezier(.4,0,.2,1)
}}
.panel.open{{transform:translateX(0)}}
.panel-title{{font-family:'Syne',sans-serif;font-weight:700;font-size:15px;color:#f0f0ff;margin-bottom:18px}}
.panel-label{{font-size:9px;letter-spacing:.12em;opacity:.4;margin-bottom:4px;text-transform:uppercase}}
.panel-field{{
  width:100%;background:#0d0d1c;border:1px solid #1e1e30;border-radius:8px;
  color:#d0d0e8;font-family:'DM Mono',monospace;font-size:11px;padding:8px 10px;
  margin-bottom:13px;resize:vertical;transition:border-color .15s
}}
.panel-field:focus{{outline:none;border-color:#5b8dee66}}
select.panel-field{{cursor:pointer}}
.panel-btn{{
  width:100%;font-family:'DM Mono',monospace;font-size:11px;padding:10px;
  border-radius:8px;cursor:pointer;margin-top:4px;letter-spacing:.05em;
  transition:background .15s,border-color .15s
}}
.panel-btn.primary{{background:#5b8dee;border:none;color:#fff;font-weight:500}}
.panel-btn.primary:hover{{background:#4a7ddd}}
.panel-btn.cancel{{background:transparent;border:1px solid #2a2a40;color:#606080;margin-top:8px}}
.panel-btn.cancel:hover{{background:#1a1a28;color:#9090b8}}

#tt{{
  position:fixed;background:#1a1a2e;border:1px solid #2a2a42;border-radius:6px;
  padding:4px 10px;font-size:10px;color:#c0c0e0;pointer-events:none;opacity:0;
  transition:opacity .1s;white-space:nowrap;z-index:400
}}
.dlabel{{font-family:'DM Mono',monospace;font-size:9px;fill:#2a2a44;letter-spacing:.06em}}
</style>
</head>
<body>

<div id="toolbar">
  <span id="toolbar-title">◈ Task Timeline</span>
  <span id="toolbar-sub">Zakaria · ACI Faculty Operations</span>
  <div class="tb-sep"></div>
  <button class="tb-btn accent" onclick="openNewBranch()">＋ New branch</button>
  <button class="tb-btn" onclick="openNewEvent(null)">＋ Add event</button>
  <div class="tb-sep"></div>
  <button class="tb-btn" onclick="exportData()">⬇ Export JSON</button>
  <div id="tb-spacer"></div>
  <span style="font-size:9px;opacity:.2;letter-spacing:.05em">drag · scroll · click nodes</span>
</div>

<div id="wrap" style="padding-top:48px">
  <svg id="svg" xmlns="http://www.w3.org/2000/svg"></svg>
</div>

<!-- New Branch Panel -->
<div class="panel" id="panel-branch">
  <div class="panel-title">New branch</div>
  <div class="panel-label">Person</div>
  <input class="panel-field" id="nb-person" placeholder="e.g. Prof. Al-Hassan" type="text">
  <div class="panel-label">Task title</div>
  <input class="panel-field" id="nb-title" placeholder="e.g. Enrolment spreadsheet" type="text">
  <div class="panel-label">Date</div>
  <input class="panel-field" id="nb-date" type="date">
  <div class="panel-label">Form of request</div>
  <select class="panel-field" id="nb-form">
    <option>Email</option><option>Teams Call</option><option>Meeting</option>
    <option>In Person Request</option><option>Team Message</option><option>Other</option>
  </select>
  <div class="panel-label">Priority</div>
  <select class="panel-field" id="nb-priority">
    <option value="">—</option><option>High</option><option>Medium</option><option>Low</option>
  </select>
  <div class="panel-label">Description</div>
  <textarea class="panel-field" id="nb-desc" rows="3" placeholder="What was requested?"></textarea>
  <div class="panel-label">SharePoint link (optional)</div>
  <input class="panel-field" id="nb-link" placeholder="https://…" type="url">
  <div class="panel-label">Link label</div>
  <input class="panel-field" id="nb-linklabel" placeholder="e.g. document-v1.xlsx">
  <div class="panel-label">Time taken</div>
  <input class="panel-field" id="nb-time" placeholder="e.g. 30 mins">
  <button class="panel-btn primary" onclick="submitNewBranch()">Create branch</button>
  <button class="panel-btn cancel" onclick="closePanel('panel-branch')">Cancel</button>
</div>

<!-- New Event Panel -->
<div class="panel" id="panel-event">
  <div class="panel-title">Add event</div>
  <div class="panel-label">Branch</div>
  <select class="panel-field" id="ne-branch"></select>
  <div class="panel-label">Date</div>
  <input class="panel-field" id="ne-date" type="date">
  <div class="panel-label">Form / type</div>
  <select class="panel-field" id="ne-form">
    <option>Email</option><option>Teams Call</option><option>Meeting</option>
    <option>In Person Request</option><option>Team Message</option>
    <option>Follow-up</option><option>Completed</option><option>Note</option><option>Other</option>
  </select>
  <div class="panel-label">Priority</div>
  <select class="panel-field" id="ne-priority">
    <option value="">—</option><option>High</option><option>Medium</option><option>Low</option>
  </select>
  <div class="panel-label">Title</div>
  <input class="panel-field" id="ne-title" placeholder="Short summary">
  <div class="panel-label">Notes / description</div>
  <textarea class="panel-field" id="ne-desc" rows="3" placeholder="Details…"></textarea>
  <div class="panel-label">SharePoint link (optional)</div>
  <input class="panel-field" id="ne-link" placeholder="https://…" type="url">
  <div class="panel-label">Link label</div>
  <input class="panel-field" id="ne-linklabel" placeholder="e.g. minutes-jan20.docx">
  <div class="panel-label">Time taken</div>
  <input class="panel-field" id="ne-time" placeholder="e.g. 1.5 Hours">
  <button class="panel-btn primary" onclick="submitNewEvent()">Add event</button>
  <button class="panel-btn cancel" onclick="closePanel('panel-event')">Cancel</button>
</div>

<div id="tt"></div>

<script>
let DATA = {timeline_json};
const COLORS = {json.dumps(COLORS)};
const SVG_NS='http://www.w3.org/2000/svg';
const svg=document.getElementById('svg');
const wrap=document.getElementById('wrap');

let panX=0,isDragging=false,dragStart={{x:0,y:0}},panStart={{x:0,y:0}};
let openCards={{}};

const AXIS_FRAC=0.52, NODE_R=6, PX_DAY=32, MARGIN=110;

// ── Dates ──────────────────────────────────────────────────────────────────
const parse=s=>new Date(s+'T12:00:00');
const today=()=>new Date().toISOString().slice(0,10);

function DR(){{
  const all=DATA.branches.flatMap(b=>b.events.map(e=>parse(e.date)));
  if(!all.length){{const t=new Date();return{{min:new Date(t.getFullYear(),t.getMonth()-1,1),max:new Date(t.getFullYear(),t.getMonth()+3,1)}};}}
  const mn=new Date(Math.min(...all)),mx=new Date(Math.max(...all));
  mn.setDate(mn.getDate()-40);mx.setDate(mx.getDate()+40);
  return{{min:mn,max:mx,span:(mx-mn)/864e5}};
}}

function totalW(dr){{return Math.max(window.innerWidth*1.5,dr.span*PX_DAY+MARGIN*2);}}

function d2x(dateStr,dr,tw){{
  return MARGIN+(parse(dateStr)-dr.min)/(dr.max-dr.min)*(tw-MARGIN*2)+panX;
}}

// ── SVG ────────────────────────────────────────────────────────────────────
function se(tag,a,p){{
  const e=document.createElementNS(SVG_NS,tag);
  Object.entries(a).forEach(([k,v])=>e.setAttribute(k,v));
  p&&p.appendChild(e);return e;
}}

// ── Render ──────────────────────────────────────────────────────────────────
function render(){{
  const W=window.innerWidth,H=wrap.clientHeight||window.innerHeight-48;
  svg.setAttribute('width',W);svg.setAttribute('height',H);
  while(svg.firstChild)svg.removeChild(svg.firstChild);
  const dr=DR(),tw=totalW(dr),ay=H*AXIS_FRAC;
  drawAxis(W,H,ay,dr,tw);
  DATA.branches.forEach((b,i)=>drawBranch(b,i,ay,H,dr,tw));
}}

function drawAxis(W,H,ay,dr,tw){{
  se('line',{{x1:panX,y1:ay,x2:panX+tw,y2:ay,stroke:'#161624','stroke-width':'1'}},svg);
  const d=new Date(dr.min);d.setDate(1);
  while(d<=dr.max){{
    const x=MARGIN+(d-dr.min)/(dr.max-dr.min)*(tw-MARGIN*2)+panX;
    if(x>-20&&x<W+20){{
      se('line',{{x1:x,y1:ay-6,x2:x,y2:ay+6,stroke:'#1e1e34','stroke-width':'1'}},svg);
      se('line',{{x1:x,y1:0,x2:x,y2:H,stroke:'#0e0e1e','stroke-width':'1','stroke-dasharray':'2 8'}},svg);
      const lbl=se('text',{{x,y:ay+20,class:'dlabel','text-anchor':'middle'}},svg);
      lbl.textContent=d.toLocaleDateString('en-GB',{{month:'short',year:'2-digit'}});
    }}
    d.setMonth(d.getMonth()+1);
  }}
  const tx=MARGIN+(new Date(today()+'T12:00:00')-dr.min)/(dr.max-dr.min)*(tw-MARGIN*2)+panX;
  if(tx>0&&tx<W){{
    se('line',{{x1:tx,y1:ay-14,x2:tx,y2:ay+14,stroke:'#5b8dee','stroke-width':'1.5',opacity:'.8'}},svg);
    const tl=se('text',{{x:tx,y:ay+30,class:'dlabel','text-anchor':'middle',fill:'#5b8dee55','font-size':'8'}},svg);
    tl.textContent='today';
  }}
}}

function drawBranch(branch,idx,ay,H,dr,tw){{
  const evs=[...branch.events].sort((a,b)=>a.date.localeCompare(b.date));
  if(!evs.length)return;
  const col=branch.color||COLORS[idx%COLORS.length];
  const goUp=idx%2===0,dir=goUp?-1:1;
  const STEM=Math.min(80+evs.length*24,goUp?ay-55:H-ay-55);
  const nodeY=ay+dir*STEM;
  const x0=d2x(evs[0].date,dr,tw),x1=d2x(evs[evs.length-1].date,dr,tw);

  se('line',{{x1:x0,y1:ay,x2:x0,y2:nodeY,stroke:col,'stroke-width':'1.5',opacity:'.3'}},svg);
  if(evs.length>1)se('line',{{x1:x0,y1:nodeY,x2:x1,y2:nodeY,stroke:col,'stroke-width':'1.5',opacity:'.5'}},svg);

  // branch labels — add event button
  const lx=x0,ly=nodeY+dir*28;
  const lg=se('g',{{style:'cursor:pointer'}},svg);
  const lbl=se('text',{{x:lx,y:ly,fill:col,'font-family':"'Syne',sans-serif",'font-size':'11','font-weight':'700','letter-spacing':'.03em','text-anchor':'middle',opacity:'.9'}},lg);
  lbl.textContent=branch.person;
  const sub=se('text',{{x:lx,y:ly+dir*14,fill:col,'font-family':"'DM Mono',monospace",'font-size':'8','text-anchor':'middle',opacity:'.32'}},lg);
  sub.textContent=(branch.task_title||'').slice(0,30);
  // small + to add event to this branch
  const addBtn=se('text',{{x:lx+4,y:ly+dir*26,fill:col,'font-size':'14','text-anchor':'middle',opacity:'.35',style:'cursor:pointer',title:'Add event'}},lg);
  addBtn.textContent='＋';
  addBtn.addEventListener('click',e=>{{e.stopPropagation();openNewEvent(branch.id);}});
  addBtn.addEventListener('mouseenter',()=>addBtn.setAttribute('opacity','.8'));
  addBtn.addEventListener('mouseleave',()=>addBtn.setAttribute('opacity','.35'));

  evs.forEach((ev,ei)=>{{
    const nx=d2x(ev.date,dr,tw),ny=nodeY;
    if(ei>0)se('line',{{x1:nx,y1:ay,x2:nx,y2:ny,stroke:col,'stroke-width':'1',opacity:'.15','stroke-dasharray':'2 5'}},svg);
    se('circle',{{cx:nx,cy:ay,r:'2.5',fill:col,opacity:'.4'}},svg);
    const isOpen=!!openCards[ev.id];
    const g=se('g',{{style:'cursor:pointer'}},svg);
    if(isOpen)se('circle',{{cx:nx,cy:ny,r:NODE_R+6,fill:'none',stroke:col,'stroke-width':'1',opacity:'.22'}},g);
    se('circle',{{cx:nx,cy:ny,r:NODE_R,fill:isOpen?col:'#07070e',stroke:col,'stroke-width':'2',opacity:'.95'}},g);
    const tly=ny+dir*(-(NODE_R+7));
    const tll=se('text',{{x:nx,y:tly,fill:col,'font-size':'7','text-anchor':'middle','letter-spacing':'.08em','font-family':"'DM Mono',monospace",opacity:'.38'}},g);
    tll.textContent=(ev.form||ev.type||'').toUpperCase().slice(0,6);
    g.addEventListener('mouseenter',e=>{{
      const tt=document.getElementById('tt');
      tt.textContent=ev.title+' · '+ev.date;
      tt.style.left=(e.clientX+14)+'px';tt.style.top=(e.clientY-10)+'px';tt.style.opacity='1';
    }});
    g.addEventListener('mouseleave',()=>{{document.getElementById('tt').style.opacity='0';}});
    g.addEventListener('click',e=>{{e.stopPropagation();toggleCard(ev,branch,nx,ny,dir,col);}});
  }});
}}

// ── Cards ───────────────────────────────────────────────────────────────────
function toggleCard(ev,branch,nx,ny,dir,col){{
  if(openCards[ev.id]){{openCards[ev.id].el.remove();delete openCards[ev.id];render();return;}}
  const card=document.createElement('div');
  card.className='ecard';
  card.style.borderColor=col+'44';
  card.style.left=(nx-150)+'px';
  card.style.top=(dir<0?(ny-270-20):(ny+20))+'px';
  card.innerHTML=cardViewHTML(ev,branch,col);
  wrap.appendChild(card);
  openCards[ev.id]={{el:card,branch,nx,ny,dir,col}};
  render();
}}

function cardViewHTML(ev,branch,col){{
  const pri=ev.priority;
  const priHtml=pri?`<span style="font-size:8px;padding:2px 7px;border-radius:10px;
    background:${{pri==='High'?'#ee5b5b22':pri==='Medium'?'#e8c34a22':'#52c97e22'}};
    color:${{pri==='High'?'#ee5b5b':pri==='Medium'?'#e8c34a':'#52c97e'}};margin-left:6px">${{pri}}</span>`:'';
  const linkHtml=ev.sharepoint_url
    ?`<a class="card-link" href="${{ev.sharepoint_url}}" target="_blank">
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
          <path d="M2 2h4v1H3v6h6V8h1v2a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z" fill="#5b8dee"/>
          <path d="M7 2h3v3h-1V3.7L5.35 7.35l-.7-.7L8.3 3H7V2z" fill="#5b8dee"/>
        </svg>${{ev.sharepoint_label||'View document'}}</a>`:'';
  return`<div class="card-header">
    <div>
      <div class="card-type" style="color:${{col}}">${{ev.form||ev.type||'Event'}}${{priHtml}}</div>
      <div class="card-title">${{ev.title}}</div>
      <div class="card-meta">${{ev.date}}${{ev.time_taken?' · '+ev.time_taken:''}}</div>
    </div>
    <span class="card-close" onclick="closeCard('${{ev.id}}')">✕</span>
  </div>
  ${{ev.description?`<div class="card-desc">${{ev.description}}</div>`:'<div style="height:4px"></div>'}}
  ${{linkHtml}}
  <div class="card-divider"></div>
  <div class="card-actions">
    <button class="btn primary" onclick="startEdit('${{ev.id}}','${{branch.id}}')">Edit</button>
    <button class="btn danger" onclick="deleteEvent('${{ev.id}}','${{branch.id}}')">Delete</button>
  </div>`;
}}

function cardEditHTML(ev,col){{
  return`<div class="card-header">
    <div class="card-title" style="font-size:12px;color:${{col}}">Edit event</div>
    <span class="card-close" onclick="cancelEdit('${{ev.id}}')">✕</span>
  </div>
  <div class="card-field-label">Date</div>
  <input class="card-field" id="ef-date-${{ev.id}}" value="${{ev.date}}" type="date">
  <div class="card-field-label">Form / type</div>
  <input class="card-field" id="ef-form-${{ev.id}}" value="${{ev.form||ev.type||''}}">
  <div class="card-field-label">Priority</div>
  <select class="card-field" id="ef-pri-${{ev.id}}">
    <option value="" ${{!ev.priority?'selected':''}}>—</option>
    <option ${{ev.priority==='High'?'selected':''}}>High</option>
    <option ${{ev.priority==='Medium'?'selected':''}}>Medium</option>
    <option ${{ev.priority==='Low'?'selected':''}}>Low</option>
  </select>
  <div class="card-field-label">Title</div>
  <input class="card-field" id="ef-title-${{ev.id}}" value="${{(ev.title||'').replace(/"/g,'&quot;')}}">
  <div class="card-field-label">Notes</div>
  <textarea class="card-field" id="ef-desc-${{ev.id}}" rows="3">${{ev.description||''}}</textarea>
  <div class="card-field-label">SharePoint link</div>
  <input class="card-field" id="ef-link-${{ev.id}}" value="${{ev.sharepoint_url||''}}" type="url">
  <div class="card-field-label">Link label</div>
  <input class="card-field" id="ef-linklabel-${{ev.id}}" value="${{ev.sharepoint_label||''}}">
  <div class="card-field-label">Time taken</div>
  <input class="card-field" id="ef-time-${{ev.id}}" value="${{ev.time_taken||''}}">
  <div class="card-actions">
    <button class="btn primary" onclick="saveEdit('${{ev.id}}')">Save</button>
    <button class="btn" onclick="cancelEdit('${{ev.id}}')">Cancel</button>
  </div>`;
}}

window.closeCard=id=>{{if(openCards[id]){{openCards[id].el.remove();delete openCards[id];render();}}}};

window.startEdit=(evId,branchId)=>{{
  const branch=DATA.branches.find(b=>b.id===branchId);
  const ev=branch?.events.find(e=>e.id===evId);
  if(!ev||!openCards[evId])return;
  openCards[evId].el.innerHTML=cardEditHTML(ev,openCards[evId].col);
}};

window.cancelEdit=evId=>{{
  const oc=openCards[evId];if(!oc)return;
  const branch=oc.branch;
  const ev=branch.events.find(e=>e.id===evId);
  if(!ev)return;
  oc.el.innerHTML=cardViewHTML(ev,branch,oc.col);
}};

window.saveEdit=evId=>{{
  const oc=openCards[evId];if(!oc)return;
  const branch=oc.branch;
  const ev=branch.events.find(e=>e.id===evId);
  if(!ev)return;
  const g=id=>document.getElementById(id+'_'+evId)||document.getElementById(id+evId)||document.getElementById('ef-'+id.replace('ef-','')+'-'+evId);
  const fld=suffix=>document.getElementById('ef-'+suffix+'-'+evId)?.value;
  ev.date=fld('date')||ev.date;
  ev.form=fld('form')||ev.form;
  ev.priority=fld('pri')||'';
  ev.title=fld('title')||ev.title;
  ev.description=document.getElementById('ef-desc-'+evId)?.value||'';
  ev.sharepoint_url=fld('link')||'';
  ev.sharepoint_label=fld('linklabel')||'';
  ev.time_taken=fld('time')||'';
  branch.events.sort((a,b)=>a.date.localeCompare(b.date));
  persist();render();
  oc.el.innerHTML=cardViewHTML(ev,branch,oc.col);
}};

window.deleteEvent=(evId,branchId)=>{{
  if(!confirm('Delete this event?'))return;
  const branch=DATA.branches.find(b=>b.id===branchId);
  if(!branch)return;
  branch.events=branch.events.filter(e=>e.id!==evId);
  if(openCards[evId]){{openCards[evId].el.remove();delete openCards[evId];}}
  persist();render();
}};

// ── Panels ──────────────────────────────────────────────────────────────────
function togglePanel(id){{
  ['panel-branch','panel-event'].forEach(p=>{{
    const el=document.getElementById(p);
    if(p===id)el.classList.toggle('open');
    else el.classList.remove('open');
  }});
}}
window.closePanel=id=>document.getElementById(id).classList.remove('open');

window.openNewBranch=()=>{{
  document.getElementById('nb-date').value=today();
  togglePanel('panel-branch');
}};

window.openNewEvent=(branchId)=>{{
  const sel=document.getElementById('ne-branch');
  sel.innerHTML='';
  DATA.branches.forEach(b=>{{
    const o=document.createElement('option');
    o.value=b.id;o.textContent=b.person+' — '+b.task_title;
    if(branchId&&b.id===branchId)o.selected=true;
    sel.appendChild(o);
  }});
  document.getElementById('ne-date').value=today();
  togglePanel('panel-event');
}};

window.submitNewBranch=()=>{{
  const person=document.getElementById('nb-person').value.trim();
  const title=document.getElementById('nb-title').value.trim();
  const d=document.getElementById('nb-date').value;
  if(!person||!title||!d){{alert('Person, title and date required.');return;}}
  DATA.branches.push({{
    id:uid(),person,task_title:title,
    color:COLORS[DATA.branches.length%COLORS.length],
    events:[{{
      id:uid(),date:d,
      form:document.getElementById('nb-form').value,
      priority:document.getElementById('nb-priority').value,
      title,
      description:document.getElementById('nb-desc').value.trim(),
      sharepoint_url:document.getElementById('nb-link').value.trim(),
      sharepoint_label:document.getElementById('nb-linklabel').value.trim()||'View document',
      time_taken:document.getElementById('nb-time').value.trim()
    }}]
  }});
  closePanel('panel-branch');persist();render();
}};

window.submitNewEvent=()=>{{
  const branchId=document.getElementById('ne-branch').value;
  const branch=DATA.branches.find(b=>b.id===branchId);
  if(!branch)return;
  const d=document.getElementById('ne-date').value;
  const title=document.getElementById('ne-title').value.trim();
  if(!d||!title){{alert('Date and title required.');return;}}
  branch.events.push({{
    id:uid(),date:d,
    form:document.getElementById('ne-form').value,
    priority:document.getElementById('ne-priority').value,
    title,
    description:document.getElementById('ne-desc').value.trim(),
    sharepoint_url:document.getElementById('ne-link').value.trim(),
    sharepoint_label:document.getElementById('ne-linklabel').value.trim()||'View document',
    time_taken:document.getElementById('ne-time').value.trim()
  }});
  branch.events.sort((a,b)=>a.date.localeCompare(b.date));
  closePanel('panel-event');persist();render();
}};

// ── Persist ─────────────────────────────────────────────────────────────────
function persist(){{
  try{{localStorage.setItem('aci_timeline',JSON.stringify(DATA));}}catch(e){{}}
  // Signal to parent Streamlit for file save (best-effort)
  try{{window.parent.postMessage({{type:'streamlit:setComponentValue',value:JSON.stringify(DATA)}},'*');}}catch(e){{}}
}}

window.exportData=()=>{{
  const blob=new Blob([JSON.stringify(DATA,null,2)],{{type:'application/json'}});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download='timeline_data.json';a.click();
}};

// Restore from localStorage if available (client-side persistence between refreshes)
try{{
  const saved=localStorage.getItem('aci_timeline');
  if(saved){{const parsed=JSON.parse(saved);if(parsed.branches)DATA=parsed;}}
}}catch(e){{}}

// ── Pan & scroll ─────────────────────────────────────────────────────────────
svg.addEventListener('mousedown',e=>{{
  if(e.button!==0)return;
  Object.values(openCards).forEach(c=>c.el.remove());openCards={{}};
  isDragging=true;dragStart={{x:e.clientX}};panStart={{x:panX}};
  svg.classList.add('dragging');
}});
window.addEventListener('mousemove',e=>{{
  if(!isDragging)return;
  panX=panStart.x+(e.clientX-dragStart.x);
  const dr=DR(),tw=totalW(dr);
  panX=Math.min(MARGIN,Math.max(-(tw-window.innerWidth+MARGIN),panX));
  render();
}});
window.addEventListener('mouseup',()=>{{isDragging=false;svg.classList.remove('dragging');}});
svg.addEventListener('wheel',e=>{{
  e.preventDefault();
  panX-=(e.deltaX||e.deltaY)*.8;
  const dr=DR(),tw=totalW(dr);
  panX=Math.min(MARGIN,Math.max(-(tw-window.innerWidth+MARGIN),panX));
  render();
}},{{passive:false}});
window.addEventListener('resize',render);

function uid(){{return Math.random().toString(36).slice(2,10);}}

render();
</script>
</body>
</html>"""

st.components.v1.html(TIMELINE_HTML, height=800, scrolling=False)

st.markdown("""
<style>
html,body,[data-testid="stAppViewContainer"]{{background:#07070e !important}}
[data-testid="stAppViewContainer"]>.main{{background:#07070e !important;padding:0 !important}}
.block-container{{padding:0 !important;max-width:100% !important}}
iframe{{border:none !important;display:block}}
header[data-testid="stHeader"]{{display:none !important}}
[data-testid="stDecoration"]{{display:none !important}}
footer{{display:none !important}}
</style>
""", unsafe_allow_html=True)
