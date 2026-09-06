"""Board graph for planning. Major-city hexagons are NOT contracted: their seven
cells are real spaces for movement, but building into them is free because the
track is pre-built."""
import json,collections
B={(c['a'],c['b']):c for c in json.load(open('eb-board-mileposts.json'))['cells']}
CIT={tuple(c['cell']):c for c in json.load(open('eb-cities-verified.json'))['cities']}
X=json.load(open('eb-crossings-verified.json'))
def S(l): return {tuple(sorted([(e[0],e[1]),(e[2],e[3])])) for e in l}
PLUS2,BLOCK=S(X['plus2']),S(X['impassable'])
NB=[(1,0),(-1,0),(0,1),(0,-1),(1,-1),(-1,1)]
NODES=[k for k,c in B.items() if c['cls'] in ('clear','mtn','city')]
IX={k:i for i,k in enumerate(NODES)}
def build_cost(k):
    c=B[k]
    if c.get('ctype')=='major': return 0          # pre-built track
    if c['cls']=='city': return 3
    return 2 if c['cls']=='mtn' else 1
cost=[build_cost(k) for k in NODES]
edges=[]
for k in NODES:
    for d in NB:
        k2=(k[0]+d[0],k[1]+d[1])
        if k2 not in IX or IX[k2]<IX[k]: continue
        key=tuple(sorted([k,k2]))
        if key in BLOCK: continue
        both_major = B[k].get('ctype')=='major' and B[k2].get('ctype')=='major'
        sur=0 if both_major else (2 if key in PLUS2 else 0)
        edges.append([IX[k],IX[k2],sur])
city_node={}
for k,c in CIT.items():
    if k in IX: city_node[c['key']]=IX[k]
# a major city is reachable at any of its seven cells
majorcells=collections.defaultdict(list)
for k,c in B.items():
    if c.get('ctype')=='major' and k in IX: majorcells[c['piece']].append(k)
json.dump(dict(cells=[list(k) for k in NODES],cost=cost,edges=edges,
               city=city_node,
               note='undirected edges [u,v,surcharge]. Building into a milepost costs cost[v] + surcharge; movement is 1 per milepost either way.'),
          open('eb-plan-graph.json','w'),separators=(',',':'))
print('nodes',len(NODES),'edges',len(edges),'cities mapped',len(city_node))
print('free (major) cells',sum(1 for c in cost if c==0))
