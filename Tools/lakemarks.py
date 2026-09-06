import json,cv2,numpy as np,collections
import masks2 as M
def jac(sol,i,j):
    return np.array([0,1,0,2*i,0,j],float)@sol, np.array([0,0,1,0,2*j,i],float)@sol
def canon(name):
    d=json.load(open(name+'.json')); sol=np.array(d['sol'])
    ij=np.array([[c['i'],c['j']] for c in d['cells']],float); ci,cj=ij.mean(0)
    du,dv=jac(sol,ci,cj); cands={}
    for (p,q) in [(1,0),(0,1),(1,1),(1,-1),(-1,1),(-1,0),(0,-1),(-1,-1)]:
        v=p*du+q*dv
        if np.hypot(*v)>=0.5*np.hypot(*du): cands[(p,q)]=v
    def pick(t):
        best=None
        for k,v in cands.items():
            if v[1]<=0: continue
            a=np.degrees(np.arctan2(v[1],v[0])); e=abs(((a-t+180)%360)-180)
            if best is None or e<best[0]: best=(e,k)
        return best[1]
    Mt=np.column_stack([np.array(pick(30),float),np.array(pick(90),float)])
    K=np.round(np.linalg.inv(Mt)).astype(int)
    return d,K
board={(c['a'],c['b']):c for c in json.load(open('eb-board-mileposts.json'))['cells']}
NODE={k for k,c in board.items() if c['cls'] in ('clear','mtn','city')}
MT={k for k,c in board.items() if c['cls']=='mtn'}
out=[]
for name,fn in [('NCLake','Lake_Channel_NorthCentral.jpg'),('NELake','Lake_Channel_NorthEast.jpg')]:
    d,K=canon(name)
    cells={}
    for c in d['cells']:
        a,b=K@np.array([c['i'],c['j']]); cells[(int(a),int(b))]=c
    mine={k for k,c in cells.items() if c['cls']=='mtn'}
    best=None
    for da in range(-90,91):
        for db in range(-90,91):
            s=sum(1 for (a,b) in mine if (a+da,b+db) in MT)
            if best is None or s>best[0]: best=(s,da,db)
    s,da,db=best
    print(name,'alignment offset',(da,db),'matching mountains',s,'of',len(mine))
    im=cv2.imread('/mnt/user-data/uploads/'+fn); H,W=im.shape[:2]
    b_,g_,r_,mx=M.channels(im)
    red=((r_>120)&(r_-g_>60)&(r_-b_>60)).astype(np.uint8)
    thick=cv2.morphologyEx(red,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15)))
    thin=cv2.dilate((red&(1-thick)).astype(np.uint8),np.ones((7,7),np.uint8))
    NB=[(1,0),(0,1),(1,-1)]
    for (a,b),c in cells.items():
        g1=(a+da,b+db)
        if g1 not in NODE: continue
        for dd in NB:
            k2=(a+dd[0],b+dd[1]); g2=(g1[0]+dd[0],g1[1]+dd[1])
            if k2 not in cells or g2 not in NODE: continue
            x0,y0=c['x'],c['y']; x1,y1=cells[k2]['x'],cells[k2]['y']
            n=40; hit=0
            for t in np.linspace(0.15,0.85,n):
                x,y=int(x0+(x1-x0)*t),int(y0+(y1-y0)*t)
                if 0<=y<H and 0<=x<W and thin[y,x]: hit+=1
            if hit>=0.75*n:
                out.append(dict(piece=name,edge=[list(g1),list(g2)],hit=hit))
seen={}
for o in out: seen[tuple(sorted(map(tuple,o['edge'])))]=o
print('\nmarked crossings found:',len(seen))
for k in sorted(seen): print('  ',k)
json.dump([{'edge':[list(a),list(b)]} for a,b in sorted(seen)],open('lake_marks.json','w'),indent=1)
