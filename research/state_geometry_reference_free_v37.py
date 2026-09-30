from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, log_loss
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_reference_free_v37")
OUT.mkdir(parents=True, exist_ok=True)

PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":1.18,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
# Correct p5 to protocol value after construction.
PARAMS[4]["beta_memory"]=.9982

HSEEDS=range(120,130)
CSEEDS=range(7400,7410)
N=300
FUTURE=60
RADIUS=1.1
STRIDE=5
MEMS=[-0.8,0.0,0.8]
PRESS=[0.0,1.0,2.0]
ANGLES=[0,30,150]
WINDOW_STEPS=12  # first 60 future steps sampled every 5 steps
TEST_EACH_PAIR=True

def history(pair,seed,n=N):
    rng=np.random.default_rng(seed+1000*pair)
    if pair==0:return np.ones(n),-np.ones(n)
    if pair==1:return np.where(np.arange(n)%2==0,1.,-1.),np.ones(n)
    if pair==2:
        return (
            np.where(rng.random(n)<.12,-1.,1.),
            np.where(rng.random(n)<.06,1.,-1.)
        )
    return (
        np.sign(np.sin(np.linspace(0,18*np.pi,n))),
        np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))
    )

def extract(cfg,seed,u):
    r=simulate(np.r_[u,np.zeros(FUTURE)],cfg,seed=seed)
    i=N
    return {
        "state_prev":float(r["state"][i-2]),
        "state":float(r["state"][i-1]),
        "memory":float(r["memory"][i-1]),
        "pressure":float(r["pressure"][i-1]),
    }

def cont(cfg,ctx,seed):
    return simulate(
        np.zeros(FUTURE),cfg,seed=seed,
        initial_prev_state=ctx["state_prev"],
        initial_state=ctx["state"],
        initial_memory=ctx["memory"],
        initial_pressure=ctx["pressure"]
    )

def transform(donor,receiver,angle):
    d=np.array([
        donor["state_prev"]-receiver["state_prev"],
        donor["state"]-receiver["state"],
    ])
    th=np.deg2rad(angle)
    R=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]])
    rd=RADIUS*(R@d)
    c=dict(receiver)
    c["state_prev"]=receiver["state_prev"]+rd[0]
    c["state"]=receiver["state"]+rd[1]
    return c

def features(run):
    s=run["state"][::STRIDE].astype(float)
    # Fixed, reference-free trajectory observables.
    ds=np.diff(s)
    dd=np.diff(s,2)
    q1=np.mean(s)
    q2=np.std(s)
    q3=np.mean(np.abs(s))
    q4=np.max(s)-np.min(s)
    q5=np.mean(ds)
    q6=np.std(ds)
    q7=np.mean(np.abs(ds))
    q8=np.std(dd)
    q9=np.mean(np.abs(dd))
    q10=s[-1]-s[0]
    q11=np.mean(s[:4])
    q12=np.mean(s[-4:])
    # Preserve temporal structure without referencing another trajectory.
    return np.array([q1,q2,q3,q4,q5,q6,q7,q8,q9,q10,q11,q12],dtype=float)

def build_dataset():
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
                                    run=cont(cfg,st,cs+hs)
                                    f=features(run)
                                    rows.append({
                                        "param":pp["name"],"pair":pair,"history_seed":hs,
                                        "memory":mem,"pressure":pressure,"angle_deg":angle,
                                        "label":label, "seed":cs+hs, **{f"f{i}":x for i,x in enumerate(f)}
                                    })
    return pd.DataFrame(rows)

def fit_and_score(df):
    feat=[f"f{i}" for i in range(12)]
    records=[]
    for hs_test in sorted(df.history_seed.unique()):
        train=df[df.history_seed!=hs_test]
        test=df[df.history_seed==hs_test]
        model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=5000,C=1.0))
        model.fit(train[feat],train.label)
        pred=model.predict(test[feat])
        proba=model.predict_proba(test[feat])[:,1]
        for angle in ANGLES:
            sub=test[test.angle_deg==angle]
            pp=feat
            yhat=model.predict(sub[feat])
            ph=model.predict_proba(sub[feat])[:,1]
            records.append({
                "heldout_history_seed":hs_test,
                "angle_deg":angle,
                "accuracy":float(accuracy_score(sub.label,yhat)),
                "log_loss":float(log_loss(sub.label,ph,labels=[0,1])),
                "n":int(len(sub))
            })
    return pd.DataFrame(records)

def permutation_test(df_summary):
    # Global descriptive null: shuffle angle labels within each held-out history block
    rng=np.random.default_rng(737373)
    obs=float(df_summary.query("angle_deg==30").accuracy.mean() -
              df_summary.query("angle_deg==150").accuracy.mean())
    vals=np.asarray(df_summary.query("angle_deg==30").accuracy.tolist()+
                    df_summary.query("angle_deg==150").accuracy.tolist())
    # Paired sign-flip across history seeds.
    a=df_summary[df_summary.angle_deg==30].sort_values("heldout_history_seed").accuracy.to_numpy()
    b=df_summary[df_summary.angle_deg==150].sort_values("heldout_history_seed").accuracy.to_numpy()
    d=a-b
    null=np.empty(20000)
    for i in range(len(null)):
        null[i]=np.mean(d*rng.choice([-1.,1.],size=len(d)))
    p=float((1+np.sum(null>=obs))/(len(null)+1))
    return {
        "observed_accuracy_difference_30_minus_150":obs,
        "paired_null_mean":float(null.mean()),
        "paired_null_95th":float(np.quantile(null,.95)),
        "paired_signflip_p":p,
        "n_history_blocks":int(len(d))
    }

def main():
    raw=build_dataset()
    raw.to_csv(OUT/"reference_free_raw.csv",index=False)
    summary=fit_and_score(raw)
    summary.to_csv(OUT/"decoder_summary.csv",index=False)
    stats=summary.groupby("angle_deg",as_index=False).agg(
        mean_accuracy=("accuracy","mean"),
        sd_accuracy=("accuracy","std"),
        mean_log_loss=("log_loss","mean"),
        min_accuracy=("accuracy","min"),
        max_accuracy=("accuracy","max")
    )
    stats.to_csv(OUT/"angle_summary.csv",index=False)

    pivot=summary.pivot(index="heldout_history_seed",columns="angle_deg",values="accuracy").reset_index()
    pivot["gap_30_minus_150"]=pivot[30]-pivot[150]
    pivot.to_csv(OUT/"history_gaps.csv",index=False)

    null=permutation_test(summary)
    payload={
        "experiment":"state_geometry_reference_free_v37",
        "design":{
            "independent_history_seeds":list(HSEEDS),
            "six_blind_parameter_points":True,
            "history_pairs":4,
            "memory_values":MEMS,
            "pressure_values":PRESS,
            "angles_deg":ANGLES,
            "radius":RADIUS,
            "future_input":"exactly zero",
            "continuation_seeds":list(CSEEDS),
            "decoder":"standardized logistic regression trained on other history seeds only",
            "features":"12 fixed reference-free trajectory statistics",
            "primary":"held-out accuracy difference 30° minus 150°",
            "null":"paired sign flip across 10 held-out history-seed blocks"
        },
        "null":null
    }
    (OUT/"summary.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
    print(stats.to_string(index=False))
    print("\nNULL",json.dumps(null,indent=2))

if __name__=="__main__":
    main()
