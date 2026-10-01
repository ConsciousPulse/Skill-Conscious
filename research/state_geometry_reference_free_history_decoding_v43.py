from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import confusion_matrix
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_reference_free_history_decoding_v43")
OUT.mkdir(parents=True, exist_ok=True)

PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
HSEEDS=range(300,310)
N=300
FUTURE=60
STRIDE=5
TEST_NOISE=range(17400,17405)

def history(pair,seed,n=N):
    rng=np.random.default_rng(seed+1000*pair)
    if pair==0:
        return np.ones(n),-np.ones(n)
    if pair==1:
        return np.where(np.arange(n)%2==0,1.,-1.),np.ones(n)
    if pair==2:
        return np.where(rng.random(n)<.12,-1.,1.),np.where(rng.random(n)<.06,1.,-1.)
    return np.sign(np.sin(np.linspace(0,18*np.pi,n))),np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))

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
        np.zeros(FUTURE),
        cfg,
        seed=seed,
        initial_prev_state=ctx["state_prev"],
        initial_state=ctx["state"],
        initial_memory=ctx["memory"],
        initial_pressure=ctx["pressure"],
    )

def feat(run,kind):
    s=run["state"][::STRIDE].astype(float)
    m=run["memory"][::STRIDE].astype(float)
    p=run["pressure"][::STRIDE].astype(float)
    if kind=="state":
        return s
    if kind=="state_norm":
        return s/max(np.linalg.norm(s),1e-12)
    if kind=="memory":
        return m
    if kind=="pressure":
        return p
    if kind=="joint_norm":
        z=np.concatenate([s,m,p])
        return z/max(np.linalg.norm(z),1e-12)
    raise ValueError(kind)

def make_dataset_kind(kind):
    X=[]; y=[]; meta=[]
    for pi,pp in enumerate(PARAMS):
        cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
        for pair in range(4):
            for hs in HSEEDS:
                ua,ub=history(pair,hs)
                a=extract(cfg,hs,ua)
                b=extract(cfg,hs,ub)
                rec={k:(a[k]+b[k])/2 for k in a}
                for j,cs in enumerate(TEST_NOISE):
                    run=cont(cfg,rec,cs+hs)
                    X.append(feat(run,kind))
                    y.append(pair)
                    meta.append((pi,pp["name"],pair,hs,j))
    return np.asarray(X),np.asarray(y),meta

def fit_eval(Xtr,ytr,Xte,yte):
    model=Pipeline([
        ("scale",StandardScaler()),
        ("clf",LogisticRegression(max_iter=3000,random_state=0)),
    ])
    model.fit(Xtr,ytr)
    pred=model.predict(Xte)
    return float(np.mean(pred==yte)),pred

def main():
    kinds=["state","state_norm","memory","pressure","joint_norm"]
    rows=[]
    predictions={}

    for kind in kinds:
        X,y,meta=make_dataset_kind(kind)
        meta=np.asarray(meta,dtype=object)
        lopo=[]
        cms=np.zeros((4,4),dtype=int)

        for pi in range(len(PARAMS)):
            train=meta[:,0]!=pi
            test=meta[:,0]==pi
            acc,pred=fit_eval(X[train],y[train],X[test],y[test])
            cms += confusion_matrix(y[test],pred,labels=[0,1,2,3])
            lopo.append(acc)
            predictions.setdefault(kind,[]).append((y[test].copy(),pred))

        rows.append({
            "feature_set":kind,
            "lopo_mean_accuracy":float(np.mean(lopo)),
            "lopo_sd":float(np.std(lopo,ddof=1)),
            "fold_accuracies":lopo,
            "confusion_matrix":cms.tolist(),
        })

    rng=np.random.default_rng(430043)
    obs=rows[-1]["lopo_mean_accuracy"]
    null=np.empty(5000)

    for b in range(len(null)):
        vals=[]
        for yy,pred in predictions["joint_norm"]:
            yy=yy.copy()
            rng.shuffle(yy)
            vals.append(float(np.mean(pred==yy)))
        null[b]=np.mean(vals)

    summary={
        "experiment":"state_geometry_reference_free_history_decoding_v43",
        "classes":4,
        "chance_accuracy":0.25,
        "future_input":"exactly zero",
        "reference_free":True,
        "feature_results":rows,
        "joint_norm_permutation_null_mean":float(null.mean()),
        "joint_norm_permutation_null_95":float(np.quantile(null,.95)),
        "joint_norm_permutation_p":float((1+np.sum(null>=obs))/(len(null)+1)),
        "protocol_note":"LOPO across six blind parameter points; ten disjoint history seeds per class/parameter; five independent continuation noise seeds; no angular transform and no reference trajectory.",
    }

    pd.DataFrame([
        {k:v for k,v in r.items() if k not in ("fold_accuracies","confusion_matrix")}
        for r in rows
    ]).to_csv(OUT/"lopo_feature_summary.csv",index=False)

    for r in rows:
        pd.DataFrame(
            r["confusion_matrix"],
            index=["true0","true1","true2","true3"],
            columns=["pred0","pred1","pred2","pred3"],
        ).to_csv(OUT/f"confusion_{r['feature_set']}.csv")

    (OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
