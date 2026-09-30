from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/memory_lifetime_v5");OUT.mkdir(parents=True,exist_ok=True)
RELAX=1.205;PRESS=.125;CROSS=.15

def cfg(beta,seed):
    return Config(beta_memory=float(beta),relaxation=RELAX,pressure_gain=PRESS,cross_gain=CROSS,noise_std=.01)

def trajectory_gap(beta,seed,protocol=0,prefix=300,future=500):
    n=prefix; suffix=np.ones(future)
    rng=np.random.default_rng(seed+100*protocol)
    if protocol==0:
        a=np.ones(n);b=-np.ones(n)
    elif protocol==1:
        a=np.where(np.arange(n)%2==0,1.,-1.);b=np.ones(n)
    elif protocol==2:
        a=np.where(rng.random(n)<.12,-1.,1.);b=np.where(rng.random(n)<.06,1.,-1.)
    else:
        a=np.sign(np.sin(np.linspace(0,18*np.pi,n)));b=np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))
    c=cfg(beta,seed)
    A=simulate(np.r_[a,suffix],c,seed=seed)
    B=simulate(np.r_[b,suffix],c,seed=seed)
    d=np.abs(A["state"][n:]-B["state"][n:])
    d0=max(float(d[0]),1e-9)
    dn=d/d0
    def first_below(x):
        q=np.where(dn<=x)[0]
        return int(q[0]) if len(q) else future
    auc=float(np.trapz(np.clip(dn,0,2),dx=1.0))
    return {
        "auc":auc,
        "half_life":first_below(.5),
        "t20":first_below(.2),
        "t10":first_below(.1),
        "tail_ratio":float(np.mean(dn[-50:])),
        "max_ratio":float(np.max(dn)),
    }

def main():
    betas=np.round(np.linspace(.995, .9995, 91),6)
    rows=[]
    for beta in betas:
        for seed in range(20):
            for protocol in range(4):
                row=trajectory_gap(beta,seed,protocol)
                rows.append({"beta":beta,"seed":seed,"protocol":protocol,**row})
    raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
    agg=raw.groupby("beta").agg({"auc":["mean","std"],"half_life":["mean","std"],
                                 "t20":["mean","std"],"t10":["mean","std"],
                                 "tail_ratio":["mean","std"],"max_ratio":"mean"}).reset_index()
    agg.columns=["beta"]+[f"{a}_{b}" for a,b in agg.columns.tolist()[1:]]
    agg.to_csv(OUT/"lifetime_curve.csv",index=False)
    out={}
    for metric in ["auc_mean","half_life_mean","t20_mean","t10_mean","tail_ratio_mean"]:
        i=int(np.argmax(agg[metric].values))
        out["peak_"+metric]={"beta":float(agg.beta.iloc[i]),"value":float(agg[metric].iloc[i])}
    out["bands"]={}
    for name,(lo,hi) in {"A":(.995,.9965),"B":(.9965,.998),"C":(.998,.999),"D":(.999,.9995)}.items():
        q=agg[(agg.beta>=lo)&(agg.beta<hi)]
        out["bands"][name]={m:float(q[m].mean()) for m in ["auc_mean","half_life_mean","t20_mean","t10_mean","tail_ratio_mean"]}
    (OUT/"summary.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print("PEAKS",json.dumps(out,indent=2))
    print("TOP AUC");print(agg.nlargest(10,"auc_mean")[["beta","auc_mean","half_life_mean","t20_mean","t10_mean","tail_ratio_mean"]].to_string(index=False))
if __name__=="__main__":main()
