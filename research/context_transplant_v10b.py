from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/context_transplant_v10b");OUT.mkdir(parents=True,exist_ok=True)
REGIMES={
 "persistence":{"beta_memory":.99730,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "critical":{"beta_memory":.998606,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "baseline":{"beta_memory":.92,"relaxation":.32,"pressure_gain":.55,"cross_gain":.85},
}
SEEDS=range(20)

def history(kind,n=300,seed=0):
    rng=np.random.default_rng(seed+1000*kind)
    if kind==0:return np.ones(n)
    if kind==1:return -np.ones(n)
    if kind==2:return np.where(np.arange(n)%2==0,1.,-1.)
    return np.where(rng.random(n)<.12,-1.,1.)

def extract(p,seed,inp):
    c=Config(**p,noise_std=.01)
    R=simulate(np.r_[inp,np.zeros(500)],c,seed=seed)
    i=300
    return {
      "state_prev":float(R["state"][i-2]),"state":float(R["state"][i-1]),
      "memory":float(R["memory"][i-1]),"pressure":float(R["pressure"][i-1]),
    },c

def cont(c,ctx,seed):
    return simulate(np.zeros(500),c,seed=seed,initial_prev_state=ctx["state_prev"],
                    initial_state=ctx["state"],initial_memory=ctx["memory"],initial_pressure=ctx["pressure"])

def d(a,b):
    return float(np.mean(np.abs(a["state"]-b["state"])))

def affinity(r,a,b):
    da=d(r,a);db=d(r,b)
    return (db-da)/max(da+db,1e-12),da,db

def main():
    modes=["A_full","B_full","A_state_only","B_state_only","A_memory_only","B_memory_only",
           "A_pressure_only","B_pressure_only","A_minus_state","B_minus_state"]
    rows=[]
    for reg,p in REGIMES.items():
        for seed in SEEDS:
            A,c=extract(p,seed,history(0,seed=seed));B,_=extract(p,seed,history(1,seed=seed))
            common={
                "state_prev":(A["state_prev"]+B["state_prev"])/2,
                "state":(A["state"]+B["state"])/2,
                "memory":(A["memory"]+B["memory"])/2,
                "pressure":(A["pressure"]+B["pressure"])/2,
            }
            contexts={
              "A_full":A,"B_full":B,
              "A_state_only":{"state_prev":A["state_prev"],"state":A["state"],"memory":common["memory"],"pressure":common["pressure"]},
              "B_state_only":{"state_prev":B["state_prev"],"state":B["state"],"memory":common["memory"],"pressure":common["pressure"]},
              "A_memory_only":{"state_prev":common["state_prev"],"state":common["state"],"memory":A["memory"],"pressure":common["pressure"]},
              "B_memory_only":{"state_prev":common["state_prev"],"state":common["state"],"memory":B["memory"],"pressure":common["pressure"]},
              "A_pressure_only":{"state_prev":common["state_prev"],"state":common["state"],"memory":common["memory"],"pressure":A["pressure"]},
              "B_pressure_only":{"state_prev":common["state_prev"],"state":common["state"],"memory":common["memory"],"pressure":B["pressure"]},
              "A_minus_state":{"state_prev":B["state_prev"],"state":B["state"],"memory":A["memory"],"pressure":A["pressure"]},
              "B_minus_state":{"state_prev":A["state_prev"],"state":A["state"],"memory":B["memory"],"pressure":B["pressure"]},
            }
            RA=cont(c,A,seed);RB=cont(c,B,seed)
            for mode,ctx in contexts.items():
                R=RA if mode=="A_full" else RB if mode=="B_full" else cont(c,ctx,seed)
                aff,da,db=affinity(R,RA,RB)
                rows.append({"regime":reg,"seed":seed,"mode":mode,"dist_A":da,"dist_B":db,"affinity_A":aff})
    raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
    agg=raw.groupby(["regime","mode"]).agg({"dist_A":"mean","dist_B":"mean","affinity_A":["mean","std"]}).reset_index()
    agg.columns=["regime","mode","dist_A_mean","dist_B_mean","affinity_A_mean","affinity_A_sd"]
    agg.to_csv(OUT/"summary.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps({"experiment":"context_transplant_v10b","results":agg.to_dict("records")},indent=2),encoding="utf-8")
    print(agg.to_string(index=False))
if __name__=="__main__":main()
