from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/critical_boundary_fast_v4");OUT.mkdir(parents=True,exist_ok=True)
RELAX=1.205;PRESS=.125;CROSS=.15

def cfg(beta,seed=0):
    return Config(beta_memory=float(beta),relaxation=RELAX,pressure_gain=PRESS,cross_gain=CROSS,noise_std=.01)

def gap(c,seed,k):
    suffix=np.sin(np.linspace(0,4*np.pi,160))*.7;n=240
    rng=np.random.default_rng(seed+100*k)
    if k==0:a=np.ones(n);b=-np.ones(n)
    elif k==1:a=np.where(np.arange(n)%2==0,1.,-1.);b=np.ones(n)
    else:a=np.where(rng.random(n)<.12,-1.,1.);b=np.where(rng.random(n)<.06,1.,-1.)
    A=simulate(np.r_[a,suffix],c,seed=seed);B=simulate(np.r_[b,suffix],c,seed=seed)
    return float(np.mean(np.abs(A["state"][-120:]-B["state"][-120:])))

def lift(c,seed):
    u=np.zeros(600);u[90:140]=.7;u[260:320]=-1.;u[450:500]=.4
    R=simulate(u,c,seed=seed);q=R["q"][200:];x=R["cross"][200:]
    hi=x>=np.quantile(x,.75);lo=x<=np.quantile(x,.25)
    return float(np.mean((q=="X")[hi])-np.mean((q=="X")[lo]))

def main():
    betas=np.round(np.linspace(.996,.9994,69),6);rows=[]
    for b in betas:
        for s in range(8):
            c=cfg(b,s)
            gs=[gap(c,s,k) for k in range(3)]
            rows.append({"beta":b,"seed":s,"gap":np.mean(gs),"lift":lift(c,s)})
    raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
    a=raw.groupby("beta").mean(numeric_only=True).reset_index()
    a["gap_slope"]=np.gradient(a.gap,a.beta);a["lift_slope"]=np.gradient(a.lift,a.beta)
    a.to_csv(OUT/"boundary.csv",index=False)
    i=int(np.argmax(a.gap_slope))
    out={"max_gap_slope":float(a.gap_slope.iloc[i]),"beta_at_max_gap_slope":float(a.beta.iloc[i]),
         "max_lift_slope":float(a.lift_slope.max()),"beta_at_max_lift_slope":float(a.beta.iloc[int(np.argmax(a.lift_slope))]),
         "thresholds":{str(t):float(a[a.gap>=t].beta.iloc[0]) if np.any(a.gap>=t) else None for t in (.05,.1,.2,.3,.4,.5)},
         "top":a.nlargest(8,"gap").to_dict("records")}
    (OUT/"summary.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps(out,indent=2))
if __name__=="__main__":main()
