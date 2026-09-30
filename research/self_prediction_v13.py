from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error
from src.ontto.dynamics import Config, simulate

OUT=Path("results/self_prediction_v13");OUT.mkdir(parents=True,exist_ok=True)
REGIMES={
 "persistence":{"beta_memory":.99730,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "critical":{"beta_memory":.998606,"relaxation":1.205,"pressure_gain":.125,"cross_gain":.15},
 "holdout_critical":{"beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 "baseline":{"beta_memory":.92,"relaxation":.32,"pressure_gain":.55,"cross_gain":.85},
}
SEEDS=range(20)

def make_inputs(seed,n=1000):
    rng=np.random.default_rng(seed)
    u=np.zeros(n)
    blocks=np.array([-.8,-.4,0,.4,.8])
    for k in range(0,n,25):
        u[k:k+25]=rng.choice(blocks)
    return u

def simulate_features(p,seed):
    u=make_inputs(seed)
    c=Config(**p,noise_std=.01)
    R=simulate(u,c,seed=seed)
    x=np.column_stack([u[:-1],u[1:],R["state"][:-1],R["memory"][:-1],R["pressure"][:-1],
                       R["score"][:-1],R["cross"][:-1],R["theta"][:-1]])
    ext=np.column_stack([u[:-1],u[1:]])
    target=R["state"][1:]
    return ext,x,target

def main():
    rows=[]
    # Cross-seed generalization: train on 15 seeds, test on 5 held-out seeds.
    folds=[list(range(k,k+5)) for k in [0,5,10,15]]
    for reg,p in REGIMES.items():
        for fi,test_seeds in enumerate(folds):
            train_seeds=[s for s in SEEDS if s not in test_seeds]
            Xext=[];Xfull=[];Y=[];Xscr=[]
            for s in train_seeds:
                ext,full,y=simulate_features(p,s)
                Xext.append(ext);Xfull.append(full);Y.append(y)
            Xe=np.vstack(Xext);Xf=np.vstack(Xfull);Y=np.concatenate(Y)
            me=Ridge(alpha=1e-3).fit(Xe,Y);mf=Ridge(alpha=1e-3).fit(Xf,Y)
            for s in test_seeds:
                ext,full,y=simulate_features(p,s)
                pe=me.predict(ext);pf=mf.predict(full)
                rows.append({"regime":reg,"fold":fi,"seed":s,
                             "r2_external":r2_score(y,pe),"r2_internal":r2_score(y,pf),
                             "gain_r2":r2_score(y,pf)-r2_score(y,pe),
                             "mae_external":mean_absolute_error(y,pe),
                             "mae_internal":mean_absolute_error(y,pf),
                             "gain_mae":mean_absolute_error(y,pe)-mean_absolute_error(y,pf)})
    raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
    agg=raw.groupby("regime").agg({"r2_external":["mean","std"],"r2_internal":["mean","std"],
                                   "gain_r2":["mean","std"],"mae_external":"mean","mae_internal":"mean","gain_mae":"mean"}).reset_index()
    agg.columns=["regime","r2_external_mean","r2_external_sd","r2_internal_mean","r2_internal_sd",
                 "gain_r2_mean","gain_r2_sd","mae_external_mean","mae_internal_mean","gain_mae_mean"]
    agg.to_csv(OUT/"summary.csv",index=False)
    out={"experiment":"self_prediction_v13","results":agg.to_dict("records")}
    (OUT/"summary.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(agg.to_string(index=False))
if __name__=="__main__":main()
