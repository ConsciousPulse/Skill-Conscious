from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_cross_history_reference_v40")
OUT.mkdir(parents=True, exist_ok=True)

PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]

TEST_HSEEDS=range(150,160)
REF_HSEEDS=range(180,190)
CREF=range(10400,10405)
CTEST=range(11400,11405)
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
    c=dict(receiver)
    c["state_prev"]=receiver["state_prev"]+rd[0]
    c["state"]=receiver["state"]+rd[1]
    return c

def signature(run):
    return run["state"][::STRIDE].astype(float)

def score(sig,ra,rb):
    da=float(np.linalg.norm(sig-ra))
    db=float(np.linalg.norm(sig-rb))
    return float((db-da)/max(da+db,1e-12))

def main():
    rows=[]
    for pp in PARAMS:
        cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
        for pair in range(4):
            # References are built from an independent history seed of the same history-pair template.
            for hs_test, hs_ref in zip(TEST_HSEEDS,REF_HSEEDS):
                ua,ub=history(pair,hs_test)
                ra_hist,rb_hist=history(pair,hs_ref)

                ta=extract(cfg,hs_test,ua)
                tb=extract(cfg,hs_test,ub)
                rr_a=extract(cfg,hs_ref,ra_hist)
                rr_b=extract(cfg,hs_ref,rb_hist)

                test_receiver={k:(ta[k]+tb[k])/2 for k in ta}
                ref_receiver={k:(rr_a[k]+rr_b[k])/2 for k in rr_a}

                refs={}
                for dn,donor in [("A",rr_a),("B",rr_b)]:
                    st=transform(donor,ref_receiver,0)
                    refs[dn]=np.mean(np.stack([signature(cont(cfg,st,s)) for s in CREF]),axis=0)

                for mem in MEMS:
                    for pressure in PRESS:
                        rc=dict(test_receiver)
                        rc["memory"]=mem
                        rc["pressure"]=pressure
                        for angle in ANGLES:
                            for donor,label in [(ta,"A"),(tb,"B")]:
                                expected=1 if label=="A" else -1
                                st=transform(donor,rc,angle)
                                for cs in CTEST:
                                    sig=signature(cont(cfg,st,cs+hs_test))
                                    rows.append({
                                        "param":pp["name"],"pair":pair,
                                        "test_history_seed":hs_test,"ref_history_seed":hs_ref,
                                        "memory":mem,"pressure":pressure,"angle_deg":angle,
                                        "donor":label,
                                        "signed_affinity":expected*score(sig,refs["A"],refs["B"])
                                    })

    raw=pd.DataFrame(rows)
    raw.to_csv(OUT/"raw.csv",index=False)

    cell=(raw.groupby(["param","pair","test_history_seed","memory","pressure","angle_deg"],as_index=False)
          .agg(signed_affinity=("signed_affinity","mean")))
    a=cell[cell.angle_deg==30].drop(columns="angle_deg").rename(columns={"signed_affinity":"affinity_30"})
    b=cell[cell.angle_deg==150].drop(columns="angle_deg").rename(columns={"signed_affinity":"affinity_150"})
    wide=a.merge(b,on=["param","pair","test_history_seed","memory","pressure"],how="inner")
    wide["contrast_30_150"]=wide["affinity_30"]-wide["affinity_150"]
    wide.to_csv(OUT/"paired_metrics.csv",index=False)

    block=(wide.groupby(["pair","test_history_seed"],as_index=False)
           .agg(contrast_30_150=("contrast_30_150","mean")))

    rng=np.random.default_rng(104040)
    mat=block.pivot(index="pair",columns="test_history_seed",values="contrast_30_150").to_numpy()
    obs=float(mat.mean())
    null=np.mean(rng.choice([-1.,1.],size=(N_PERM,)+mat.shape)*mat[None,:,:],axis=(1,2))
    p=float((1+np.sum(null>=obs))/(N_PERM+1))
    boot=np.empty(N_BOOT)
    for i in range(N_BOOT):
        vals=[]
        for row in mat:
            idx=rng.integers(0,len(row),size=len(row))
            vals.extend(row[idx])
        boot[i]=np.mean(vals)

    summary={
        "observed_mean_contrast_30_minus_150":obs,
        "null_mean":float(null.mean()),
        "null_95th":float(np.quantile(null,.95)),
        "permutation_p":p,
        "bootstrap_95_low":float(np.quantile(boot,.025)),
        "bootstrap_95_high":float(np.quantile(boot,.975)),
        "history_seed_blocks":int(len(block)),
        "history_pair_strata":4
    }
    pd.DataFrame([summary]).to_csv(OUT/"summary.csv",index=False)

    ctx=(wide.groupby(["memory","pressure"],as_index=False)
         .agg(mean_contrast=("contrast_30_150","mean")))
    ctx.to_csv(OUT/"context_summary.csv",index=False)

    (OUT/"summary.json").write_text(json.dumps({
        "experiment":"state_geometry_cross_history_reference_v40",
        "design":{
            "test_history_seeds":list(TEST_HSEEDS),
            "reference_history_seeds":list(REF_HSEEDS),
            "blind_parameter_points":6,
            "history_pairs":4,
            "memory_values":MEMS,
            "pressure_values":PRESS,
            "angles_deg":ANGLES,
            "radius":RADIUS,
            "future_input":"exactly zero",
            "reference_noise_seeds":list(CREF),
            "test_noise_seeds":list(CTEST),
            "primary":"30° minus 150° signed-affinity using references generated from a disjoint history seed",
            "null":"history-seed block sign flip stratified by history pair",
            "bootstrap":"history-seed block resampling within pair strata"
        },
        "summary":summary
    },indent=2),encoding="utf-8")
    print(pd.DataFrame([summary]).to_string(index=False))

if __name__=="__main__":
    main()
