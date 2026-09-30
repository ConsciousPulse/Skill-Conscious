from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/context_factorial_v9");OUT.mkdir(parents=True,exist_ok=True)
REGIMES={
 "persistence":{"beta_memory":.99730,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "critical":{"beta_memory":.998606,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "baseline":{"beta_memory":.92,"relaxation":.32,"pressure_gain":.55,"cross_gain":.85},
}
SEEDS=range(20)

def run(p,seed,mode):
    a=np.ones(300);b=-np.ones(300);future=np.zeros(500);c=Config(**p,noise_std=.01)
    A=simulate(np.r_[a,future],c,seed=seed);B=simulate(np.r_[b,future],c,seed=seed)
    i=300
    A0,A1=float(A["state"][i-2]),float(A["state"][i-1]);B0,B1=float(B["state"][i-2]),float(B["state"][i-1])
    Am,Bm=float(A["memory"][i-1]),float(B["memory"][i-1]);Ap,Bp=float(A["pressure"][i-1]),float(B["pressure"][i-1])
    ms=(Am+Bm)/2.;ps=(Ap+Bp)/2.;s0=(A0+B0)/2.;s1=(A1+B1)/2.
    if mode=="full": ia,ja,ib,jb=A0,B0,A1,B1;am,bm=Am,Bm;ap,bp=Ap,Bp
    elif mode=="state_memory": ia=ja=s0;ib=jb=s1;am=bm=ms;ap,bp=Ap,Bp
    elif mode=="state_pressure": ia=ja=s0;ib=jb=s1;am,bm=Am,Bm;ap=bp=ps
    elif mode=="memory_pressure": ia,ja,ib,jb=A0,B0,A1,B1;am=bm=ms;ap=bp=ps
    else: ia=ja=s0;ib=jb=s1;am=bm=ms;ap=bp=ps
    FA=simulate(future,c,seed=seed,initial_prev_state=ia,initial_state=ib,initial_memory=am,initial_pressure=ap)
    FB=simulate(future,c,seed=seed,initial_prev_state=ja,initial_state=jb,initial_memory=bm,initial_pressure=bp)
    d=np.abs(FA["state"]-FB["state"])
    return float(np.mean(d[:100])),float(np.mean(d[-100:])),float(np.mean(d))

def main():
    modes=["full","state_memory","state_pressure","memory_pressure","all"]
    rows=[]
    for reg,p in REGIMES.items():
        for mode in modes:
            for seed in SEEDS:
                s,e,m=run(p,seed,mode);rows.append({"regime":reg,"mode":mode,"seed":seed,"start":s,"end":e,"mean":m})
    raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
    agg=raw.groupby(["regime","mode"]).agg({"start":"mean","end":"mean","mean":"mean"}).reset_index()
    agg["end_vs_full"]=agg.apply(lambda r:r.end/max(float(agg[(agg.regime==r.regime)&(agg.mode=="full")].end.iloc[0]),1e-12),axis=1)
    agg.to_csv(OUT/"factorial.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps({"experiment":"context_factorial_v9","results":agg.to_dict("records")},indent=2),encoding="utf-8")
    print(agg.to_string(index=False))
if __name__=="__main__":main()
