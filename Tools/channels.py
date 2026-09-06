import json,cv2,numpy as np,collections
import masks2 as M
PIECES=[('NorthWest','163813399'),('NorthCentral','163839438'),('NorthEast','170428058'),
        ('SouthWest','163825427'),('SouthCentral','163854400'),('SouthEast','170106074')]
K={n:np.array(v['K']) for n,v in json.load(open('K.json')).items()}
T=json.load(open('placement.json'))
board={(c['a'],c['b']):c for c in json.load(open('eb-board-mileposts.json'))['cells']}
NODE={k for k,c in board.items() if c['cls'] in ('clear','mtn','city')}
NB=[(1,0),(0,1),(1,-1)]
found=[]
for name,fn in PIECES:
    im=cv2.imread(f'/mnt/user-data/uploads/PXL_20260905_{fn}.jpg')
    H,W=im.shape[:2]
    wat=M.water_mask(im); bd=M.board_mask(im); ink=M.raw_ink(im)
    big=cv2.morphologyEx(wat,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(45,45)))
    # coastline = the rim of a water body. Normally drawn as a black line; at a
    # legal lake channel it is drawn blue, i.e. no dark ink on the rim.
    rim=(cv2.dilate(big,np.ones((13,13),np.uint8))-big).astype(np.uint8)
    inkd=cv2.dilate(ink,np.ones((11,11),np.uint8))
    blue_rim=(rim&(1-inkd)&bd).astype(np.uint8)
    d=json.load(open(name+'.json'))
    P={}
    for c in d['cells']:
        a,b=K[name]@np.array([c['i'],c['j']])
        P[(int(a+T[name][0]),int(b+T[name][1]))]=(c['x'],c['y'])
    okp=lambda x,y:0<=int(y)<H and 0<=int(x)<W and bd[int(y),int(x)]
    for k,(x0,y0) in P.items():
        if k not in NODE or not okp(x0,y0): continue
        for dd in NB:
            k2=(k[0]+dd[0],k[1]+dd[1])
            if k2 not in P or k2 not in NODE: continue
            x1,y1=P[k2]
            if not okp(x1,y1): continue
            n=80; w=0; br=0; blk=0
            for t in np.linspace(0.08,0.92,n):
                x,y=int(x0+(x1-x0)*t),int(y0+(y1-y0)*t)
                if not(0<=y<H and 0<=x<W): continue
                w+=big[y,x]; br+=blue_rim[y,x]; blk+=inkd[y,x]&rim[y,x]
            if w>=3:
                found.append(dict(piece=name,edge=[list(k),list(k2)],water=int(w),
                                  blue_rim=int(br),black_rim=int(blk)))
cand=collections.defaultdict(list)
for f in found: cand[tuple(sorted(map(tuple,f['edge'])))].append(f)
print('water-crossing edges:',len(cand))
ranked=sorted(cand.items(),key=lambda kv:-max(x['blue_rim']-x['black_rim'] for x in kv[1]))
for k,v in ranked[:16]:
    b=max(x['blue_rim'] for x in v); bl=max(x['black_rim'] for x in v)
    print('  ',k,'blue_rim',b,'black_rim',bl,v[0]['piece'])
json.dump([{'edge':[list(a),list(b)],'blue':max(x['blue_rim'] for x in v),
            'black':max(x['black_rim'] for x in v)} for (a,b),v in ranked],open('channels.json','w'),indent=1)
