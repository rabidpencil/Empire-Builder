import json
G=open('eb-plan-graph.json').read()
C=open('cards.json').read()
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
#map{width:100%;height:46vh;background:#0c0e13;border:1px solid var(--line);border-radius:12px;margin-bottom:12px;display:block}
.tag{display:inline-block;font-size:12px;color:var(--dim);margin-right:8px}
details{border:1px solid var(--line);border-radius:10px;margin-bottom:8px;background:#151922}
details>summary{list-style:none;cursor:pointer;padding:9px 12px;font-size:13px;color:var(--dim);
  display:flex;justify-content:space-between;align-items:center;gap:10px}
details>summary::-webkit-details-marker{display:none}
details>summary::after{content:'▾';color:var(--dim);font-size:12px}
details[open]>summary::after{content:'▴'}
details>summary b{color:var(--ink);font-weight:600}
details .row{margin:0 12px 10px}
details .row:first-of-type{margin-top:2px}
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
<details id="dSetup"><summary><span id="sumSetup">train &amp; options</span></summary>
<div class="row">
  <label>train</label>
  <div class="seg" id="spd"><div data-v="9">9 moves</div><div data-v="12">12 moves</div></div>
  <div class="seg" id="lds"><div data-v="2">2 loads</div><div data-v="3">3 loads</div></div>
</div>
<div class="row">
  <label>circus</label>
  <select id="k0"></select><select id="k1"></select>
</div>
</details>
<details id="dGame"><summary><span id="sumGame">game state</span></summary>
<div class="row">
  <label>cash</label><input type="text" id="cash" inputmode="numeric" placeholder="50">
  <label>turn</label><input type="text" id="turn" inputmode="numeric" placeholder="1">
  <label>pace</label>
  <div class="seg" id="pace"><div data-v="1.2">ahead</div><div data-v="1">even</div><div data-v="0.7">behind</div></div>
</div>
<div class="row">
  <label>delivered</label><select id="deliv"></select><button class="sm" id="adddeliv">+</button>
</div>
<div id="pending" class="note"></div>
<div class="row">
  <label>other $</label><input type="text" id="gain" inputmode="numeric" placeholder="0">
  <button class="sm" id="logturn">End turn</button>
  <button class="sm" id="undoturn">Undo turn</button>
</div>
</details>
<div id="vic" class="note"></div>
<details id="dPlan"><summary><span id="sumPlan">planning options</span></summary>
<div class="row">
  <label>routes</label>
  <div class="seg" id="rts"><div data-v="1">1</div><div data-v="2">2</div><div data-v="3">3</div></div>
</div>
<div class="row" id="holdrow">
  <label>aboard</label><select id="hold"></select><button class="sm" id="addhold">+</button>
</div>
<div id="held" class="note"></div>
<div class="row">
  <label>rank by</label>
  <div class="seg" id="mode"><div data-v="delta">turns saved</div><div data-v="build">cheapest</div><div data-v="moves">fewest moves</div><div data-v="perTurn">$/turn</div><div data-v="reach">expansion</div></div>
</div>
<div class="row">
  <label>start in</label><select id="start"></select>
</div>
</details>
<div class="row">
  <button class="go" id="go">Plan</button>
  <button class="sm" id="clr">Clear track</button>
  <button class="sm" id="resetall">Reset all</button>
</div>
<div id="track"></div>
</header>
<svg id="map" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet"></svg>
<details id="dTrack" style="margin:0 16px 8px"><summary><span id="sumTrack">add track by hand</span></summary>
<div class="row" style="padding:0 12px">
  <label>from</label><select id="ta"></select><select id="tb"></select>
  <button class="sm" id="addcheap">Add cheapest</button><button class="sm" id="addshort">Add shortest</button><button class="sm" id="undo">Undo</button>
</div>
<div id="tinfo" class="note" style="padding:0 12px 10px"></div></details>
<div id="mapdbg" class="note" style="padding:0 16px"></div>
<main id="out"><div class="empty">Enter your three card numbers and tap Plan.</div></main>
<script>
window.onerror=function(m,src,line,col){
  var o=document.getElementById('out');
  if(o) o.innerHTML='<div class="empty" style="color:#ff8a8a">script error: '+m+'<br>line '+line+'</div>';
};
const G=__G__, CARDS=__C__, CITIES=__CI__;
__CORE__
const core=makeCore(G,CARDS,CITIES);
let owned=new Set(), speed=9, loads=2, circus=['tampa','tampa'], mode='build', startKey='';
let routes=2, carrying=[], undoStack=[];
let cash=50, turn=1, pace=1, log=[], pending=[];   // log: [{turn,gain,delivered}]
try{ const s=localStorage.getItem('eb_track'); if(s) owned=new Set(JSON.parse(s));
     const t=localStorage.getItem('eb_train'); if(t){const o=JSON.parse(t);speed=o.s;loads=o.l;}
     const k=localStorage.getItem('eb_circus'); if(k) circus=JSON.parse(k);
     const m=localStorage.getItem('eb_mode'); if(m) mode=m;
     const st=localStorage.getItem('eb_start'); if(st!==null) startKey=st;
     const rt=localStorage.getItem('eb_routes'); if(rt) routes=+rt;
     const cy=localStorage.getItem('eb_carry'); if(cy) carrying=JSON.parse(cy);
     const gm=localStorage.getItem('eb_game'); if(gm){const o=JSON.parse(gm);cash=o.cash;turn=o.turn;pace=o.pace;log=o.log||[];pending=o.pending||[];} }catch(e){}
function saveTrack(){ try{ localStorage.setItem('eb_track',JSON.stringify([...owned])); }catch(e){} }
function saveTrain(){ try{ localStorage.setItem('eb_train',JSON.stringify({s:speed,l:loads})); }catch(e){} }
function seg(id,val,set){ const el=document.getElementById(id);
  [...el.children].forEach(d=>{ d.classList.toggle('on', +d.dataset.v===val());
    d.onclick=()=>{ set(+d.dataset.v); saveTrain(); seg(id,val,set); }; }); }
seg('spd',()=>speed,v=>{speed=v; summaries();});
seg('lds',()=>loads,v=>{loads=v; if(routes>loads){routes=loads;} drawRoutes();});
function drawRoutes(){ const el=document.getElementById('rts');
  [...el.children].forEach(d=>{ const v=+d.dataset.v;
    d.style.display=v<=loads?'':'none';
    d.classList.toggle('on',v===routes);
    d.onclick=()=>{ routes=v; try{localStorage.setItem('eb_routes',routes);}catch(e){} drawRoutes(); summaries(); }; }); }
drawRoutes();
function hand(){ return ['c1','c2','c3'].map(i=>document.getElementById(i).value.trim()).filter(Boolean); }
function saveCarry(){ try{localStorage.setItem('eb_carry',JSON.stringify(carrying));}catch(e){} }
function drawHold(){
  carrying=carrying.filter(h=>CARDS[h.card]&&CARDS[h.card][h.idx]);
  const sel=document.getElementById('hold'); const opts=[];
  for(const c of hand()){ const ds=CARDS[c]||[];
    ds.forEach((d,i)=>opts.push(`<option value="${c}:${i}">card ${c} · ${d.load} &rarr; ${d.city}</option>`)); }
  sel.innerHTML=opts.join('')||'<option value="">enter cards first</option>';
  document.getElementById('held').innerHTML = carrying.length
    ? 'aboard: '+carrying.map((h,i)=>`${CARDS[h.card][h.idx].load} &rarr; ${CARDS[h.card][h.idx].city} <a href="#" data-h="${i}">&times;</a>`).join(' · ')
    : '';
  document.querySelectorAll('#held a').forEach(a=>a.onclick=e=>{e.preventDefault();carrying.splice(+a.dataset.h,1);saveCarry();drawHold();});
}
document.getElementById('addhold').onclick=()=>{ const v=document.getElementById('hold').value;
  if(!v) return; const [card,idx]=v.split(':');
  if(carrying.length>=loads) return;
  carrying.push({card,idx:+idx}); saveCarry(); drawHold(); summaries(); };
['c1','c2','c3'].forEach(i=>document.getElementById(i).addEventListener('input',()=>{drawHold();drawDeliv();}));
(function(){ const el=document.getElementById('mode');
  const paint=()=>[...el.children].forEach(d=>{ d.classList.toggle('on',d.dataset.v===mode);
    d.onclick=()=>{ mode=d.dataset.v; try{localStorage.setItem('eb_mode',mode);}catch(e){} paint(); summaries(); render(); }; });
  paint(); })();
const sorted=[...CITIES].sort((a,b)=>a.name.localeCompare(b.name));
[0,1].forEach(i=>{ const el=document.getElementById('k'+i);
  el.innerHTML='<option value="aboard">on my train</option><option value="taken">another player</option>'
    +sorted.map(c=>`<option value="${c.key}">${c.name}</option>`).join('');
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
  const dbg=document.getElementById('mapdbg');
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
  if(dbg) dbg.textContent='map: '+Object.keys(core.CITY).length+' cities, '+owned.size
    +' track segments, viewBox '+svg.getAttribute('viewBox')+', '+s.length+' chars drawn';
}
(function(){ const sorted=[...CITIES].sort((a,b)=>a.name.localeCompare(b.name));
  const o=sorted.map(c=>`<option value="${c.key}">${c.name}</option>`).join('');
  document.getElementById('ta').innerHTML=o; document.getElementById('tb').innerHTML=o;
  const preview=()=>{
    const a=document.getElementById('ta').value,b=document.getElementById('tb').value;
    const info=document.getElementById('tinfo');
    if(a===b){ info.textContent=''; return; }
    const c=core.connect(a,b,owned,false), f=core.connect(a,b,owned,true);
    if(!c||!f){ info.textContent='no route'; return; }
    info.innerHTML=`cheapest <b>$${c.cost}M</b> / ${c.moves} moves &nbsp;&middot;&nbsp; shortest <b>$${f.cost}M</b> / ${f.moves} moves`
      +(f.moves<c.moves?` &rarr; $${f.cost-c.cost}M buys ${c.moves-f.moves} fewer moves`:'');
  };
  document.getElementById('ta').onchange=preview;
  document.getElementById('tb').onchange=preview;
  const addIt=short=>()=>{
    const a=document.getElementById('ta').value,b=document.getElementById('tb').value;
    if(a===b) return;
    const r=core.connect(a,b,owned,short);
    if(!r) return;
    undoStack.push(new Set(owned));
    r.edges.forEach(e=>owned.add(e));
    document.getElementById('tinfo').innerHTML=`added ${core.NAME[a]} &rarr; ${core.NAME[b]}: <b>$${r.cost}M</b>, ${r.newSegments} new segments, ${r.moves} moves`;
    saveTrack(); trackLine(); drawHold(); vicLine(); };
  document.getElementById('addcheap').onclick=addIt(false);
  document.getElementById('addshort').onclick=addIt(true);
  document.getElementById('undo').onclick=()=>{ if(!undoStack.length) return;
    owned=undoStack.pop(); saveTrack(); trackLine();
    document.getElementById('tinfo').textContent='undone'; }; })();

['dSetup','dGame','dPlan','dTrack'].forEach(id=>{ const d=document.getElementById(id);
  if(!d) return;
  try{ d.open = localStorage.getItem('eb_'+id)==='1'; }catch(e){}
  d.addEventListener('toggle',()=>{ try{localStorage.setItem('eb_'+id,d.open?'1':'0');}catch(e){} }); });
function summaries(){
  const set=(id,html)=>{ const e=document.getElementById(id); if(e) e.innerHTML=html; };
  const cn=k=>k==='aboard'?'aboard':k==='taken'?'taken':(core.NAME[k]||'?');
  set('sumSetup',`train <b>${speed} moves / ${loads} loads</b> · circus ${cn(circus[0])}, ${cn(circus[1])}`);
  set('sumGame',`<b>$${cash}M</b> · turn ${turn} · ${({1.2:'ahead',1:'even',0.7:'behind'})[pace]||''}`);
  set('sumPlan',`<b>${routes} route${routes===1?'':'s'}</b> · by ${({delta:'turns saved',build:'cheapest',moves:'fewest moves',perTurn:'$/turn',reach:'expansion'})[mode]}`
    +(startKey?` · from ${core.NAME[startKey]}`:'')+(carrying.length?` · ${carrying.length} aboard`:''));
  set('sumTrack',`add track by hand · <b>${owned.size}</b> segments built`);
}
function saveGame(){ try{localStorage.setItem('eb_game',JSON.stringify({cash,turn,pace,log,pending}));}catch(e){} }
// every demand on the cards in hand, plus a circus run for any card that is a
// multiple of 5, as things you can tick off as delivered
function deliverables(){
  const out=[];
  for(const c of hand()){ const ds=CARDS[c]||[];
    ds.forEach((d,i)=>out.push({card:c,idx:i,load:d.load,city:d.city,pay:d.payout}));
    if(Number(c)%5===0 && ds.length){
      let lo=ds[0]; for(const d of ds) if(d.payout<lo.payout) lo=d;
      out.push({card:c,idx:-1,load:'circus',city:lo.city,pay:20});
    } }
  return out;
}
function drawDeliv(){
  const sel=document.getElementById('deliv'); if(!sel) return;
  const ds=deliverables();
  sel.innerHTML = ds.length
    ? ds.map((d,i)=>`<option value="${i}">card ${d.card} · ${d.load} &rarr; ${d.city} $${d.pay}M</option>`).join('')
    : '<option value="">enter cards first</option>';
  const p=document.getElementById('pending');
  const tot=pending.reduce((s,x)=>s+x.pay,0);
  p.innerHTML = pending.length
    ? pending.map((x,i)=>`${x.load} &rarr; ${x.city} <b>$${x.pay}M</b> <a href="#" data-p="${i}">&times;</a>`).join(' · ')
      +` &nbsp;= <b>$${tot}M</b> this turn`
    : '';
  document.querySelectorAll('#pending a').forEach(a=>a.onclick=e=>{
    e.preventDefault(); pending.splice(+a.dataset.p,1); saveGame(); drawDeliv(); });
}
// income rate from the turns you've logged: median-ish, plus the best and worst
// of the recent window so the estimate can be shown as a range rather than a
// number it hasn't earned.
function rates(){
  const w=log.slice(-6).map(x=>x.gain);
  if(!w.length) return null;
  const avg=w.reduce((a,b)=>a+b,0)/w.length;
  return {avg, lo:Math.min(...w), hi:Math.max(...w)};
}
function turnsLeft(r){ if(!r||r<=0) return null; return (250-cash)/r*pace; }
function vicLine(){
  const el=document.getElementById('vic'); const r=rates();
  if(!r){ el.textContent='log a few turns and a turns-to-win estimate appears here'; return; }
  const a=turnsLeft(r.avg), lo=turnsLeft(r.hi), hi=turnsLeft(r.lo);
  el.innerHTML=`$${cash}M · turn ${turn} · earning ~$${r.avg.toFixed(0)}M/turn `
    +`&rarr; <b>${Math.max(0,Math.round(a))} turns to $250M</b> (range ${Math.max(0,Math.round(lo))}–${Math.max(0,Math.round(hi))})`;
}
['cash','turn'].forEach(id=>{ const el=document.getElementById(id);
  el.value=(id==='cash'?cash:turn);
  el.addEventListener('input',()=>{ const v=parseInt(el.value||'0',10);
    if(id==='cash') cash=v; else turn=v; saveGame(); vicLine(); summaries(); }); });
(function(){ const el=document.getElementById('pace');
  const paint=()=>[...el.children].forEach(d=>{ d.classList.toggle('on',+d.dataset.v===pace);
    d.onclick=()=>{ pace=+d.dataset.v; saveGame(); paint(); vicLine(); summaries(); if(LAST) render(); }; });
  paint(); })();
document.getElementById('adddeliv').onclick=()=>{
  const sel=document.getElementById('deliv'); if(sel.value==='') return;
  const d=deliverables()[+sel.value]; if(!d) return;
  if(pending.some(p=>p.card===d.card)) return;   // one route per card
  pending.push(d); saveGame(); drawDeliv(); };
document.getElementById('logturn').onclick=()=>{
  const g=document.getElementById('gain');
  const other=parseInt(g.value||'0',10)||0;
  const gain=pending.reduce((s,x)=>s+x.pay,0)+other;
  const delivered=pending.slice();
  log.push({turn,gain,delivered}); cash+=gain; turn+=1; g.value='';
  // a delivered circus chip now lives in the city it was taken to
  for(const d of delivered) if(d.idx===-1){
    const k=core.norm(d.city);
    let i=circus.indexOf('aboard'); if(i<0) i=circus.findIndex(x=>x!=='taken');
    if(i>=0){ circus[i]=k; const el=document.getElementById('k'+i); if(el) el.value=k; }
    try{localStorage.setItem('eb_circus',JSON.stringify(circus));}catch(e){}
  }
  // spent cards leave the hand, and anything aboard that just got dropped is gone
  const spent=new Set(delivered.map(d=>d.card));
  ['c1','c2','c3'].forEach(id=>{ const el=document.getElementById(id);
    if(spent.has(el.value.trim())) el.value=''; });
  carrying=carrying.filter(h=>!delivered.some(d=>d.card===h.card&&d.idx===h.idx));
  pending=[]; saveCarry();
  document.getElementById('cash').value=cash; document.getElementById('turn').value=turn;
  saveGame(); vicLine(); summaries(); drawHold(); drawDeliv(); LAST=null;
  document.getElementById('out').innerHTML='<div class="empty">turn '+turn+' — enter your new card and tap Plan.</div>'; };
document.getElementById('undoturn').onclick=()=>{
  const last=log.pop(); if(!last) return;
  cash-=last.gain; turn-=1; pending=last.delivered||[];
  document.getElementById('cash').value=cash; document.getElementById('turn').value=turn;
  saveGame(); vicLine(); summaries(); if(LAST) render(); };

function trackLine(){ document.getElementById('track').textContent =
  owned.size ? owned.size+' segments of track already built (counted as free)' : 'no track built yet';
  drawMap(); summaries(); }
try{ trackLine(); drawHold(); vicLine(); summaries(); drawDeliv(); }catch(e){ console.error(e); }
document.getElementById('resetall').onclick=()=>{
  if(!confirm('Reset track, game state, train and circus to defaults?')) return;
  try{ ['eb_track','eb_train','eb_circus','eb_mode','eb_start','eb_routes','eb_carry','eb_game',
        'eb_dSetup','eb_dGame','eb_dPlan','eb_dTrack'].forEach(k=>localStorage.removeItem(k)); }catch(e){}
  location.reload(); };
document.getElementById('clr').onclick=()=>{ owned=new Set(); saveTrack(); trackLine(); };
document.getElementById('go').onclick=()=>{
  const h=hand();
  const bad=h.filter(x=>!CARDS[x]);
  const out=document.getElementById('out');
  if(bad.length){ out.innerHTML='<div class="empty">No such card: '+bad.join(', ')+'</div>'; return; }
  if(h.length<routes){ out.innerHTML='<div class="empty">Need at least '+routes+' cards to plan '+routes+' routes.</div>'; return; }
  out.innerHTML='<div class="empty">Working…</div>';
  setTimeout(()=>{
    const t0=Date.now();
    LAST=core.plan(h,loads,speed,owned,10,circus,startKey||null,carrying,routes);
    render(Date.now()-t0);
  },30);
};
let LAST=null;
function render(ms){
  const out=document.getElementById('out');
  if(!LAST) return;
  const r0=rates();
  // fall back to what this hand itself implies if no turns are logged yet
  const R=(r0&&r0.avg>0)?r0.avg:(LAST.length?Math.max(1,LAST[0].perTurn):10);
  LAST.forEach(x=>{ x.deltaT = x.turns - (x.payout - x.build)/R; });
  const res=(mode==='delta')?LAST.slice().sort((a,b)=>a.deltaT-b.deltaT):core.sortBy(LAST,mode);
  if(!res.length){ out.innerHTML='<div class="empty">No legal combination found.</div>'; return; }
  out.innerHTML=res.map((r,i)=>`<div class="res">
      <div class="hd"><span class="cost">$${r.build}M</span>
        <span class="mv">${r.moves} moves · ${r.turns} turn${r.turns===1?'':'s'} · pays <span class="pay">$${r.payout}M</span></span></div>
      <div><span class="tag" style="color:${r.deltaT<0?'#54c98a':'#d98a8a'}">${r.deltaT<0?'':'+'}${r.deltaT.toFixed(1)} turns to win</span><span class="tag">$${r.perTurn}M/turn</span><span class="tag">expansion ${r.reach}</span>${r.fastMoves<r.moves?`<span class="tag">or $${r.fastBuild}M for ${r.fastMoves} moves (${r.fastTurns}t)</span>`:''}${r.newCities.length?`<span class="tag">opens ${r.newCities.slice(0,4).join(', ')}${r.newCities.length>4?'…':''}</span>`:''}</div>
      ${r.legs.map(l=>`<div class="leg">card <b>${l.card}</b> · <span class="${l.circus?'circus':''}">${l.load}${l.held?' (aboard)':''}</span>: ${l.from} &rarr; ${l.to} <span class="pay">$${l.pay}M</span></div>`).join('')}
      <div class="row" style="margin:10px 0 0"><button class="sm" data-i="${i}">Mark this track as built</button></div>
    </div>`).join('')+`<div class="note">${res.length} options${ms?' · '+(ms/1000).toFixed(1)+'s':''} · ranked by ${({delta:'turns saved',build:'cheapest build',moves:'fewest moves',perTurn:'profit per turn',reach:'expansion value'})[mode]}</div>`;
    out.querySelectorAll('button[data-i]').forEach(b=>b.onclick=()=>{
      const r=res[+b.dataset.i];
      undoStack.push(new Set(owned));
      r.edges.forEach(e=>owned.add(e));
      saveTrack(); trackLine(); b.textContent='added'; b.disabled=true;
    });
}
</script></body></html>"""
HTML=HTML.replace('__CORE__',CORE).replace('__G__',G).replace('__C__',C).replace('__CI__',CI)
open('/mnt/user-data/outputs/eb_planner.html','w').write(HTML)
import os;print(round(os.path.getsize('/mnt/user-data/outputs/eb_planner.html')/1024),'KB')
