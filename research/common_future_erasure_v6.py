from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/common_future_erasure_v6");OUT.mkdir(parents=True,exist_ok=True)

CANDIDATES={
 "persistence_ridge":{"beta_memory":.99730,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "critical_ridge":{"beta_memory":.998606,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "baseline":{"beta_memory":.92,"relaxation":.32,"pressure_gain":.55,"cross_gain":.85},
}
FUTURE_SCALES=[.25,.5,1.,1.5,2.,3.]
SEEDS=range(20)

def cfg(p,seed,noise=.01):
    return Config(**p,noise_std=noise)

def history(n,protocol,seed):
    rng=np.random.default_rng(seed+1000*protocol)
    if protocol==0:return np.ones(n),-np.ones(n)
    if protocol==1:return np.where(np.arange(n)%2==0,1.,-1.),np.ones(n)
    if protocol==2:return np.where(rng.random(n)<.12,-1.,1.),np.where(rng.random(n)<.06,1.,-1.)
    return np.sign(np.sin(np.linspace(0,18*np.pi,n))),np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))

def run(p,seed,protocol,scale):
    a,b=history(300,protocol,seed)
    future=np.sin(np.linspace(0,4*np.pi,500))*scale
    c=cfg(p,seed)
    A=simulate(np.r_[a,future],c,seed=seed);B=simulate(np.r_[b,future],c,seed=seed)
    d=np.abs(A["state"][300:]-B["state"][300:])
    return float(np.mean(d[:100])),float(np.mean(d[-100:])),float(np.mean(d)),float(np.max(d))

def main():
    rows=[]
    for name,p in CANDIDATES.items():
        for scale in FUTURE_SCALES:
            for seed in SEEDS:
                for protocol in range(4):
                    start,end,meanv,maxv=run(p,seed,protocol,scale)
                    rows.append({"regime":name,"scale":scale,"seed":seed,"protocol":protocol,
                                 "start_gap":start,"end_gap":end,"mean_gap":meanv,"max_gap":maxv})
    raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
    agg=raw.groupby(["regime","scale"]).agg({"start_gap":"mean","end_gap":"mean","mean_gap":"mean","max_gap":"mean"}).reset_index()
    agg["erasure_fraction"]=1.0-agg["end_gap"]/agg["start_gap"].clip(lower=1e-9)
    agg.to_csv(OUT/"erasure_curve.csv",index=False)
    summary={}
    for regime in CANDIDATES:
        q=agg[agg.regime==regime]
        summary[regime]={
          "best_erasure":float(q.erasure_fraction.max()),
          "worst_erasure":float(q.erasure_fraction.min()),
          "scale_at_max_persistence":float(q.loc[q.mean_gap.idxmax(),"scale"]),
          "mean_gap_at_scale_1":float(q.loc[q.scale==1.0,"mean_gap"].iloc[0]),
          "end_gap_at_scale_1":float(q.loc[q.scale==1.0,"end_gap"].iloc[0]),
        }
    out={"experiment":"common_future_erasure_v6","summary":summary}
    (OUT/"summary.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps(out,indent=2))
    print(agg.to_string(index=False))
if __name__=="__main__":main()
