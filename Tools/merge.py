import pickle,numpy as np,json,cv2,collections
D=pickle.load(open('D.pkl','rb')); T=json.load(open('placement.json'))
COR={}
for c in json.load(open('corrections_local.json')):
    COR[(c['piece'],c['i'],c['j'])]=c['to']
NAMES=list(T)
PRI={'city':4,'mtn':3,'clear':3,'edge':1,'none':0}
board={}
for n in NAMES:
    ta,tb=T[n]
    for c in D[n]['cells']:
        # a cell just off the board silhouette can still be real: the fixer shows
        # one ring beyond it, so anything classified or hand-marked there must
        # survive the merge rather than being filtered out by the mask.
        if not (c.get('board') or c['cls']!='none' or (n,c['i'],c['j']) in COR): continue
        k=(c['a']+ta,c['b']+tb)
        cls=c['cls']; ct=c.get('ctype'); manual=False
        fix=COR.get((n,c['i'],c['j']))
        if fix is not None:
            manual=True
            if fix.startswith('city_'): cls,ct='city',fix.split('_')[1]
            else: cls,ct=fix,None
        rec=dict(cls=cls,piece=n,ctype=ct,seam=bool(c.get('edge')),manual=manual)
        if k not in board or rec['manual'] or (not board[k].get('manual') and PRI[rec['cls']]>PRI[board[k]['cls']]):
            if k in board: rec['also']=board[k]['piece']
            board[k]=rec
        else:
            board[k]['also']=n
print(collections.Counter(v['cls'] for v in board.values()))
print('total cells on board:',len(board))
seam=[k for k,v in board.items() if v['cls']=='edge']
print('still unresolved after merge:',len(seam))
json.dump({'cells':[{'a':k[0],'b':k[1],**v} for k,v in sorted(board.items())],
           'placement':T},open('eb-board-mileposts.json','w'))
# render
s=26.0; E1=np.array([np.cos(np.radians(30)),np.sin(np.radians(30))])*s; E2=np.array([0,1.0])*s
P={k:(k[0]*E1+k[1]*E2) for k in board}
xs=[p[0] for p in P.values()]; ys=[p[1] for p in P.values()]
W=int(max(xs)-min(xs))+80; H=int(max(ys)-min(ys))+80
img=np.full((H,W,3),255,np.uint8)
ox,oy=-min(xs)+40,-min(ys)+40
COL={'clear':(60,170,60),'mtn':(30,110,220),'city':(200,40,200),'edge':(0,215,255)}
for k,v in board.items():
    x,y=int(P[k][0]+ox),int(P[k][1]+oy)
    c=COL.get(v['cls'])
    if v['cls']=='clear': cv2.circle(img,(x,y),4,c,-1)
    elif v['cls']=='mtn': cv2.drawMarker(img,(x,y),c,cv2.MARKER_TRIANGLE_UP,14,3)
    elif v['cls']=='city': cv2.circle(img,(x,y),8,c,-1)
    elif v['cls']=='edge': cv2.drawMarker(img,(x,y),c,cv2.MARKER_SQUARE,12,3)
cv2.imwrite('/mnt/user-data/outputs/board_assembled.png',img)
print('render',W,H)
