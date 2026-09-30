from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_reference_free_margin_v39")
OUT.mkdir(parents=True, exist_ok=True)

PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
HSEEDS=range(140,150)
CSEEDS=range(9400,9410)
N=300
FUTURE=60
RADIUS=1.1
STRIDE=5
MEMS=[-0.8,0.0,0.8]
PRESS=[0.0,1.0,2.0]
ANGLES=[0,30,150]

def history(pair,seed,n=N):
    rng=np.random.default_rng(seed+1000*pair)
    if pair==0:return np.ones(n),-np.ones(n)
    if pair==1:return np.where(np.arange(n)%2==0,1.,-1.),np.ones(n)
    if pair==2:
        return np.where(rng.random(n)<.12,-1.,1.),np.where(rng.random(n)<.06,1.,-1.)
    return np.sign(np.sin(np.linspace(0,18*np.pi,n))),np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))

def extract(cfg,seed,u):
    r=simulate(np.r_[u,np.zeros(FUTURE)],cfg,seed=seed)
    i=N
    return {"state_prev":float(r["state"][i-2]),"state":float(r["state"][i-1]),
            "memory":float(r["memory"][i-1]),"pressure":float(r["pressure"][i-1])}

def cont(cfg,ctx,seed):
    return simulate(np.zeros(FUTURE),cfg,seed=seed,
                    initial_prev_state=ctx["state_prev"],initial_state=ctx["state"],
                    initial_memory=ctx["memory"],initial_pressure=ctx["pressure"])

def transform(donor,receiver,angle):
    d=np.array([donor["state_prev"]-receiver["state_prev"],donor["state"]-receiver["state"]])
    th=np.deg2rad(angle)
    R=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]])
    rd=RADIUS*(R@d)
    c=dict(receiver); c["state_prev"]=receiver["state_prev"]+rd[0]; c["state"]=receiver["state"]+rd[1]
    return c

def features(run):
    s=run["state"][::STRIDE].astype(float)
    ds=np.diff(s); dd=np.diff(s,2)
    return np.array([
        np.mean(s),np.std(s),np.mean(np.abs(s)),np.max(s)-np.min(s),
        np.mean(ds),np.std(ds),np.mean(np.abs(ds)),
        np.std(dd),np.mean(np.abs(dd)),s[-1]-s[0],
        np.mean(s[:4]),np.mean(s[-4:])
    ],float)

def main():
    rows=[]
    for pp in PARAMS:
        cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
        for pair in range(4):
            for hs in HSEEDS:
                ua,ub=history(pair,hs)
                a=extract(cfg,hs,ua); b=extract(cfg,hs,ub)
                receiver={k:(a[k]+b[k])/2 for k in a}
                for mem in MEMS:
                    for pressure in PRESS:
                        rc=dict(receiver); rc["memory"]=mem; rc["pressure"]=pressure
                        for angle in ANGLES:
                            for donor,label in [(a,0),(b,1)]:
                                st=transform(donor,rc,angle)
                                for cs in CSEEDS:
                                    f=features(cont(cfg,st,cs+hs))
                                    rows.append([pp["name"],pair,hs,mem,pressure,angle,label,*f])
    raw=pd.DataFrame(rows,columns=["param","pair","history_seed","memory","pressure","angle_deg","label"]+[f"f{i}" for i in range(12)])
    raw.to_csv(OUT/"raw.csv",index=False)
    feat=[f"f{i}" for i in range(12)]
    rec=[]
    for hs in HSEEDS:
        train=raw[raw.history_seed!=hs]
        test=raw[raw.history_seed==hs]
        model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=5000,C=1.0))
        model.fit(train[feat],train.label)
        for angle in ANGLES:
            sub=test[test.angle_deg==angle]
            proba=model.predict_proba(sub[feat])[:,1]
            signed=(2*sub.label.to_numpy()-1)*(2*proba-1)
            signed_logit=(2*sub.label.to_numpy()-1)*model[-1].decision_function(
                model[:-1].transform(sub[feat]) if hasattr(model,"steps") else sub[feat]
            )
            # The pipeline's decision_function is the safest exact implementation.
            signed_logit=(2*sub.label.to_numpy()-1)*model.decision_function(sub[feat])
            for context_key,g in sub.assign(signed_margin=signed,signed_logit=signed_logit).groupby(["pair","memory","pressure"]):
                rec.append({
                    "heldout_history_seed":hs,
                    "pair":int(context_key[0]),
                    "memory":float(context_key[1]),
                    "pressure":float(context_key[2]),
                    "angle_deg":angle,
                    "mean_signed_margin":float(g.signed_margin.mean()),
                    "mean_signed_logit":float(g.signed_logit.mean()),
                    "accuracy":float(accuracy_score(g.label,(proba[sub.index.isin(g.index)]>=.5).astype(int))) if False else float(np.mean(((g.signed_margin>=0)))),
                })
    dec=pd.DataFrame(rec)
    dec.to_csv(OUT/"decoder_context_summary.csv",index=False)
    block=dec.groupby(["heldout_history_seed","angle_deg"],as_index=False).agg(
        mean_signed_margin=("mean_signed_margin","mean"),
        mean_signed_logit=("mean_signed_logit","mean"),
        accuracy=("accuracy","mean")
    )
    block.to_csv(OUT/"decoder_summary.csv",index=False)
    stats=block.groupby("angle_deg",as_index=False).agg(
        mean_signed_margin=("mean_signed_margin","mean"),
        sd_signed_margin=("mean_signed_margin","std"),
        mean_signed_logit=("mean_signed_logit","mean"),
        sd_signed_logit=("mean_signed_logit","std"),
        mean_accuracy=("accuracy","mean")
    )
    stats.to_csv(OUT/"angle_summary.csv",index=False)

    results=[]
    rng=np.random.default_rng(939393)
    for metric in ["mean_signed_margin","mean_signed_logit"]:
        a=block[block.angle_deg==30].sort_values("heldout_history_seed")[metric].to_numpy()
        b=block[block.angle_deg==150].sort_values("heldout_history_seed")[metric].to_numpy()
        d=a-b
        obs=float(d.mean())
        null=np.mean(rng.choice([-1.,1.],size=(20000,len(d)))*d[None,:],axis=1)
        results.append({
            "metric":metric,
            "observed_30_minus_150":obs,
            "null_mean":float(null.mean()),
            "null_95th":float(np.quantile(null,.95)),
            "signflip_p":float((1+np.sum(null>=obs))/20001),
            "n_history_blocks":int(len(d))
        })
    result_df=pd.DataFrame(results)
    result_df.to_csv(OUT/"metric_summary.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps({
        "experiment":"state_geometry_reference_free_margin_v39",
        "design":{
            "independent_history_seeds":list(HSEEDS),
            "angles_deg":ANGLES,
            "memory_values":MEMS,
            "pressure_values":PRESS,
            "radius":RADIUS,
            "future_input":"exactly zero",
            "decoder":"cross-history standardized logistic regression",
            "features":"12 reference-free trajectory statistics",
            "primary":"30° minus 150° paired continuous signed decoder margin",
            "null":"paired sign flip across held-out history-seed blocks"
        }
    },indent=2),encoding="utf-8")
    print(stats.to_string(index=False)); print(result_df.to_string(index=False))

if __name__=="__main__":
    main()
