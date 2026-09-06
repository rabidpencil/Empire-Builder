import pickle,numpy as np,json,itertools
D=pickle.load(open('D.pkl','rb'))
NAMES=['NorthWest','NorthCentral','NorthEast','SouthWest','SouthCentral','SouthEast']
NB=[(1,0),(-1,0),(0,1),(0,-1),(1,-1),(-1,1)]
S={}
for n in NAMES:
    S[n]={(c['a'],c['b']) for c in D[n]['cells'] if c.get('board')}
off=json.load(open('offsets.json'))
T={'NorthWest':(0,0)}
chain=[('NorthWest','NorthCentral'),('NorthCentral','NorthEast'),
       ('NorthWest','SouthWest'),('SouthWest','SouthCentral'),('SouthCentral','SouthEast')]
for a,b in chain:
    ta=T[a]; d=off[f'{a}|{b}']; T[b]=(ta[0]+d[0],ta[1]+d[1])
def placed(T):
    return {n:{(a+T[n][0],b+T[n][1]) for a,b in S[n]} for n in NAMES}
def score(T):
    P=placed(T); ov=0; ct=0
    keys=list(P)
    for i in range(len(keys)):
        for j in range(i+1,len(keys)):
            A,B=P[keys[i]],P[keys[j]]
            ov+=len(A&B)
            ct+=sum(1 for c in A for d in NB if (c[0]+d[0],c[1]+d[1]) in B)
    return ct-8*ov, ct, ov
best=score(T)
print('start',best)
improved=True
while improved:
    improved=False
    for n in NAMES[1:]:
        for da,db in itertools.product(range(-4,5),repeat=2):
            if da==0 and db==0: continue
            T2=dict(T); T2[n]=(T[n][0]+da,T[n][1]+db)
            s=score(T2)
            if s[0]>best[0]: T,best,improved=T2,s,True
# Pin the global frame to a fixed physical landmark (the Phoenix city marker on
# SouthWest = (1,16)). Per-piece lattice origins are arbitrary and can shift when
# the masks change, which would silently invalidate coordinates already exported.
import numpy as _np
_K=_np.array(json.load(open('K.json'))['SouthWest']['K'])
_d=json.load(open('SouthWest.json'))
_anchor=min((c for c in _d['cells'] if c['cls']=='city'),
            key=lambda c:(c['x']-2830)**2+(c['y']-838)**2)
_ab=_K@_np.array([_anchor['i'],_anchor['j']])
_cur=(_ab[0]+T['SouthWest'][0], _ab[1]+T['SouthWest'][1])
_sh=(1-_cur[0], 16-_cur[1])
T={n:(t[0]+int(_sh[0]),t[1]+int(_sh[1])) for n,t in T.items()}
print('anchor shift',_sh)
print('final',best,T)
json.dump({n:list(T[n]) for n in NAMES},open('placement.json','w'))
