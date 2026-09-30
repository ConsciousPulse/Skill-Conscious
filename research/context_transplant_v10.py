from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/context_transplant_v10");OUT.mkdir(parents=True,exist_ok=True)
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

def context(p,seed,inp):
    c=Config(**p,noise_std=.01)
    z=np.zeros(500)
    R=simulate(np.r_[inp,z],c,seed=seed)
    i=300
    return {
      "state_prev":float(R["state"][i-2]),"state":float(R["state"][i-1]),
      "memory":float(R["memory"][i-1]),"pressure":float(R["pressure"][i-1]),
    }, c

def continue_context(c,ctx,seed):
    z=np.zeros(500)
    return simulate(z,c,seed=seed,initial_prev_state=ctx["state_prev"],initial_state=ctx["state"],
                    initial_memory=ctx["memory"],initial_pressure=ctx["pressure"])

def distance(a,b):
    return float(np.mean(np.abs(a["state"]-b["state"])))

def main():
    modes=["A_full","B_full","A_state_B_memory_pressure","B_state_A_memory_pressure",
           "A_state_memory_B_pressure","B_state_memory_A_pressure","A_state_only","B_state_only"]
    rows=[]
    for reg,p in REGIMES.items():
        for seed in SEEDS:
            A_in=history(0,seed=seed);B_in=history(1,seed=seed)
            A,c=context(p,seed,A_in);B,_=context(p,seed,B_in)
            RA=continue_context(c,A,seed);RB=continue_context(c,B,seed)
            refs={"A":RA,"B":RB}
            hybrids={
              "A_state_B_memory_pressure":{"state_prev":A["state_prev"],"state":A["state"],"memory":B["memory"],"pressure":B["pressure"]},
              "B_state_A_memory_pressure":{"state_prev":B["state_prev"],"state":B["state"],"memory":A["memory"],"pressure":A["pressure"]},
              "A_state_memory_B_pressure":{"state_prev":A["state_prev"],"state":A["state"],"memory":A["memory"],"pressure":B["pressure"]},
              "B_state_memory_A_pressure":{"state_prev":B["state_prev"],"state":B["state"],"memory":B["memory"],"pressure":A["pressure"]},
              "A_state_only":{"state_prev":A["state_prev"],"state":A["state"],"memory":B["memory"],"pressure":B["pressure"]},
              "B_state_only":{"state_prev":B["state_prev"],"state":B["state"],"memory":A["memory"],"pressure":A["pressure"]},
            }
            for mode in modes:
                if mode=="A_full": R=RA
                elif mode=="B_full": R=RB
                else: R=continue_context(c,hybrids[mode],seed)
                da=distance(R,refs["A"]);db=distance(R,refs["B"])
                # positive means closer to A; +1 would be A, -1 B.
                affinity=(db-da)/max(da+db,1e-12)
                rows.append({"regime":reg,"seed":seed,"mode":mode,
                             "dist_A":da,"dist_B":db,"affinity_A":affinity})
    raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
    agg=raw.groupby(["regime","mode"]).agg({"dist_A":"mean","dist_B":"mean","affinity_A":["mean","std"]}).reset_index()
    agg.columns=["regime","mode","dist_A_mean","dist_B_mean","affinity_A_mean","affinity_A_sd"]
    agg.to_csv(OUT/"summary.csv",index=False)
    summary={"experiment":"context_transplant_v10","results":agg.to_dict("records")}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(agg.to_string(index=False))
if __name__=="__main__":main()
