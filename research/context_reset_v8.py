from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/context_reset_v8");OUT.mkdir(parents=True,exist_ok=True)
REGIMES={
 "persistence":{"beta_memory":.99730,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "critical":{"beta_memory":.998606,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "baseline":{"beta_memory":.92,"relaxation":.32,"pressure_gain":.55,"cross_gain":.85},
}
SEEDS=range(20)

def hist(seed):
    rng=np.random.default_rng(seed+7000)
    a=np.ones(300);b=-np.ones(300)
    return a,b

def run(p,seed,mode):
    a,b=hist(seed); future=np.zeros(500);c=Config(**p,noise_std=.01)
    A=simulate(np.r_[a,future],c,seed=seed);B=simulate(np.r_[b,future],c,seed=seed)
    idx=300
    # Context at the common-future boundary.
    A0=float(A["state"][idx-2]);A1=float(A["state"][idx-1]);Am=float(A["memory"][idx-1]);Ap=float(A["pressure"][idx-1])
    B0=float(B["state"][idx-2]);B1=float(B["state"][idx-1]);Bm=float(B["memory"][idx-1]);Bp=float(B["pressure"][idx-1])
    if mode=="full":
        ia,ib=A0,A1;ja,jb=B0,B1;am,bm=Am,Bm;ap,bp=Ap,Bp
    elif mode=="reset_state":
        s=(A1+B1)/2.;sp=(A0+B0)/2.;ia=ja=s;ib=jb=sp;am,bm=Am,Bm;ap,bp=Ap,Bp
    elif mode=="reset_memory":
        m=(Am+Bm)/2.;ia,ib=A0,A1;ja,jb=B0,B1;am=bm=m;ap,bp=Ap,Bp
    elif mode=="reset_pressure":
        pp=(Ap+Bp)/2.;ia,ib=A0,A1;ja,jb=B0,B1;am,bm=Am,Bm;ap=bp=pp
    else:
        s=(A1+B1)/2.;sp=(A0+B0)/2.;m=(Am+Bm)/2.;pp=(Ap+Bp)/2.
        ia=ja=s;ib=jb=sp;am=bm=m;ap=bp=pp
    # Continue with identical zero future.
    fa=simulate(future,c,seed=seed,initial_prev_state=ia,initial_state=ib,initial_memory=am,initial_pressure=ap)
    # Second branch uses separate initial values.
    fb=simulate(future,c,seed=seed+100000,initial_prev_state=ja,initial_state=jb,initial_memory=bm,initial_pressure=bp)
    d=np.abs(fa["state"]-fb["state"])
    return float(np.mean(d[:100])),float(np.mean(d[-100:])),float(np.mean(d))

def main():
    modes=["full","reset_state","reset_memory","reset_pressure","reset_all"]
    rows=[]
    for reg,p in REGIMES.items():
        for mode in modes:
            for seed in SEEDS:
                s,e,m=run(p,seed,mode)
                rows.append({"regime":reg,"mode":mode,"seed":seed,"start":s,"end":e,"mean":m})
    raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
    agg=raw.groupby(["regime","mode"]).agg({"start":"mean","end":"mean","mean":"mean"}).reset_index()
    agg["retention"]=agg["end"]/agg["start"].clip(lower=1e-9);agg.to_csv(OUT/"context_resets.csv",index=False)
    print(agg.to_string(index=False))
    (OUT/"summary.json").write_text(json.dumps({"experiment":"context_reset_v8","results":agg.to_dict("records")},indent=2),encoding="utf-8")
if __name__=="__main__":main()
