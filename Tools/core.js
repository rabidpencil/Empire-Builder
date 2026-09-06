// ---- planning core: shared by the app and the node test ----
function makeCore(G, CARDS, CITIES){
  const N=G.cells.length, COST=G.cost;
  const adj=Array.from({length:N},()=>[]);
  const ekey=(u,v)=>u<v?u+'_'+v:v+'_'+u;
  for(const [u,v,s] of G.edges){ adj[u].push([v,s]); adj[v].push([u,s]); }
  const norm=s=>s.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'');
  const NAME={}, SRC={};
  for(const c of CITIES){ NAME[c.key]=c.name;
    for(const l of c.loads){ const k=l.toLowerCase(); (SRC[k]=SRC[k]||[]).push(c.key); } }
  const CITY=G.city;

  class PQ{ constructor(){this.a=[];}
    push(x){const a=this.a;a.push(x);let i=a.length-1;while(i>0){const p=(i-1)>>1;if(a[p][0]<=a[i][0])break;[a[p],a[i]]=[a[i],a[p]];i=p;}}
    pop(){const a=this.a,t=a[0],l=a.pop();if(a.length){a[0]=l;let i=0;for(;;){const x=2*i+1,y=x+1;let m=i;
      if(x<a.length&&a[x][0]<a[m][0])m=x; if(y<a.length&&a[y][0]<a[m][0])m=y; if(m===i)break;[a[m],a[i]]=[a[i],a[m]];i=m;}}return t;}
    get size(){return this.a.length;} }

  // build weight of entering v across edge (u,v): free if that track is already owned
  function w(u,v,s,owned){ return owned.has(ekey(u,v))?0:COST[v]+s; }

  function dijkstra(src,owned){
    const d=new Float64Array(N).fill(Infinity); d[src]=0;
    const pq=new PQ(); pq.push([0,src]);
    while(pq.size){ const [c,u]=pq.pop(); if(c>d[u])continue;
      for(const [v,s] of adj[u]){ const nc=c+w(u,v,s,owned); if(nc<d[v]){d[v]=nc;pq.push([nc,v]);} } }
    return d;
  }

  function steiner(terms,owned){
    const t=[...new Set(terms)], k=t.length;
    if(k===1) return {cost:0,nodes:new Set([t[0]])};
    const F=1<<k, dp=[], par=[];
    for(let m=0;m<F;m++){ dp.push(new Float64Array(N).fill(Infinity)); par.push(new Array(N).fill(null)); }
    t.forEach((v,i)=>dp[1<<i][v]=0);
    for(let m=1;m<F;m++){
      const row=dp[m];
      for(let sub=(m-1)&m; sub; sub=(sub-1)&m){ const o=m^sub; if(sub>o)continue;
        const a=dp[sub],b=dp[o];
        for(let v=0;v<N;v++){ const s=a[v]+b[v]; if(s<row[v]){row[v]=s;par[m][v]=['m',sub,o];} } }
      const pq=new PQ();
      for(let v=0;v<N;v++) if(row[v]<Infinity) pq.push([row[v],v]);
      while(pq.size){ const [c,u]=pq.pop(); if(c>row[u])continue;
        for(const [v,s] of adj[u]){ const nc=c+w(u,v,s,owned); if(nc<row[v]){row[v]=nc;par[m][v]=['e',u];pq.push([nc,v]);} } }
    }
    const full=F-1; let root=0;
    for(let v=1;v<N;v++) if(dp[full][v]<dp[full][root]) root=v;
    const nodes=new Set(), st=[[full,root]];
    while(st.length){ const [m,v]=st.pop(); nodes.add(v); const p=par[m][v];
      if(!p)continue; if(p[0]==='m'){st.push([p[1],v]);st.push([p[2],v]);} else st.push([m,p[1]]); }
    return {cost:dp[full][root],nodes};
  }

  function tourMoves(nodes,stops,owned){
    const sub=new Set(nodes);
    for(const e of owned){ const [a,b]=e.split('_').map(Number); sub.add(a); sub.add(b); }
    const bfs=s=>{ const d=new Map([[s,0]]); const q=[s];
      for(let i=0;i<q.length;i++){ const u=q[i];
        for(const [v] of adj[u]) if(sub.has(v)&&!d.has(v)&&(nodes.has(v)||owned.has(ekey(u,v)))){ d.set(v,d.get(u)+1); q.push(v); } }
      return d; };
    const D=new Map(); for(const s of new Set(stops)) D.set(s,bfs(s));
    const n=stops.length; let best=Infinity;
    const perm=(arr,cur)=>{ if(!arr.length){
        const pos=new Map(cur.map((x,i)=>[x,i]));
        for(let j=0;j*2+1<n;j++) if(pos.get(j*2)>pos.get(j*2+1)) return;
        let tot=0; for(let i=0;i+1<cur.length;i++){ const d=D.get(stops[cur[i]]); const v=d.get(stops[cur[i+1]]);
          if(v===undefined) return; tot+=v; }
        if(tot<best) best=tot; return; }
      for(let i=0;i<arr.length;i++) perm(arr.filter((_,j)=>j!==i),cur.concat(arr[i])); };
    perm([...Array(n).keys()],[]);
    return best;
  }

  function plan(hand,loads,speed,owned,topn){
    owned=owned||new Set();
    const CD={}; for(const k in CITY) CD[k]=dijkstra(CITY[k],owned);
    const combos=[];
    const pick=(idx,chosen)=>{ if(chosen.length===loads){ combos.push(chosen.slice()); return; }
      for(let i=idx;i<hand.length;i++) for(const d of (CARDS[hand[i]]||[]))
        pick(i+1,chosen.concat([{card:hand[i],d}])); };
    pick(0,[]);
    const cand=[];
    for(const combo of combos){
      const srcLists=combo.map(c=>SRC[c.d.load.toLowerCase()]||[]);
      const walk=(i,acc)=>{ if(i===srcLists.length){
          const terms=[]; combo.forEach((c,j)=>{ terms.push(acc[j]); terms.push(norm(c.d.city)); });
          const uniq=[...new Set(terms)];
          let bound=0; const inn=new Set([uniq[0]]);
          while(inn.size<uniq.length){ let bd=Infinity,bn=null;
            for(const x of inn) for(const y of uniq) if(!inn.has(y)){ const v=CD[x][CITY[y]]; if(v<bd){bd=v;bn=y;} }
            bound+=bd; inn.add(bn); }
          cand.push({bound,combo,srcs:acc.slice(),terms});
          return; }
        for(const s of srcLists[i]) walk(i+1,acc.concat([s])); };
      walk(0,[]);
    }
    cand.sort((a,b)=>a.bound-b.bound);
    const out=[];
    for(const c of cand.slice(0,topn||8)){
      const tn=c.terms.map(k=>CITY[k]);
      const {cost,nodes}=steiner(tn,owned);
      const stops=[]; c.combo.forEach((x,j)=>{ stops.push(CITY[c.srcs[j]]); stops.push(CITY[norm(x.d.city)]); });
      const mv=tourMoves(nodes,stops,owned);
      out.push({build:cost,moves:mv,turns:Math.ceil(mv/speed),
        payout:c.combo.reduce((s,x)=>s+x.d.payout,0),
        legs:c.combo.map((x,j)=>({card:x.card,load:x.d.load,from:NAME[c.srcs[j]],to:x.d.city,pay:x.d.payout})),
        nodes:[...nodes]});
    }
    out.sort((a,b)=>a.build-b.build || a.moves-b.moves);
    return out;
  }
  return {plan,NAME,CITY,ekey,norm};
}
if(typeof module!=='undefined') module.exports={makeCore};
