"""Opening planner: rank every legal 2-demand combination from a 3-card hand by
build cost and by movement."""
import json,heapq,itertools,collections,math,time,unicodedata
G=json.load(open('eb-plan-graph.json'))
CELLS=G['cells']; COST=G['cost']; CITY=G['city']
N=len(CELLS)
adj=[[] for _ in range(N)]
for u,v,s in G['edges']:
    adj[u].append((v,COST[v]+s,1))     # (to, build cost, movement)
    adj[v].append((u,COST[u]+s,1))
cards=json.load(open('/mnt/user-data/uploads/eb-demand-cards.json'))
cities=json.load(open('eb-cities-verified.json'))['cities']
def key(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return ''.join(ch for ch in s if ch.isalnum())
NAME={c['key']:c['name'] for c in cities}
SRC=collections.defaultdict(list)
for c in cities:
    for l in c['loads']: SRC[l.lower()].append(c['key'])

def dijkstra(src,w=1):
    d=[math.inf]*N; d[src]=0; pq=[(0,src)]
    while pq:
        c,u=heapq.heappop(pq)
        if c>d[u]: continue
        for v,bc,mv in adj[u]:
            nc=c+(bc if w==1 else mv)
            if nc<d[v]: d[v]=nc; heapq.heappush(pq,(nc,v))
    return d
CN=sorted(CITY); CD={k:dijkstra(CITY[k]) for k in CN}          # build distance
CM={k:dijkstra(CITY[k],0) for k in CN}                          # movement distance

def steiner(terms):
    """min build cost of a tree spanning terms; returns (cost, node set)"""
    t=list(dict.fromkeys(terms)); k=len(t)
    if k==1: return 0,{t[0]}
    INF=math.inf
    dp=[[INF]*N for _ in range(1<<k)]; par=[[None]*N for _ in range(1<<k)]
    for i,v in enumerate(t): dp[1<<i][v]=0
    for mask in range(1,1<<k):
        row=dp[mask]
        sub=(mask-1)&mask
        while sub:
            o=mask^sub
            if sub<o:
                a,b=dp[sub],dp[o]
                for v in range(N):
                    s=a[v]+b[v]
                    if s<row[v]: row[v]=s; par[mask][v]=('m',sub,o)
            sub=(sub-1)&mask
        pq=[(c,v) for v,c in enumerate(row) if c<INF]; heapq.heapify(pq)
        while pq:
            c,u=heapq.heappop(pq)
            if c>row[u]: continue
            for v,bc,mv in adj[u]:
                nc=c+bc
                if nc<row[v]: row[v]=nc; par[mask][v]=('e',u,None); heapq.heappush(pq,(nc,v))
    full=(1<<k)-1
    root=min(range(N),key=lambda v:dp[full][v])
    nodes=set(); st=[(full,root)]
    while st:
        mask,v=st.pop(); nodes.add(v)
        p=par[mask][v]
        if p is None: continue
        if p[0]=='m': st.append((p[1],v)); st.append((p[2],v))
        else: st.append((mask,p[1]))
    return dp[full][root],nodes

def tree_moves(nodes,stops):
    """fewest moves to visit stops in a legal order, travelling only inside the tree"""
    sub=set(nodes)
    idx={v:i for i,v in enumerate(sorted(sub))}
    m=len(idx); ad=[[] for _ in range(m)]
    for u in sub:
        for v,bc,mv in adj[u]:
            if v in sub: ad[idx[u]].append(idx[v])
    def bfs(s):
        d=[-1]*m; d[s]=0; q=collections.deque([s])
        while q:
            u=q.popleft()
            for v in ad[u]:
                if d[v]<0: d[v]=d[u]+1; q.append(v)
        return d
    D={s:bfs(idx[s]) for s in set(stops)}
    best=math.inf
    for order in itertools.permutations(range(len(stops))):
        seq=[stops[i] for i in order]
        if not legal(order,len(stops)): continue
        tot=sum(D[seq[i]][idx[seq[i+1]]] for i in range(len(seq)-1))
        if tot<best: best=tot
    return best
def legal(order,n):
    # stops are [p0,d0,p1,d1]; each pickup must precede its delivery
    pos={s:i for i,s in enumerate(order)}
    return all(pos[2*j]<pos[2*j+1] for j in range(n//2))

def plan(hand,speed=9,topn=15):
    cand=[]
    for A,B in itertools.combinations(hand,2):
        for da in cards[A]:
            for db in cards[B]:
                for sa in SRC[da['load'].lower()]:
                    for sb in SRC[db['load'].lower()]:
                        ta,tb=key(da['city']),key(db['city'])
                        terms=[sa,ta,sb,tb]
                        # MST lower bound on city-to-city build distance
                        u=list(dict.fromkeys(terms)); bound=0; inn={u[0]}
                        while len(inn)<len(u):
                            e=min((CD[x][CITY[y]],y) for x in inn for y in u if y not in inn)
                            bound+=e[0]; inn.add(e[1])
                        cand.append((bound,A,da,sa,B,db,sb,terms))
    cand.sort(key=lambda z:z[0])
    out=[]
    for bound,A,da,sa,B,db,sb,terms in cand[:topn]:
        c,nodes=steiner([CITY[x] for x in terms])
        stops=[CITY[sa],CITY[key(da['city'])],CITY[sb],CITY[key(db['city'])]]
        mv=tree_moves(nodes,stops)
        pay=da['payout']+db['payout']
        out.append(dict(cards=[A,B],
            demands=[f"{da['load']} {NAME[sa]}->{da['city']} ${da['payout']}M",
                     f"{db['load']} {NAME[sb]}->{db['city']} ${db['payout']}M"],
            build=c,payout=pay,net=pay-c,moves=mv,turns=math.ceil(mv/speed)))
    out.sort(key=lambda r:-r['net'])
    return out

if __name__=='__main__':
    hand=['1','37','82']
    t0=time.time(); res=plan(hand); dt=time.time()-t0
    print(f'hand {hand}   {dt:.1f}s\n')
    for r in res[:8]:
        print(f"  ${r['build']:>3}M build | pay ${r['payout']:>3}M | net ${r['net']:>4}M | {r['moves']:>3} moves ({r['turns']} turns)")
        for d in r['demands']: print('      ',d)
