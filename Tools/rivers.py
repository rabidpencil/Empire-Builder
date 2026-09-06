import json,cv2,numpy as np,collections
import masks2 as M
PIECES=[('NorthWest','163813399'),('NorthCentral','163839438'),('NorthEast','170428058'),
        ('SouthWest','163825427'),('SouthCentral','163854400'),('SouthEast','170106074')]
K={n:np.array(v['K']) for n,v in json.load(open('K.json')).items()}
T=json.load(open('placement.json'))
NB=[(1,0),(0,1),(1,-1)]           # three directions cover every edge once
board={(c['a'],c['b']):c for c in json.load(open('eb-board-mileposts.json'))['cells']}
NODE={k for k,c in board.items() if c['cls'] in ('clear','mtn','city')}
edges=collections.defaultdict(list)
for name,fn in PIECES:
    im=cv2.imread(f'/mnt/user-data/uploads/PXL_20260905_{fn}.jpg')
    wat=M.water_mask(im); bd=M.board_mask(im)
    big=cv2.morphologyEx(wat,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(45,45)))
    riv=(wat&(1-cv2.dilate(big,np.ones((9,9),np.uint8)))&bd).astype(np.uint8)
    riv=cv2.morphologyEx(riv,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    d=json.load(open(name+'.json'))
    P={}
    for c in d['cells']:
        a,b=K[name]@np.array([c['i'],c['j']])
        P[(int(a+T[name][0]),int(b+T[name][1]))]=(c['x'],c['y'])
    # Topological test: cut the board along the rivers and see whether the two
    # mileposts land in different pieces. A run-length test along the segment
    # can't tell a crossing from a river running alongside the edge.
    cut=(bd&(1-cv2.dilate(riv,np.ones((5,5),np.uint8)))&(1-cv2.dilate(big,np.ones((5,5),np.uint8)))).astype(np.uint8)
    ncomp,comp=cv2.connectedComponents(cut,4)
    def lab(x,y):
        x,y=int(x),int(y)
        if not (0<=y<comp.shape[0] and 0<=x<comp.shape[1]): return 0
        if comp[y,x]: return comp[y,x]
        w=comp[max(y-14,0):y+15,max(x-14,0):x+15]
        w=w[w>0]
        return int(np.bincount(w).argmax()) if w.size else 0
    H,W=riv.shape
    okpt=lambda x,y: 0<=int(y)<bd.shape[0] and 0<=int(x)<bd.shape[1] and bd[int(y),int(x)]
    for k,(x0,y0) in P.items():
        if k not in NODE or not okpt(x0,y0): continue
        for dd in NB:
            k2=(k[0]+dd[0],k[1]+dd[1])
            if k2 not in P or k2 not in NODE: continue
            x1,y1=P[k2]
            if not okpt(x1,y1): continue
            n=64; hits=[]
            for t in np.linspace(0.12,0.88,n):
                x,y=int(x0+(x1-x0)*t),int(y0+(y1-y0)*t)
                if 0<=y<H and 0<=x<W: hits.append(riv[y,x])
                else: hits.append(0)
            hits=np.array(hits)
            if hits.sum()==0: continue
            # a genuine crossing is a short transverse run in the interior of the
            # segment; a river flowing alongside the edge gives a long run, and a
            # graze at a bend touches one end.
            runs=[];run=0
            for h in hits:
                if h: run+=1
                elif run: runs.append(run);run=0
            if run: runs.append(run)
            if hits[0] or hits[-1]: continue
            if hits.sum()>0.40*n: continue
            if max(runs)<3: continue
            edges[tuple(sorted([k,k2]))].append((name,int(max(runs))))
mine=set(edges)
print('river-crossing edges detected:',len(mine))
his=set()
for e in json.load(open('crossings_newframe.json'))['river_edges']:
    his.add(tuple(sorted([(e[0],e[1]),(e[2],e[3])])))
print('your tagged river edges:',len(his))
print('agree:',len(mine&his),'  only mine:',len(mine-his),'  only yours:',len(his-mine))
json.dump({'detected':[list(a)+list(b) for a,b in sorted(mine)],
           'agree':[list(a)+list(b) for a,b in sorted(mine&his)],
           'only_detected':[list(a)+list(b) for a,b in sorted(mine-his)],
           'only_tagged':[list(a)+list(b) for a,b in sorted(his-mine)]},open('rivers_compare.json','w'))
