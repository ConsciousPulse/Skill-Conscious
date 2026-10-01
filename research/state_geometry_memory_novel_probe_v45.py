from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_memory_novel_probe_v45")
OUT.mkdir(parents=True,exist_ok=True)

PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
HSEEDS=range(600,610)
DONOR_SEEDS=range(700,701)
TEST_NOISE=range(19400,19402)
N=300
FUTURE=60
STRIDE=5
PROBE=np.r_[np.ones(10),-np.ones(10),np.zeros(10),0.5*np.ones(10),-0.5*np.ones(10),np.zeros(10)]

def history(pair,seed,n=N):
    rng=np.random.default_rng(seed+1000*pair)
    if pair==0: return np.ones(n),-np.ones(n)
    if pair==1: return np.where(np.arange(n)%2==0,1.,-1.),np.ones(n)
    if pair==2: return np.where(rng.random(n)<.12,-1.,1.),np.where(rng.random(n)<.06,1.,-1.)
    return np.sign(np.sin(np.linspace(0,18*np.pi,n))),np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))

def extract(cfg,seed,u):
    r=simulate(np.r_[u,np.zeros(FUTURE)],cfg,seed=seed)
    i=N
    return {"state_prev":float(r["state"][i-2]),"state":float(r["state"][i-1]),"memory":float(r["memory"][i-1]),"pressure":float(r["pressure"][i-1])}

def cont_probe(cfg,ctx,seed):
    return simulate(PROBE,cfg,seed=seed,initial_prev_state=ctx["state_prev"],initial_state=ctx["state"],initial_memory=ctx["memory"],initial_pressure=ctx["pressure"])

def state_feat(run):
    s=run["state"][::STRIDE].astype(float)
    return s/max(np.linalg.norm(s),1e-12)

def fit_model(X,y):
    model=Pipeline([("scale",StandardScaler()),("clf",LogisticRegression(max_iter=2000,random_state=0))])
    model.fit(X,y)
    return model

def precompute():
    out={}
    for pi,pp in enumerate(PARAMS):
        cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
        recs={}; donors={}
        for pair in range(4):
            recs[pair]=[]
            for hs in HSEEDS:
                ua,ub=history(pair,hs)
                a=extract(cfg,hs,ua); b=extract(cfg,hs,ub)
                recs[pair].append({"history_seed":hs,"ctx":{k:(a[k]+b[k])/2 for k in a}})
        for pair in range(4):
            donors[pair]=[]
            for ds in DONOR_SEEDS:
                du,dv=history(pair,ds)
                da=extract(cfg,ds,du); db=extract(cfg,ds,dv)
                donors[pair].append({"history_seed":ds,"memory":(da["memory"]+db["memory"])/2,"pressure":(da["pressure"]+db["pressure"])/2,"state_prev":(da["state_prev"]+db["state_prev"])/2,"state":(da["state"]+db["state"])/2})
        out[pi]={"cfg":cfg,"recs":recs,"donors":donors}
    return out

def training_data(cache,held_out):
    X=[]; y=[]
    for pi,dat in cache.items():
        if pi==held_out: continue
        for pair in range(4):
            for item in dat["recs"][pair]:
                for cs in TEST_NOISE:
                    X.append(state_feat(cont_probe(dat["cfg"],item["ctx"],cs+item["history_seed"])))
                    y.append(pair)
    return np.asarray(X),np.asarray(y)

def main():
    cache=precompute()
    rows=[]; clean_folds=[]
    for pi,pp in enumerate(PARAMS):
        Xtr,ytr=training_data(cache,pi)
        model=fit_model(Xtr,ytr)
        dat=cache[pi]
        yy=[]; pred=[]
        for pair in range(4):
            for item in dat["recs"][pair]:
                for cs in TEST_NOISE:
                    yy.append(pair)
                    pred.append(int(model.predict(state_feat(cont_probe(dat["cfg"],item["ctx"],cs+item["history_seed"])).reshape(1,-1))[0]))
        clean_folds.append(float(np.mean(np.asarray(yy)==np.asarray(pred))))

        for receiver in range(4):
            for item in dat["recs"][receiver]:
                hs=item["history_seed"]; base=item["ctx"]
                for donor in range(4):
                    if donor==receiver: continue
                    d=dat["donors"][donor][0]
                    for cs in TEST_NOISE:
                        seed=cs+hs+donor*10000
                        variants={"intact":base,"memory_swap":dict(base,memory=d["memory"]),"pressure_swap":dict(base,pressure=d["pressure"]),"state_swap":dict(base,state_prev=d["state_prev"],state=d["state"])}
                        for intervention,ctx in variants.items():
                            probs=model.predict_proba(state_feat(cont_probe(dat["cfg"],ctx,seed)).reshape(1,-1))[0]
                            rows.append({"param":pp["name"],"test_pair":receiver,"test_history_seed":hs,"donor_pair":donor,"donor_history_seed":d["history_seed"],"noise_seed":cs,"intervention":intervention,"p_receiver":float(probs[receiver]),"p_donor":float(probs[donor]),"pull":float(probs[donor]-probs[receiver])})

    raw=pd.DataFrame(rows)
    raw.to_csv(OUT/"raw.csv",index=False)
    wide=raw.pivot_table(index=["param","test_pair","test_history_seed","donor_pair","donor_history_seed","noise_seed"],columns="intervention",values="pull").reset_index()
    wide["memory_delta"]=wide["memory_swap"]-wide["intact"]
    wide["pressure_delta"]=wide["pressure_swap"]-wide["intact"]
    wide["state_delta"]=wide["state_swap"]-wide["intact"]
    x=wide["memory_delta"].to_numpy(); obs=float(x.mean())
    rng=np.random.default_rng(450045)
    null=np.mean(rng.choice([-1.,1.],size=(10000,len(x)))*x[None,:],axis=1)
    p=float((1+np.sum(null>=obs))/10001)
    boot=np.empty(10000)
    for i in range(len(boot)):
        vals=[]
        for tp,g in wide.groupby("test_pair"):
            arr=g["memory_delta"].to_numpy()
            vals.extend(arr[rng.integers(0,len(arr),size=len(arr))])
        boot[i]=np.mean(vals)
    summary={
        "experiment":"state_geometry_memory_novel_probe_v45",
        "reference_free":True,
        "probe_fixed_for_all_histories":True,
        "decoder_input":"future state trajectory only",
        "future_input":"same deterministic novel probe for every history class",
        "clean_lopo_mean_accuracy":float(np.mean(clean_folds)),
        "clean_lopo_sd":float(np.std(clean_folds,ddof=1)),
        "primary_memory_delta_pull":obs,
        "null_mean":float(null.mean()),
        "null_95th":float(np.quantile(null,.95)),
        "permutation_p":p,
        "bootstrap_95_low":float(np.quantile(boot,.025)),
        "bootstrap_95_high":float(np.quantile(boot,.975)),
        "primary_blocks":int(len(x)),
        "positive_fraction_memory_delta":float(np.mean(x>0)),
        "mean_deltas_vs_intact":{"memory_swap":float(wide.memory_delta.mean()),"pressure_swap":float(wide.pressure_delta.mean()),"state_swap":float(wide.state_delta.mean())},
        "protocol_note":"Same novel external probe is applied after each history. Only the internal starting context is intervened. The decoder sees only the resulting future state trajectory.",
    }
    pd.DataFrame([summary]).to_csv(OUT/"summary.csv",index=False)
    wide.to_csv(OUT/"primary_blocks.csv",index=False)
    pd.DataFrame({"fold":range(len(clean_folds)),"param":[p["name"] for p in PARAMS],"accuracy":clean_folds}).to_csv(OUT/"clean_lopo_folds.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
