from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/critical_boundary_v4"); OUT.mkdir(parents=True,exist_ok=True)
SEEDS=range(20)
CENTER=dict(relaxation=1.205,pressure_gain=.125,cross_gain=.15)

def make(beta,noise=.01):
    return Config(beta_memory=float(beta),relaxation=CENTER["relaxation"],pressure_gain=CENTER["pressure_gain"],cross_gain=CENTER["cross_gain"],noise_std=noise)

def protocol_gap(cfg,seed,protocol):
    suffix=np.sin(np.linspace(0,4*np.pi,220))*.7
    n=300
    rng=np.random.default_rng(seed+1000*protocol)
    if protocol==0: a=np.ones(n); b=-np.ones(n)
    elif protocol==1: a=np.where(np.arange(n)%2==0,1.,-1.); b=np.ones(n)
    elif protocol==2: a=np.where(rng.random(n)<.15,-1.,1.); b=np.where(rng.random(n)<.05,1.,-1.)
    elif protocol==3: a=np.sign(np.sin(np.linspace(0,18*np.pi,n))); b=np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))
    else: a=np.sin(np.linspace(0,10*np.pi,n)); b=np.cos(np.linspace(0,6*np.pi,n))
    A=simulate(np.r_[a,suffix],cfg,seed=seed); B=simulate(np.r_[b,suffix],cfg,seed=seed)
    return float(np.mean(np.abs(A["state"][-180:]-B["state"][-180:])))

def recovery(cfg,seed,protocol=0):
    n=520;s=220
    a=np.ones(n-s);b=-np.ones(n-s);suffix=np.ones(s)
    A=simulate(np.r_[a,suffix],cfg,seed=seed);B=simulate(np.r_[b,suffix],cfg,seed=seed)
    d=np.abs(A["state"][-s:]-B["state"][-s:])
    start=max(d[0],1e-12)
    target=.1*start
    hit=np.where(d<=target)[0]
    return float(hit[0]) if len(hit) else float(s+1),float(d[-1]/start)

def critical(cfg,seed):
    u=np.zeros(800);u[120:180]=.7;u[350:430]=-1.;u[600:650]=.4
    R=simulate(u,cfg,seed=seed);q=R["q"][250:];c=R["cross"][250:]
    hi=c>=np.quantile(c,.75);lo=c<=np.quantile(c,.25)
    return float(np.mean((q=="X")[hi])-np.mean((q=="X")[lo]))

def main():
    betas=np.round(np.linspace(.9950,.9995,181),6)
    rows=[]
    for beta in betas:
        for seed in SEEDS:
            cfg=make(beta)
            gs=[protocol_gap(cfg,seed,p) for p in range(5)]
            rec,ratio=recovery(cfg,seed)
            rows.append({"beta":beta,"seed":seed,"gap_mean":np.mean(gs),"gap_min":np.min(gs),
                         "critical_lift":critical(cfg,seed),"recovery_10pct":rec,"tail_ratio":ratio})
    raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
    agg=raw.groupby("beta").agg({"gap_mean":["mean","std"],"gap_min":"mean","critical_lift":["mean","std"],
                                 "recovery_10pct":["mean","max"],"tail_ratio":["mean","std"]})
    agg.columns=["_".join(x) for x in agg.columns];agg=agg.reset_index();agg.to_csv(OUT/"boundary.csv",index=False)
    # Operational thresholds and local slopes
    report={}
    for threshold in [.05,.10,.20,.30,.40,.50]:
        q=agg[agg.gap_mean_mean>=threshold]
        report[f"first_beta_gap_{threshold}"]=float(q.beta.iloc[0]) if len(q) else None
    # steepest local derivative of mean gap and critical lift
    report["max_gap_slope"]=float(np.max(np.gradient(agg.gap_mean_mean.values,agg.beta.values)))
    report["beta_at_max_gap_slope"]=float(agg.beta.iloc[int(np.argmax(np.gradient(agg.gap_mean_mean.values,agg.beta.values)))])
    report["max_critical_slope"]=float(np.max(np.gradient(agg.critical_lift_mean.values,agg.beta.values)))
    report["beta_at_max_critical_slope"]=float(agg.beta.iloc[int(np.argmax(np.gradient(agg.critical_lift_mean.values,agg.beta.values)))])
    # Compare far-below, boundary, and candidate bands.
    bands={"low":(.995,.997),"edge":(.998,.9985),"candidate":(.9985,.9990),"high":(.999,.9995)}
    band_summary={}
    for name,(lo,hi) in bands.items():
        q=raw[(raw.beta>=lo)&(raw.beta<hi)]
        band_summary[name]={"gap":float(q.gap_mean.mean()),"critical_lift":float(q.critical_lift.mean()),
                            "recovery":float(q.recovery_10pct.mean()),"tail_ratio":float(q.tail_ratio.mean())}
    out={"experiment":"critical_boundary_v4","center":CENTER,"bands":band_summary,"thresholds":report}
    (OUT/"summary.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print("BOUNDARY",json.dumps(report))
    print("BANDS",json.dumps(band_summary))
    print("TOP",agg.nlargest(8,"gap_mean_mean").to_string(index=False))
if __name__=="__main__":main()
