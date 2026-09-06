import pickle,numpy as np,json,itertools
D=pickle.load(open('D.pkl','rb'))
NB=[(1,0),(-1,0),(0,1),(0,-1),(1,-1),(-1,1)]
S={n:{(c['a'],c['b']) for c in D[n]['cells'] if c.get('board')} for n in D}
def sc(A,B,t):
    Bt={(a+t[0],b+t[1]) for a,b in B}
    ov=len(A&Bt)
    ct=sum(1 for c in A for d in NB if (c[0]+d[0],c[1]+d[1]) in Bt)
    return ct-8*ov,ct,ov
def search(nA,nB,prior,rad=9):
    A,B=S[nA],S[nB]; best=None
    for da in range(prior[0]-rad,prior[0]+rad+1):
        for db in range(prior[1]-rad,prior[1]+rad+1):
            s=sc(A,B,(da,db))
            if best is None or s[0]>best[0][0]: best=(s,(da,db))
    return best
# physical priors: neighbour to the right is +one piece width, below is +one piece height.
# In canonical axes (e1 at 30 deg, e2 at 90 deg): moving +x by W cells needs
# a=W/cos30, b=-a/2 ; moving +y by H cells needs a=0, b=H.
def extent(n):
    A=np.array(sorted(S[n])); return A[:,0].ptp(), A[:,1].ptp()
pairs=[('NorthWest','NorthCentral','h'),('NorthCentral','NorthEast','h'),
       ('SouthWest','SouthCentral','h'),('SouthCentral','SouthEast','h'),
       ('NorthWest','SouthWest','v'),('NorthCentral','SouthCentral','v'),
       ('NorthEast','SouthEast','v')]
res={}
for a,b,kind in pairs:
    prior=(24,-12) if kind=='h' else (0,27)
    (s,ct,ov),t=search(a,b,prior)
    res[f'{a}|{b}']=list(t)
    print(f'{a:13s}->{b:13s} {kind} offset {t} contact {ct} overlap {ov}')
json.dump(res,open('offsets.json','w'))
