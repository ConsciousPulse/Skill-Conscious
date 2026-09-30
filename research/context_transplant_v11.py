from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/context_transplant_v11");OUT.mkdir(parents=True,exist_ok=True)
REGIMES={
 "persistence":{"beta_memory":.99730,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "critical":{"beta_memory":.998606,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "baseline":{"beta_memory":.92,"relaxation":.32,"pressure_gain":.55,"cross_gain":.85},
}
SEEDS=range(20)

def history(pair,seed,n=300):
    rng=np.random.default_rng(seed+1000*pair)
    if pair==0:return np.ones(n),-np.ones(n)
    if pair==1:return np.where(np.arange(n)%2==0,1.,-1.),np.ones(n)
    if pair==2:return np.where(rng.random(n)<.12,-1.,1.),np.where(rng.random(n)<.06,1.,-1.)
    if pair==3:return np.sign(np.sin(np.linspace(0,18*np.pi,n))),np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))
    return np.sin(np.linspace(0,10*np.pi,n)),np.cos(np.linspace(0,6*np.pi,n))

def extract(p,seed,inp):
    c=Config(**p,noise_std=.01)
    R=simulate(np.r_[inp,np.zeros(500)],c,seed=seed)
    i=300
    return {"state_prev":float(R["state"][i-2]),"state":float(R["state"][i-1]),
            "memory":float(R["memory"][i-1]),"pressure":float(R["pressure"][i-1])},c

def cont(c,ctx,seed):
    return simulate(np.zeros(500),c,seed=seed,initial_prev_state=ctx["state_prev"],
                    initial_state=ctx["state"],initial_memory=ctx["memory"],initial_pressure=ctx["pressure"])

def dist(a,b): return float(np.mean(np.abs(a["state"]-b["state"])))

def affinity(r,a,b):
    da,db=dist(r,a),dist(r,b)
    return float((db-da)/max(da+db,1e-12))

def main():
    modes=["A_state_only","B_state_only","A_memory_only","B_memory_only","A_pressure_only","B_pressure_only"]
    rows=[]
    for reg,p in REGIMES.items():
        for pair in range(4):
            for seed in SEEDS:
                A,c=extract(p,seed,history(pair,seed)[0]);B,_=extract(p,seed,history(pair,seed)[1])
                RA,RB=cont(c,A,seed),cont(c,B,seed)
                common={"state_prev":(A["state_prev"]+B["state_prev"])/2,"state":(A["state"]+B["state"])/2,
                        "memory":(A["memory"]+B["memory"])/2,"pressure":(A["pressure"]+B["pressure"])/2}
                for donor,ctx in [("A",A),("B",B)]:
                    state_only={"state_prev":ctx["state_prev"],"state":ctx["state"],"memory":common["memory"],"pressure":common["pressure"]}
                    memory_only={"state_prev":common["state_prev"],"state":common["state"],"memory":ctx["memory"],"pressure":common["pressure"]}
                    pressure_only={"state_prev":common["state_prev"],"state":common["state"],"memory":common["memory"],"pressure":ctx["pressure"]}
                    for label,hctx in [("state_only",state_only),("memory_only",memory_only),("pressure_only",pressure_only)]:
                        R=cont(c,hctx,seed)
                        aff=affinity(R,RA,RB)
                        expected=1 if donor=="A" else -1
                        rows.append({"regime":reg,"pair":pair,"seed":seed,"donor":donor,
                                     "mode":label,"affinity":aff,"correct":int(np.sign(aff)==expected),
                                     "abs_affinity":abs(aff)})
    raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
    agg=raw.groupby(["regime","mode"]).agg({"affinity":["mean","std"],"correct":"mean","abs_affinity":"mean"}).reset_index()
    agg.columns=["regime","mode","affinity_mean","affinity_sd","identity_accuracy","abs_affinity_mean"]
    agg.to_csv(OUT/"summary.csv",index=False)
    summary={"experiment":"context_transplant_v11","results":agg.to_dict("records")}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(agg.to_string(index=False))
if __name__=="__main__":main()
