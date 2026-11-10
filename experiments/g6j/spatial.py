"""Geographic replication inference. Within-cell weights are normalized separately."""
import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import t

CELLS=('00','01','10','11')
CONTRASTS={'extreme':[-1,0,0,1],'factorial':[1,-1,-1,1]}


class Design:
    def __init__(self, cells, blocks, weights):
        self.blocks, self.index=np.unique(blocks,return_inverse=True)
        self.xy=np.array([b.split(',') for b in self.blocks],float)
        self.distance=cdist(self.xy,self.xy,'cityblock')/2
        self.W=np.array([np.where(np.asarray(cells)==c,weights,0.) for c in CELLS])
        if np.any(self.W.sum(1)<=0):
            raise ValueError('missing intersectional cell')
        self.W/=self.W.sum(1)[:,None]
        self.mass=np.stack([self.aggregate(w) for w in self.W])
        self.effective=1/np.sum(self.mass**2,axis=1)

    def aggregate(self, v):
        return np.bincount(self.index,weights=v,minlength=len(self.blocks))

    def contrast(self, y, coeff):
        c=np.asarray(coeff,float)
        means=self.W@y
        effect=float(c@means)
        score=self.aggregate(np.sum(c[:,None]*self.W*(y-means[:,None]),axis=0))
        df=self.effective[c!=0].min()-1
        # Leave-one-block refits renormalize surviving weights within cells.
        totals=np.stack([self.aggregate(w*y) for w in self.W])
        active=c!=0
        remain=1-self.mass[active]
        stable=np.all(remain>1e-12,axis=0)
        deleted=c[active]@((means[active,None]-totals[active][:,stable])/remain[:,stable])
        out=dict(estimate=effect,df=df,min_effective_blocks=df+1,
                 leave_min=min(deleted),leave_max=max(deleted),unstable_deletions=sum(~stable))
        for rho,tag in [(0,'independent'),(.35,'primary'),(.65,'stress')]:
            se=np.sqrt(max(0,score@(rho**self.distance)@score))
            width=t.ppf(.975,df)*se
            out.update({tag+'_lo':effect-width,tag+'_hi':effect+width})
            if tag=='primary':
                out['se']=se
                out['p']=2*t.sf(abs(effect)/se,df) if se else (0. if effect else 1.)
        return out


def bounds(lo,hi,design,coeff):
    a=np.asarray(coeff)@design.W
    return (float(np.maximum(a,0)@lo+np.minimum(a,0)@hi),
            float(np.maximum(a,0)@hi+np.minimum(a,0)@lo))


def holm(p):
    order=np.argsort(p)
    result=np.empty(len(p))
    result[order]=np.minimum(1,np.maximum.accumulate(np.asarray(p)[order]*np.arange(len(p),0,-1)))
    return result
