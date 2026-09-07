import json
G=open('eb-plan-graph.json').read()
C=open('/mnt/user-data/uploads/eb-demand-cards.json').read()
CI=json.dumps(json.load(open('eb-cities-verified.json'))['cities'],separators=(',',':'))
CORE=open('core.js').read().split('if(typeof module')[0]
HTML="""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Empire Builder — opening planner</title>
<style>
:root{--bg:#101319;--card:#191d26;--line:#2a3040;--ink:#e9ebf0;--dim:#8d93a4;--accent:#6ea8ff;--good:#54c98a}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding-bottom:40px}
header{padding:14px 16px 10px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}
h1{font-size:17px;margin:0 0 12px;font-weight:600}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
label{font-size:13px;color:var(--dim)}
input[type=text]{background:#0c0e13;border:1px solid var(--line);color:var(--ink);border-radius:8px;
  padding:10px;font-size:17px;width:70px;text-align:center}
button{background:#2b3852;color:#fff;border:1px solid #3d4f74;border-radius:8px;padding:10px 14px;font-size:15px;cursor:pointer}
button:active{background:#37476a}
button.go{background:var(--accent);border-color:var(--accent);color:#0b1220;font-weight:600;flex:1}
button.sm{padding:6px 10px;font-size:13px}
select{background:#0c0e13;border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:9px;font-size:14px}
.circus{color:#ffca57;font-weight:600}
#map{width:100%;background:#0c0e13;border:1px solid var(--line);border-radius:12px;margin-bottom:12px;display:block}
.tag{display:inline-block;font-size:12px;color:var(--dim);margin-right:8px}
.seg{display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg div{padding:8px 12px;font-size:14px;color:var(--dim);cursor:pointer;background:#0c0e13}
.seg div.on{background:#2b3852;color:#fff}
main{padding:12px 16px}
.res{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:13px;margin-bottom:11px}
.hd{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:8px}
.cost{font-size:22px;font-weight:700}
.mv{font-size:14px;color:var(--dim)}
.leg{font-size:14px;padding:3px 0;border-top:1px solid var(--line)}
.leg b{color:var(--accent);font-weight:600}
.pay{color:var(--good)}
.note{color:var(--dim);font-size:13px;margin:8px 0 0}
#track{font-size:13px;color:var(--dim)}
.empty{color:var(--dim);padding:20px 0;text-align:center}
</style></head><body>
<header>
<h1>Empire Builder — opening planner</h1>
<div class="row">
  <label>cards</label>
  <input type="text" id="c1" inputmode="numeric" placeholder="1">
  <input type="text" id="c2" inputmode="numeric" placeholder="2">
  <input type="text" id="c3" inputmode="numeric" placeholder="3">
</div>
<div class="row">
  <label>train</label>
  <div class="seg" id="spd"><div data-v="9">9 moves</div><div data-v="12">12 moves</div></div>
  <div class="seg" id="lds"><div data-v="2">2 loads</div><div data-v="3">3 loads</div></div>
</div>
<div class="row">
  <label>circus</label>
  <select id="k0"></select><select id="k1"></select>
</div>
<div class="row">
  <label>rank by</label>
  <div class="seg" id="mode"><div data-v="build">cheapest</div><div data-v="perTurn">$/turn</div><div data-v="reach">expansion</div></div>
</div>
<div class="row">
  <label>start in</label><select id="start"></select>
</div>
<div class="row">
  <button class="go" id="go">Plan</button>
  <button class="sm" id="clr">Clear track</button>
</div>
<div id="track"></div>
</header>
<svg id="map" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet"></svg>
<main id="out"><div class="empty">Enter your three card numbers and tap Plan.</div></main>
<script>
const G=__G__, CARDS=__C__, CITIES=__CI__;
__CORE__
const core=makeCore(G,CARDS,CITIES);
let owned=new Set(), speed=9, loads=2, circus=['tampa','tampa'], mode='build', startKey='';
try{ const s=localStorage.getItem('eb_track'); if(s) owned=new Set(JSON.parse(s));
     const t=localStorage.getItem('eb_train'); if(t){const o=JSON.parse(t);speed=o.s;loads=o.l;}
     const k=localStorage.getItem('eb_circus'); if(k) circus=JSON.parse(k);
     const m=localStorage.getItem('eb_mode'); if(m) mode=m;
     const st=localStorage.getItem('eb_start'); if(st!==null) startKey=st; }catch(e){}
function saveTrack(){ try{ localStorage.setItem('eb_track',JSON.stringify([...owned])); }catch(e){} }
function saveTrain(){ try{ localStorage.setItem('eb_train',JSON.stringify({s:speed,l:loads})); }catch(e){} }
function seg(id,val,set){ const el=document.getElementById(id);
  [...el.children].forEach(d=>{ d.classList.toggle('on', +d.dataset.v===val());
    d.onclick=()=>{ set(+d.dataset.v); saveTrain(); seg(id,val,set); }; }); }
seg('spd',()=>speed,v=>speed=v); seg('lds',()=>loads,v=>loads=v);
(function(){ const el=document.getElementById('mode');
  const paint=()=>[...el.children].forEach(d=>{ d.classList.toggle('on',d.dataset.v===mode);
    d.onclick=()=>{ mode=d.dataset.v; try{localStorage.setItem('eb_mode',mode);}catch(e){} paint(); render(); }; });
  paint(); })();
const sorted=[...CITIES].sort((a,b)=>a.name.localeCompare(b.name));
[0,1].forEach(i=>{ const el=document.getElementById('k'+i);
  el.innerHTML=sorted.map(c=>`<option value="${c.key}">${c.name}</option>`).join('');
  el.value=circus[i]||'tampa';
  el.onchange=()=>{ circus[i]=el.value; try{localStorage.setItem('eb_circus',JSON.stringify(circus));}catch(e){} }; });
(function(){ const el=document.getElementById('start');
  const sorted=[...CITIES].sort((a,b)=>a.name.localeCompare(b.name));
  el.innerHTML='<option value="">anywhere</option>'+sorted.map(c=>`<option value="${c.key}">${c.name}</option>`).join('');
  el.value=startKey;
  el.onchange=()=>{ startKey=el.value; try{localStorage.setItem('eb_start',startKey);}catch(e){} }; })();

// --- rough map of what you have built ---
const XY=G.cells.map(([a,b])=>[a*0.8660+0, a*0.5+b]);
const XS=XY.map(p=>p[0]), YS=XY.map(p=>p[1]);
const X0=Math.min(...XS),X1=Math.max(...XS),Y0=Math.min(...YS),Y1=Math.max(...YS);
const W=100, H=Math.round(100*(Y1-Y0)/(X1-X0));
function px(i){ return [ (XY[i][0]-X0)/(X1-X0)*W, (XY[i][1]-Y0)/(Y1-Y0)*H ]; }
function drawMap(){
  const svg=document.getElementById('map');
  svg.setAttribute('viewBox','-2 -2 '+(W+4)+' '+(H+4));
  let s='';
  for(const k in core.CITY){ const [x,y]=px(core.CITY[k]);
    s+=`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="0.7" fill="#394054"/>`; }
  for(const e of owned){ const [u,v]=e.split('_').map(Number);
    const A=px(u),B=px(v);
    s+=`<line x1="${A[0].toFixed(1)}" y1="${A[1].toFixed(1)}" x2="${B[0].toFixed(1)}" y2="${B[1].toFixed(1)}" stroke="#6ea8ff" stroke-width="0.8" stroke-linecap="round"/>`; }
  for(const k in core.CITY){ const n=CITIES.find(c=>c.key===k);
    if(n&&n.type!=='small'){ const [x,y]=px(core.CITY[k]);
      s+=`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${n.type==='major'?1.8:1.1}" fill="${n.type==='major'?'#ff5f5f':'#8d93a4'}"/>`; } }
  svg.innerHTML=s;
}
function trackLine(){ document.getElementById('track').textContent =
  owned.size ? owned.size+' segments of track already built (counted as free)' : 'no track built yet';
  drawMap(); }
trackLine();
document.getElementById('clr').onclick=()=>{ owned=new Set(); saveTrack(); trackLine(); };
document.getElementById('go').onclick=()=>{
  const hand=['c1','c2','c3'].map(i=>document.getElementById(i).value.trim()).filter(Boolean);
  const bad=hand.filter(h=>!CARDS[h]);
  const out=document.getElementById('out');
  if(bad.length){ out.innerHTML='<div class="empty">No such card: '+bad.join(', ')+'</div>'; return; }
  if(hand.length<loads){ out.innerHTML='<div class="empty">Need at least '+loads+' cards for a '+loads+'-load train.</div>'; return; }
  out.innerHTML='<div class="empty">Working…</div>';
  setTimeout(()=>{
    const t0=Date.now();
    LAST=core.plan(hand,loads,speed,owned,10,circus,startKey||null);
    render(Date.now()-t0);
  },30);
};
let LAST=null;
function render(ms){
  const out=document.getElementById('out');
  if(!LAST) return;
  const res=core.sortBy(LAST,mode);
  if(!res.length){ out.innerHTML='<div class="empty">No legal combination found.</div>'; return; }
  out.innerHTML=res.map((r,i)=>`<div class="res">
      <div class="hd"><span class="cost">$${r.build}M</span>
        <span class="mv">${r.moves} moves · ${r.turns} turn${r.turns===1?'':'s'} · pays <span class="pay">$${r.payout}M</span></span></div>
      <div><span class="tag">$${r.perTurn}M/turn</span><span class="tag">expansion ${r.reach}</span>${r.newCities.length?`<span class="tag">opens ${r.newCities.slice(0,4).join(', ')}${r.newCities.length>4?'…':''}</span>`:''}</div>
      ${r.legs.map(l=>`<div class="leg">card <b>${l.card}</b> · <span class="${l.circus?'circus':''}">${l.load}</span>: ${l.from} &rarr; ${l.to} <span class="pay">$${l.pay}M</span></div>`).join('')}
      <div class="row" style="margin:10px 0 0"><button class="sm" data-i="${i}">Mark this track as built</button></div>
    </div>`).join('')+`<div class="note">${res.length} options${ms?' · '+(ms/1000).toFixed(1)+'s':''} · ranked by ${({build:'cheapest build',perTurn:'profit per turn',reach:'expansion value'})[mode]}</div>`;
    out.querySelectorAll('button[data-i]').forEach(b=>b.onclick=()=>{
      const r=res[+b.dataset.i], s=new Set(r.nodes);
      for(const [u,v] of G.edges.map(e=>[e[0],e[1]])) if(s.has(u)&&s.has(v)) owned.add(core.ekey(u,v));
      saveTrack(); trackLine(); b.textContent='added'; b.disabled=true;
    });
}
</script></body></html>"""
HTML=HTML.replace('__CORE__',CORE).replace('__G__',G).replace('__C__',C).replace('__CI__',CI)
open('/mnt/user-data/outputs/eb_planner.html','w').write(HTML)
import os;print(round(os.path.getsize('/mnt/user-data/outputs/eb_planner.html')/1024),'KB')
