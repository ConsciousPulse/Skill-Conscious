from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/input_agnostic_memory_v7");OUT.mkdir(parents=True,exist_ok=True)
REGIMES={
 "persistence":{"beta_memory":.99730,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "critical":{"beta_memory":.998606,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "baseline":{"beta_memory":.92,"relaxation":.32,"pressure_gain":.55,"cross_gain":.85},
}
SEEDS=range(20)

def make(p,seed):
    return Config(**p,noise_std=.01)

def hist(n,kind,seed):
    rng=np.random.default_rng(seed+7000*kind)
    if kind==0:return np.ones(n),-np.ones(n)
    if kind==1:return np.where(np.arange(n)%2==0,1.,-1.),np.ones(n)
    if kind==2:return np.where(rng.random(n)<.12,-1.,1.),np.where(rng.random(n)<.06,1.,-1.)
    return np.sign(np.sin(np.linspace(0,18*np.pi,n))),np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))

def future_signal(kind,n,seed):
    rng=np.random.default_rng(seed+9000*kind)
    if kind==0:return np.zeros(n)
    if kind==1:return np.ones(n)*.0
    if kind==2:return np.sin(np.linspace(0,4*np.pi,n))*.25
    if kind==3:return rng.normal(0,.05,n)
    return np.sin(np.linspace(0,20*np.pi,n))*.05

def measure(p,seed,hproto,fproto):
    a,b=hist(300,hproto,seed);f=future_signal(fproto,500,seed);c=make(p,seed)
    A=simulate(np.r_[a,f],c,seed=seed);B=simulate(np.r_[b,f],c,seed=seed)
    d=np.abs(A["state"][300:]-B["state"][300:])
    return float(np.mean(d[:100])),float(np.mean(d[-100:])),float(np.mean(d))

def main():
    rows=[]
    for name,p in REGIMES.items():
        for h in range(4):
            for f in range(5):
                for seed in SEEDS:
                    a,b,m=measure(p,seed,h,f)
                    rows.append({"regime":name,"history":h,"future":f,"seed":seed,"start":a,"end":b,"mean":m})
    raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
    agg=raw.groupby(["regime","future"]).agg({"start":"mean","end":"mean","mean":"mean"}).reset_index()
    agg["retention"]=agg["end"]/agg["start"].clip(lower=1e-9)
    agg.to_csv(OUT/"future_modes.csv",index=False)
    summary={}
    for reg in REGIMES:
        q=agg[agg.regime==reg]
        summary[reg]={"zero_future_retention":float(q[q.future==0].retention.iloc[0]),
                      "mean_retention":float(q.retention.mean()),
                      "max_retention":float(q.retention.max()),
                      "zero_future_end_gap":float(q[q.future==0].end.iloc[0])}
    (OUT/"summary.json").write_text(json.dumps({"experiment":"input_agnostic_memory_v7","summary":summary},indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2));print(agg.to_string(index=False))
if __name__=="__main__":main()
