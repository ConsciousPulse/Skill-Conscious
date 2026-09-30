from pathlib import Path
import json
import itertools
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/context_transplant_holdout_v12");OUT.mkdir(parents=True,exist_ok=True)
# Deliberately excludes the exact V10/V11 candidates.
PARAMS=[
 {"beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
SEEDS=range(10)

def history(pair,seed,n=300):
    rng=np.random.default_rng(seed+1000*pair)
    if pair==0:return np.ones(n),-np.ones(n)
    if pair==1:return np.where(np.arange(n)%2==0,1.,-1.),np.ones(n)
    if pair==2:return np.where(rng.random(n)<.12,-1.,1.),np.where(rng.random(n)<.06,1.,-1.)
    return np.sign(np.sin(np.linspace(0,18*np.pi,n))),np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))

def extract(p,seed,inp):
    c=Config(**p,noise_std=.01)
    R=simulate(np.r_[inp,np.zeros(500)],c,seed=seed)
    i=300
    return {"state_prev":float(R["state"][i-2]),"state":float(R["state"][i-1]),
            "memory":float(R["memory"][i-1]),"pressure":float(R["pressure"][i-1])},c

def cont(c,ctx,seed):
    return simulate(np.zeros(500),c,seed=seed,initial_prev_state=ctx["state_prev"],
                    initial_state=ctx["state"],initial_memory=ctx["memory"],initial_pressure=ctx["pressure"])

def dist(a,b): return float(np.mean(np.abs(a["state"]-b["state"]))

def aff(r,a,b):
    da,db=dist(r,a),dist(r,b)
    return float((db-da)/max(da+db,1e-12))

def main():
    rows=[]
    for pi,p in enumerate(PARAMS):
        for pair in range(4):
            for seed in SEEDS:
                A,c=extract(p,seed,history(pair,seed)[0]);B,_=extract(p,seed,history(pair,seed)[1])
                RA,RB=cont(c,A,seed),cont(c,B,seed)
                common={"state_prev":(A["state_prev"]+B["state_prev"])/2,"state":(A["state"]+B["state"])/2,
                        "memory":(A["memory"]+B["memory"])/2,"pressure":(A["pressure"]+B["pressure"])/2}
                for donor,ctx in [("A",A),("B",B)]:
                    expected=1 if donor=="A" else -1
                    contexts={
                      "state_only":{"state_prev":ctx["state_prev"],"state":ctx["state"],"memory":common["memory"],"pressure":common["pressure"]},
                      "memory_only":{"state_prev":common["state_prev"],"state":common["state"],"memory":ctx["memory"],"pressure":common["pressure"]},
                      "pressure_only":{"state_prev":common["state_prev"],"state":common["state"],"memory":common["memory"],"pressure":ctx["pressure"]}}
                    for mode,hctx in contexts.items():
                        R=cont(c,hctx,seed);x=aff(R,RA,RB)
                        rows.append({"param":pi,"beta":p["beta_memory"],"relaxation":p["relaxation"],
                                     "pressure_gain":p["pressure_gain"],"cross_gain":p["cross_gain"],
                                     "pair":pair,"seed":seed,"donor":donor,"mode":mode,
                                     "affinity":x,"correct":int(np.sign(x)==expected),"abs_affinity":abs(x)})
    raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
    agg=raw.groupby(["param","mode"]).agg(identity_accuracy=("correct","mean"),
                                          abs_affinity=("abs_affinity","mean"),
                                          affinity=("affinity","mean")).reset_index()
    pooled=raw.groupby("mode").agg(identity_accuracy=("correct","mean"),abs_affinity=("abs_affinity","mean"),
                                   affinity=("affinity","mean")).reset_index()
    agg.to_csv(OUT/"by_param.csv",index=False);pooled.to_csv(OUT/"pooled.csv",index=False)
    out={"experiment":"context_transplant_holdout_v12","pooled":pooled.to_dict("records"),
         "by_param":agg.to_dict("records"),
         "state_minus_memory_accuracy":float(pooled[pooled.mode=="state_only"].identity_accuracy.iloc[0]-
                                              pooled[pooled.mode=="memory_only"].identity_accuracy.iloc[0])}
    (OUT/"summary.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print("POOLED");print(pooled.to_string(index=False))
    print("BY_PARAM");print(agg.to_string(index=False))
if __name__=="__main__":main()
