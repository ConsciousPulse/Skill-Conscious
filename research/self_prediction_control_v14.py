from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from src.ontto.dynamics import Config, simulate

OUT=Path("results/self_prediction_control_v14");OUT.mkdir(parents=True,exist_ok=True)
REGIMES={
 "critical":{"beta_memory":.998606,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "holdout_critical":{"beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 "persistence":{"beta_memory":.99730,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "baseline":{"beta_memory":.92,"relaxation":.32,"pressure_gain":.55,"cross_gain":.85},
}
def inputs(seed,n=1000):
    rng=np.random.default_rng(seed);u=np.zeros(n);blocks=np.array([-.8,-.4,0,.4,.8])
    for k in range(0,n,25):u[k:k+25]=rng.choice(blocks)
    return u
def sim(p,seed):
    u=inputs(seed);R=simulate(u,Config(**p,noise_std=.01),seed=seed)
    y=R["state"][1:]
    sets={
      "external":np.column_stack([u[:-1],u[1:]]),
      "state":np.column_stack([u[:-1],R["state"][:-1]]),
      "memory":np.column_stack([u[:-1],R["memory"][:-1]]),
      "pressure":np.column_stack([u[:-1],R["pressure"][:-1]]),
    }
    return sets,y
def main():
    folds=[list(range(k,k+5)) for k in [0,5,10,15]];rows=[]
    for reg,p in REGIMES.items():
        for fi,test in enumerate(folds):
            train=[s for s in range(20) if s not in test]
            models={}
            for name in ["external","state","memory","pressure"]:
                X=[];Y=[]
                for s in train:
                    sets,y=sim(p,s);X.append(sets[name]);Y.append(y)
                models[name]=Ridge(alpha=1e-3).fit(np.vstack(X),np.concatenate(Y))
            for s in test:
                sets,y=sim(p,s)
                for name,m in models.items():
                    rows.append({"regime":reg,"fold":fi,"seed":s,"feature":name,"r2":r2_score(y,m.predict(sets[name]))})
    raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
    agg=raw.groupby(["regime","feature"]).agg(r2_mean=("r2","mean"),r2_sd=("r2","std")).reset_index()
    agg.to_csv(OUT/"summary.csv",index=False)
    piv=agg.pivot(index="regime",columns="feature",values="r2_mean").reset_index()
    piv["state_gain_vs_external"]=piv["state"]-piv["external"]
    piv["memory_gain_vs_external"]=piv["memory"]-piv["external"]
    piv["pressure_gain_vs_external"]=piv["pressure"]-piv["external"]
    piv.to_csv(OUT/"matched_dimension.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps({"experiment":"self_prediction_control_v14","results":piv.to_dict("records")},indent=2),encoding="utf-8")
    print(piv.to_string(index=False))
if __name__=="__main__":main()
