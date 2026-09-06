import cv2, numpy as np, json, sys, collections
from scipy.spatial import cKDTree
# ---------------- masks ----------------
def channels(im):
    b,g,r=[im[:,:,i].astype(np.int16) for i in range(3)]
    mx=np.maximum(np.maximum(b,g),r).astype(np.int16)
    return b,g,r,mx
def raw_ink(im,ratio=0.60,sigma=60):
    """illumination-normalised black-ink mask: dark relative to a smooth local
    background (robust to glare / white balance) and near-neutral in colour."""
    b,g,r,mx=channels(im); mn=np.minimum(np.minimum(b,g),r)
    gray=np.clip(mx,0,255).astype(np.uint8)
    # paper-white level: morphological closing removes dark symbols entirely
    # (kernel must exceed the largest symbol), then smooth.
    k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(101,101))
    illum=cv2.GaussianBlur(cv2.morphologyEx(gray,cv2.MORPH_CLOSE,k),(0,0),sigma).astype(np.float32)+1.0
    dark=(gray.astype(np.float32)/illum)<ratio
    neutral=(mx-mn)<75
    m=(dark&neutral).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    return cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))

def background(im,dil=13):
    """dark regions touching the image border = table/shadow, dilated"""
    ink=raw_ink(im); h,w=ink.shape
    n,lab,st,ce=cv2.connectedComponentsWithStats(ink,8)
    bg=np.zeros_like(ink)
    border=set(lab[0,:]) | set(lab[-1,:]) | set(lab[:,0]) | set(lab[:,-1])
    for i in border:
        if i==0: continue
        if st[i,4] > 0.002*h*w: bg[lab==i]=1
    return cv2.dilate(bg,np.ones((dil,dil),np.uint8),1) if dil>1 else bg
def board_mask(im,bg=None):
    """board silhouette = land | water | printed border, WB-robust"""
    b,g,r,mx=channels(im)
    land=land_mask(im)
    wat=water_mask(im)
    # city symbols are neither land- nor water-coloured; a hexagon clipped by a
    # die-cut edge is not enclosed, so without this the silhouette has a bite out
    # of it exactly where Los Angeles and Atlanta sit.
    red=((r>110)&(r-g>45)&(r-b>45)).astype(np.uint8)
    m=((land|wat|red)>0).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8),iterations=3)
    n,lab,st,ce=cv2.connectedComponentsWithStats(m,8)
    if n>1: m=(lab==(np.argmax(st[1:,4])+1)).astype(np.uint8)
    ff=m.copy(); h,w=m.shape; mm=np.zeros((h+2,w+2),np.uint8)
    cv2.floodFill(ff,mm,(0,0),1)
    return (m|(ff==0)).astype(np.uint8)

def ink_mask(im):
    return (raw_ink(im)*board_mask(im)).astype(np.uint8)
def water_mask(im):
    b,g,r,mx=channels(im)
    return (((b-r)>0.45*mx)&(mx>90)).astype(np.uint8)
def land_mask(im,bg=None):
    b,g,r,mx=channels(im)
    bg3=background(im,dil=3)
    p99=np.percentile(mx[::8,::8],99)
    cand=((mx>0.62*p99)&((b-r)<0.36*mx)&((r-b)<0.36*mx)&(bg3==0)).astype(np.uint8)
    cand=cv2.morphologyEx(cand,cv2.MORPH_CLOSE,np.ones((11,11),np.uint8),iterations=3)
    n,lab,st,ce=cv2.connectedComponentsWithStats(cand,8)
    h,w=cand.shape; keep=np.zeros(n,bool)
    edge=set(lab[0,:])|set(lab[-1,:])|set(lab[:,0])|set(lab[:,-1])
    big=[i for i in range(1,n) if st[i,4]>0.003*h*w]
    interior=[i for i in big if i not in edge]
    # A piece can run off the edge of the photo, so a land region touching the
    # image border is not automatically the table. Judge it by brightness against
    # the interior land instead: printed land matches, carpet and wood do not.
    ref=None
    if interior:
        j=max(interior,key=lambda i:st[i,4])
        ref=float(np.median(mx[lab==j]))
    for i in big:
        if i in interior: keep[i]=True
        elif ref is not None and abs(float(np.median(mx[lab==i]))-ref)<0.18*ref: keep[i]=True
    cand=keep[lab].astype(np.uint8)
    ff=cand.copy(); h,w=cand.shape; m=np.zeros((h+2,w+2),np.uint8)
    cv2.floodFill(ff,m,(0,0),1)
    return (cand|(ff==0)).astype(np.uint8)


# ---------------- blob shape ----------------
def shape_of(lab,i,st):
    x,y,w,h,a=st[i]
    comp=(lab[y:y+h,x:x+w]==i).astype(np.uint8)
    cnts,_=cv2.findContours(comp,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not cnts: return None
    c=max(cnts,key=cv2.contourArea); peri=cv2.arcLength(c,True)
    verts=len(cv2.approxPolyDP(c,0.06*peri,True))
    hull=cv2.contourArea(cv2.convexHull(c))
    (_,_),rad=cv2.minEnclosingCircle(c)
    circ=a/max(np.pi*rad*rad,1)          # 1.0 = disc, ~0.41 = equilateral triangle
    return dict(w=int(w),h=int(h),a=float(a),fill=a/(w*h),aspect=w/max(h,1),circ=float(circ),
                verts=verts,sol=cv2.contourArea(c)/max(hull,1))
def tri_like(s): return s and s['verts']==3 and s['sol']>0.88 and 0.38<s['fill']<0.74 and 0.72<s['aspect']<1.62
def dot_like(s): return s and s['sol']>0.85 and s['fill']>0.62 and 0.65<s['aspect']<1.52
def robust_med(v,lo=0.6,hi=1.7):
    v=np.asarray(v,float)
    if len(v)==0: return None
    m=np.median(v)
    for _ in range(4):
        sel=v[(v>lo*m)&(v<hi*m)]
        if len(sel)==0: break
        m=np.median(sel)
    return float(m)

# ---------------- lattice ----------------
def poly(ij,deg=2):
    ij=np.asarray(ij,float); i,j=ij[:,0],ij[:,1]
    cols=[np.ones(len(i)),i,j]
    if deg>=2: cols+=[i*i,j*j,i*j]
    return np.column_stack(cols)

def fit_lattice(P,name):
    """Incremental lattice growing: fit a small central patch first, then expand
    the radius, refitting as we go. A global fit over all seeds at once lets
    perspective drift snap correspondences onto the wrong cell, which is
    unrecoverable; growing outward keeps every new assignment close to a model
    that is already good where it is being extended."""
    t=cKDTree(P); d,idx=t.query(P,k=min(7,len(P)))
    V=np.array([P[j]-P[i] for i in range(len(P)) for j in idx[i][1:]])
    rr=np.hypot(V[:,0],V[:,1])
    sp=robust_med(rr[rr>20],0.75,1.3)
    keep=(rr>0.85*sp)&(rr<1.18*sp); V2=V[keep]
    ang=np.degrees(np.arctan2(V2[:,1],V2[:,0]))%180
    cand=[]
    for c in range(0,180,2):
        m=np.abs(((ang-c+90)%180)-90)<12
        if m.sum()<5: continue
        vv=V2[m].copy(); u=np.array([np.cos(np.radians(c)),np.sin(np.radians(c))])
        vv[(vv@u)<0]*=-1
        cand.append((int(m.sum()),c,vv.mean(0)))
    cand.sort(reverse=True,key=lambda z:z[0])
    base=[cand[0]]
    for c in cand[1:]:
        if all(min(abs(c[1]-b[1]),180-abs(c[1]-b[1]))>25 for b in base): base.append(c)
        if len(base)==2: break
    M=np.column_stack([base[0][2],base[1][2]]); Minv=np.linalg.inv(M)
    ctr=P[np.argmin(np.hypot(*(P-P.mean(0)).T))]
    R=5.0*sp; sol=None; ij=np.full((len(P),2),np.nan)
    inr=np.hypot(*(P-ctr).T)<R
    ij[inr]=np.round((Minv@(P[inr]-ctr).T).T)
    while True:
        ok=~np.isnan(ij[:,0])
        deg=2 if ok.sum()>=80 else 1
        sol,*_=np.linalg.lstsq(poly(ij[ok],deg),P[ok],rcond=None)
        if deg==1: sol=np.vstack([sol,np.zeros((3,2))])
        lo=np.nanmin(ij,0)-6; hi=np.nanmax(ij,0)+7
        G=np.array([(a,b) for a in np.arange(lo[0],hi[0]) for b in np.arange(lo[1],hi[1])],float)
        Pg=poly(G,deg)@(sol[:3] if deg==1 else sol)
        gt=cKDTree(Pg)
        R=min(R*1.5,1e9)
        sel=np.hypot(*(P-ctr).T)<R
        dd,kk=gt.query(P[sel])
        assign=np.where(dd<0.30*sp,kk,-1)
        newij=np.full((len(P),2),np.nan)
        newij[np.where(sel)[0][assign>=0]]=G[assign[assign>=0]]
        grew=(~np.isnan(newij[:,0])).sum()
        if grew>=8: ij=newij
        if R>2.2*np.hypot(*(P.max(0)-P.min(0))): break
    ok=~np.isnan(ij[:,0])
    sol,*_=np.linalg.lstsq(poly(ij[ok],2),P[ok],rcond=None)
    res=np.hypot(*(P[ok]-poly(ij[ok],2)@sol).T)
    return sol,ij[ok],sp,res

# ---------------- stage 2 ----------------
def templates(ink,cells,R):
    T={}
    for cls in ('clear','mtn'):
        acc=None;n=0
        for c in cells:
            if c['cls']!=cls: continue
            x,y=int(round(c['x'])),int(round(c['y']))
            p=ink[y-R:y+R+1,x-R:x+R+1]
            if p.shape!=(2*R+1,2*R+1): continue
            acc=p.astype(float) if acc is None else acc+p; n+=1
        T[cls]=((acc/max(n,1))>0.6).astype(np.uint8) if acc is not None else None
    return T
def cover(ink,T,x,y,R,rng=8,vis=None):
    """best template coverage over small shifts. vis restricts the template to the
    part of it that lies on the board, for symbols bisected by a die-cut edge."""
    if vis is not None:
        full=T.sum()
        T=(T&vis).astype(np.uint8)
        if T.sum()<0.35*full: return 0.0      # too little of the symbol on-board
    if T.sum()<40: return 0.0
    best=0.0
    for dy in range(-rng,rng+1):
        for dx in range(-rng,rng+1):
            p=ink[y+dy-R:y+dy+R+1,x+dx-R:x+dx+R+1]
            if p.shape!=T.shape: continue
            v=float((p&T).sum())/T.sum()
            if v>best: best=v
    return best
def leak_of(ink,x,y,sp):
    Ro=int(0.60*sp); p=ink[y-Ro:y+Ro+1,x-Ro:x+Ro+1]
    yy,xx=np.mgrid[-Ro:Ro+1,-Ro:Ro+1]; rr=np.hypot(xx,yy)
    ring=((rr>0.40*sp)&(rr<0.58*sp)).astype(np.uint8)
    if p.shape!=ring.shape: return 1.0
    return float((p&ring).sum())/ring.sum()

# ---------------- cities ----------------
def find_cities(im,sp,dot_med,exclude=None,board=None):
    b,g,r,mx=channels(im)
    red=((r>110)&(r-g>45)&(r-b>45)).astype(np.uint8)
    clipped=(1-cv2.erode(board,np.ones((31,31),np.uint8),1)).astype(bool) if board is not None \
            else np.zeros(red.shape,bool)
    if exclude is not None:
        x0,y0,x1,y1=exclude; red[y0:y1,x0:x1]=0
    # city symbols are solid and chunky; the orange load icons that often touch
    # them are thin. An opening at ~a tenth of the spacing separates the two.
    rr=max(3,int(0.10*sp))|1
    red=cv2.morphologyEx(red,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(rr,rr)))
    n,lab,st,ce=cv2.connectedComponentsWithStats(red,8)
    out=[]
    for i in range(1,n):
        w,h,a=st[i,2],st[i,3],st[i,4]
        if a<0.20*sp*sp*0.25: continue
        s=shape_of(lab,i,st)
        ar=w/max(h,1)
        edge = clipped[st[i,1]:st[i,1]+h, st[i,0]:st[i,0]+w].any()
        if s['sol']<0.85 and not edge: continue   # stars/emblems out; clipped hexagons kept
        if max(w,h)>1.35*sp:
            if s['fill']<0.50: continue   # decorative emblems are not hexagons
            t='major'
        elif not (0.75<ar<1.35) or not (0.19*sp*sp<a<0.34*sp*sp): continue
        elif s['fill']>0.83: t='medium'   # square
        elif 0.70<s['fill']<0.83: t='small'   # circle (pi/4 = 0.785)
        else: continue                    # orange load icons sit between the two
        out.append(dict(cx=float(ce[i][0]),cy=float(ce[i][1]),a=float(a),w=int(w),h=int(h),
                        fill=round(s['fill'],3),verts=s['verts'],type=t,clipped=bool(edge)))
    return out,red

# ---------------- main ----------------
def run(path,name,legend=None):
    im=cv2.imread(path); H,W=im.shape[:2]
    bg=background(im); board=board_mask(im,bg); ink=(raw_ink(im)*board).astype(np.uint8)
    water=water_mask(im); land=land_mask(im,bg)
    if legend:
        x0,y0,x1,y1=legend; ink[y0:y1,x0:x1]=0
    n,lab,st,ce=cv2.connectedComponentsWithStats(ink,8)
    A=st[:,4].astype(float)
    shapes={}
    tri_a=[]; dot_a=[]
    for i in range(1,n):
        if not (60<A[i]<6000): continue
        s=shape_of(lab,i,st); shapes[i]=s
        if tri_like(s): tri_a.append((i,A[i]))
        elif dot_like(s): dot_a.append((i,A[i]))
    # dots first: they are the most numerous symbol and cluster tightly, so
    # their median is reliable even on a piece with almost no mountains.
    dot_med=robust_med([a for _,a in dot_a])
    tri_cand=[a for _,a in tri_a if dot_med is None or 3.0*dot_med<a<12.0*dot_med]
    tri_med=robust_med(tri_cand) if len(tri_cand)>=5 else (5.6*dot_med if dot_med else None)
    seeds=[i for i,a in tri_a if 0.65*tri_med<a<1.45*tri_med]+[i for i,a in dot_a if 0.55*dot_med<a<1.7*dot_med]
    P=ce[seeds]
    print(f'[{name}] {W}x{H} seeds={len(P)} (tri {len(tri_a)}, dot {len(dot_a)}) tri_med={tri_med:.0f} dot_med={dot_med:.0f}')
    sol,ij,sp,res=fit_lattice(P,name)
    print(f'[{name}] fit spacing {sp:.1f}px  res mean {res.mean():.2f} med {np.median(res):.2f} max {res.max():.2f}')
    tree=cKDTree(ce[1:])
    # enumerate
    gi=np.arange(ij[:,0].min()-30,ij[:,0].max()+31); gj=np.arange(ij[:,1].min()-30,ij[:,1].max()+31)
    G=np.array([(a,b) for a in gi for b in gj],float); Pg=poly(G)@sol
    inb=(Pg[:,0]>8)&(Pg[:,0]<W-8)&(Pg[:,1]>8)&(Pg[:,1]<H-8)
    G,Pg=G[inb],Pg[inb]
    dd,kk=tree.query(Pg)
    cells=[]
    for gij,p,d_,k_ in zip(G,Pg,dd,kk):
        cls='none'; ar=-1.0
        if d_<0.26*sp:
            s=shapes.get(k_+1) or shape_of(lab,k_+1,st); ar=s['a'] if s else -1
            if dot_like(s) and 0.40*dot_med<ar<2.3*dot_med: cls='clear'
            elif tri_like(s) and 0.60*tri_med<ar<1.75*tri_med: cls='mtn'
            else: cls='amb'
        yi,xi=int(p[1]),int(p[0])
        cells.append(dict(i=int(gij[0]),j=int(gij[1]),x=float(p[0]),y=float(p[1]),cls=cls,area=float(ar),
                          land=bool(land[yi,xi]),water=bool(water[yi,xi]),board=bool(board[yi,xi])))
    # stage 2
    R=int(0.34*sp); T=templates(ink,cells,R); nfix=0; nedge=0
    # a milepost printed on the die-cut line is bisected: each piece holds half a
    # symbol, so match only the part of the template that is actually on-board.
    edgezone=(board-cv2.erode(board,np.ones((2*int(0.40*sp)+1,)*2,np.uint8),1)).astype(bool)
    for c in cells:
        x0,y0=int(round(c['x'])),int(round(c['y']))
        onedge = (0<=y0<H and 0<=x0<W and bool(edgezone[y0,x0]))
        if onedge: c['edge']=True
        if c['cls']=='none' and onedge: c['cls']='amb'
        if c['cls']!='amb': continue
        x,y=int(round(c['x'])),int(round(c['y']))
        # the land mask is unreliable on narrow puzzle tabs, so seam-zone cells
        # are gated on the board silhouette instead.
        gate = board[y,x] if c.get('edge') else c['land']
        if not (R+8<x<W-R-8 and R+8<y<H-R-8) or c['water'] or not gate:
            c['cls']='none'; continue
        bd=board[y-R:y+R+1,x-R:x+R+1]
        vis=bd if bd.shape==(2*R+1,2*R+1) else None
        cm=cover(ink,T['mtn'],x,y,R,vis=vis) if T['mtn'] is not None else 0
        cd=cover(ink,T['clear'],x,y,R,vis=vis) if T['clear'] is not None else 0
        lk=leak_of(ink,x,y,sp)
        c.update(cov_mtn=round(cm,3),cov_dot=round(cd,3),leak=round(lk,3),stage2=True)
        if cm>0.80 and lk<0.10: c['cls']='mtn'; nfix+=1; nedge+=c.get('edge',False)
        elif cd>0.80 and cm<0.55 and lk<0.10: c['cls']='clear'; nfix+=1; nedge+=c.get('edge',False)
        elif c.get('edge') and lk<0.06 and cd>0.60 and cm<0.40:
            c['cls']='clear'; c['seam_resolved']=True; nfix+=1; nedge+=1
        elif c.get('edge') and lk<0.06 and cm>0.60 and cd<0.75:
            c['cls']='mtn'; c['seam_resolved']=True; nfix+=1; nedge+=1
        elif c.get('edge'): c['cls']='edge'      # on the seam, evidence inconclusive
        else: c['cls']='none'
    # cities
    cities,red=find_cities(im,sp,dot_med,exclude=legend,board=board)
    cc=np.array([[c['x'],c['y']] for c in cells])
    for ci,cy in enumerate(cities):
        rad=1.15*sp if cy['type']=='major' else 0.36*sp
        d=np.hypot(cc[:,0]-cy['cx'],cc[:,1]-cy['cy'])
        idxs=np.where(d<rad)[0]
        cy['cells']=[[cells[k]['i'],cells[k]['j']] for k in idxs]
        for k in idxs: cells[k].update(cls='city',city=ci,ctype=cy['type'])
    print(f'[{name}] stage2 +{nfix} ({nedge} on seam), unresolved seam cells {sum(1 for c in cells if c["cls"]=="edge")}; cities '+str(collections.Counter(c['type'] for c in cities))
          +'  '+str(collections.Counter(c['cls'] for c in cells)))
    # recall check
    syms=[ce[i] for i in seeds]
    d2,_=cKDTree(cc).query(np.array(syms))
    print(f'[{name}] recall: {int((d2>0.26*sp).sum())} of {len(syms)} seed symbols unmatched')
    json.dump(dict(name=name,W=W,H=H,sp=float(sp),tri_med=tri_med,dot_med=dot_med,
                   sol=sol.tolist(),cells=cells,cities=cities),open(f'{name}.json','w'))
    ov=im.copy(); COL={'clear':(60,220,60),'mtn':(0,150,255),'city':(255,0,220)}
    for c in cells:
        x,y=int(c['x']),int(c['y'])
        if c['cls']=='edge':
            cv2.drawMarker(ov,(x,y),(255,255,0),cv2.MARKER_SQUARE,44,4); continue
        if c['cls']=='none':
            if c.get('cov_mtn',0)>0.8 or c.get('cov_dot',0)>0.9:
                cv2.drawMarker(ov,(x,y),(0,255,255),cv2.MARKER_TILTED_CROSS,50,5)
            continue
        cv2.circle(ov,(x,y),int(0.19*sp),COL[c['cls']],5)
    cv2.imwrite(f'ov_{name}.png',ov)
    cv2.imwrite(f'ovs_{name}.png',cv2.resize(ov,(W//4,H//4)))
    return cells

if __name__=='__main__':
    leg=None
    if len(sys.argv)>3: leg=tuple(int(v) for v in sys.argv[3].split(','))
    run(sys.argv[1],sys.argv[2],leg)
