from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_reference_compatibility_v42")
OUT.mkdir(parents=True, exist_ok=True)

PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
TEST_HSEEDS=range(200,210)
REF_HSEEDS=range(230,240)
CREF=range(15400,15405)
CTEST=range(16400,16405)
N=300
FUTURE=60
RADIUS=1.1
STRIDE=5
MEMS=[-0.8,0.0,0.8]
PRESS=[0.0,1.0,2.0]
ANGLES=[30,150]
N_PERM=20000
N_BOOT=10000

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

def signature(run):
    return run["state"][::STRIDE].astype(float)

def score(sig,ra,rb):
    da=float(np.linalg.norm(sig-ra)); db=float(np.linalg.norm(sig-rb))
    return float((db-da)/max(da+db,1e-12))

def main():
    # Precompute reference ensembles by reference-pair, parameter, and reference history seed.
    refs={}
    for pp in PARAMS:
        cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
        for rp in range(4):
            for hrs in REF_HSEEDS:
                ua,ub=history(rp,hrs)
                a=extract(cfg,hrs,ua); b=extract(cfg,hrs,ub)
                receiver={k:(a[k]+b[k])/2 for k in a}
                cur={}
                for dn,donor in [("A",a),("B",b)]:
                    st=transform(donor,receiver,0)
                    cur[dn]=np.mean(np.stack([signature(cont(cfg,st,s)) for s in CREF]),axis=0)
                refs[(pp["name"],rp,hrs)]=cur

    rows=[]
    for pp in PARAMS:
        cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
        for tp in range(4):
            for hts in TEST_HSEEDS:
                ua,ub=history(tp,hts)
                ta=extract(cfg,hts,ua); tb=extract(cfg,hts,ub)
                test_receiver={k:(ta[k]+tb[k])/2 for k in ta}
                for rp in range(4):
                    hrs=REF_HSEEDS[list(TEST_HSEEDS).index(hts)]
                    rr=refs[(pp["name"],rp,hrs)]
                    for mem in MEMS:
                        for pressure in PRESS:
                            rc=dict(test_receiver); rc["memory"]=mem; rc["pressure"]=pressure
                            for angle in ANGLES:
                                acc=0.0; count=0
                                for donor,label in [(ta,"A"),(tb,"B")]:
                                    expected=1 if label=="A" else -1
                                    st=transform(donor,rc,angle)
                                    for cs in CTEST:
                                        sig=signature(cont(cfg,st,cs+hts))
                                        acc += expected*score(sig,rr["A"],rr["B"])
                                        count += 1
                                rows.append({
                                    "param":pp["name"],"test_pair":tp,"reference_pair":rp,
                                    "test_history_seed":hts,"reference_history_seed":hrs,
                                    "memory":mem,"pressure":pressure,"angle_deg":angle,
                                    "signed_affinity":acc/count
                                })

    raw=pd.DataFrame(rows)
    raw.to_csv(OUT/"raw.csv",index=False)
    cell=(raw.groupby(["param","test_pair","reference_pair","test_history_seed","memory","pressure","angle_deg"],as_index=False)
          .agg(signed_affinity=("signed_affinity","mean")))
    a=cell[cell.angle_deg==30].drop(columns="angle_deg").rename(columns={"signed_affinity":"affinity_30"})
    b=cell[cell.angle_deg==150].drop(columns="angle_deg").rename(columns={"signed_affinity":"affinity_150"})
    wide=a.merge(b,on=["param","test_pair","reference_pair","test_history_seed","memory","pressure"])
    wide["contrast_30_150"]=wide["affinity_30"]-wide["affinity_150"]
    wide["same_pair"]=(wide.test_pair==wide.reference_pair)
    wide.to_csv(OUT/"paired_metrics.csv",index=False)

    matrix=wide.groupby(["test_pair","reference_pair"],as_index=False).agg(
        mean_contrast=("contrast_30_150","mean"),
        sd_contrast=("contrast_30_150","std"),
        positive_fraction=("contrast_30_150",lambda x: float(np.mean(x>0)))
    )
    matrix.to_csv(OUT/"compatibility_matrix.csv",index=False)

    block=wide.groupby(["test_pair","test_history_seed"],as_index=False).agg(
        same_pair_contrast=("contrast_30_150",lambda x: float(x[x.index.map(lambda i: True)].mean()))
    )
    # Better block-level same-vs-different statistic using matrix cells in each test block.
    # For every test history seed, compare matched same-pair reference cell against the mean of the three other reference-pair cells.
    per=wide.groupby(["test_pair","test_history_seed","reference_pair"],as_index=False).agg(value=("contrast_30_150","mean"))
    piv=per.pivot(index=["test_pair","test_history_seed"],columns="reference_pair",values="value").reset_index()
    diffs=[]
    for _,row in piv.iterrows():
        tp=int(row["test_pair"])
        same=float(row[tp])
        others=[float(row[r]) for r in range(4) if r!=tp]
        diffs.append({"test_pair":tp,"test_history_seed":int(row["test_history_seed"]),
                      "same_minus_other_mean":same-float(np.mean(others)),
                      "same_value":same,"other_mean":float(np.mean(others))})
    diffs=pd.DataFrame(diffs)
    diffs.to_csv(OUT/"same_vs_other_blocks.csv",index=False)

    obs=float(diffs.same_minus_other_mean.mean())
    rng=np.random.default_rng(242424)
    x=diffs.same_minus_other_mean.to_numpy()
    null=np.mean(rng.choice([-1.,1.],size=(N_PERM,len(x)))*x[None,:],axis=1)
    p=float((1+np.sum(null>=obs))/(N_PERM+1))
    boot=np.empty(N_BOOT)
    for i in range(N_BOOT):
        vals=[]
        for tp,g in diffs.groupby("test_pair"):
            arr=g.same_minus_other_mean.to_numpy()
            idx=rng.integers(0,len(arr),size=len(arr))
            vals.extend(arr[idx])
        boot[i]=np.mean(vals)
    summary={
        "same_minus_other_mean_observed":obs,
        "null_mean":float(null.mean()),
        "null_95th":float(np.quantile(null,.95)),
        "permutation_p":p,
        "bootstrap_95_low":float(np.quantile(boot,.025)),
        "bootstrap_95_high":float(np.quantile(boot,.975)),
        "history_seed_blocks":int(len(x)),
        "history_pair_strata":4
    }
    pd.DataFrame([summary]).to_csv(OUT/"same_vs_other_summary.csv",index=False)

    (OUT/"summary.json").write_text(json.dumps({
        "experiment":"state_geometry_reference_compatibility_v42",
        "design":{
            "test_history_seeds":list(TEST_HSEEDS),
            "reference_history_seeds":list(REF_HSEEDS),
            "all_4x4_pair_mappings":True,
            "blind_parameter_points":6,"memory_values":MEMS,"pressure_values":PRESS,
            "angles_deg":ANGLES,"radius":RADIUS,"future_input":"exactly zero",
            "reference_noise_seeds":list(CREF),"test_noise_seeds":list(CTEST),
            "primary":"same-pair reference contrast minus mean contrast from the three other reference-pair templates",
            "null":"paired sign flip across test history-seed blocks",
            "bootstrap":"stratified by test-pair"
        },
        "summary":summary
    },indent=2),encoding="utf-8")
    print("MATRIX")
    print(matrix.to_string(index=False))
    print("\nSAME VS OTHER")
    print(pd.DataFrame([summary]).to_string(index=False))

if __name__=="__main__":
    main()
