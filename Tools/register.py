import json,numpy as np,itertools,cv2
NAMES=['NorthWest','NorthCentral','NorthEast','SouthWest','SouthCentral','SouthEast']
def jac(sol,i,j):
    # d(x,y)/di and /dj of  [1,i,j,i2,j2,ij] @ sol
    di=np.array([0,1,0,2*i,0,j],float)@sol
    dj=np.array([0,0,1,0,2*j,i],float)@sol
    return di,dj
def ang(v): return np.degrees(np.arctan2(v[1],v[0]))%180
D={}
for n in NAMES:
    d=json.load(open(n+'.json')); sol=np.array(d['sol'])
    ij=np.array([[c['i'],c['j']] for c in d['cells']],float)
    ci,cj=ij.mean(0)
    du,dv=jac(sol,ci,cj)
    # canonical: e1 nearest 30 deg (x>0), e2 nearest 90 deg (y>0)
    cands={}
    for (p,q) in [(1,0),(0,1),(1,1),(1,-1),(-1,1),(-1,0),(0,-1),(-1,-1)]:
        v=p*du+q*dv
        if np.hypot(*v)<0.5*np.hypot(*du): continue
        cands[(p,q)]=v
    def pick(target,want_y=True):
        best=None
        for k,v in cands.items():
            a=np.degrees(np.arctan2(v[1],v[0]))
            if want_y and v[1]<=0: continue
            e=abs(((a-target+180)%360)-180)
            if best is None or e<best[0]: best=(e,k,v)
        return best
    e1=pick(30); e2=pick(90)
    # e1 = p*du + q*dv, so M's COLUMNS are the canonical axes expressed in (i,j);
    # the coordinate change is the inverse of that, not its transpose.
    Mt=np.column_stack([np.array(e1[1],float),np.array(e2[1],float)])
    K=np.round(np.linalg.inv(Mt)).astype(int)
    d['K']=K.tolist()
    d['spacing_e1']=float(np.hypot(*e1[2])); d['spacing_e2']=float(np.hypot(*e2[2]))
    print(n,'e1',e1[1],'ang %.1f len %.1f'%(ang(e1[2]),np.hypot(*e1[2])),
              '| e2',e2[1],'ang %.1f len %.1f'%(ang(e2[2]),np.hypot(*e2[2])))
    for c in d['cells']:
        a,b=K@np.array([c['i'],c['j']])
        c['a']=int(a); c['b']=int(b)
    D[n]=d
json.dump({n:{'K':D[n]['K']} for n in NAMES},open('K.json','w'))
np.save('cells_all.npy',np.array([1]))
import pickle; pickle.dump(D,open('D.pkl','wb'))
