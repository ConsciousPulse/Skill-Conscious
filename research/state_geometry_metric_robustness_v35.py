from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_metric_robustness_v35")
OUT.mkdir(parents=True, exist_ok=True)

PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]

HSEEDS=range(100,110)
CREF=range(3400,3405)
CTEST=range(4400,4405)
N=300
FUTURE=60
RADIUS=1.1
STRIDE=5
MEMS=[-0.8,0.0,0.8]
PRESS=[0.0,1.0,2.0]
ANGLE_A=30
ANGLE_B=150
N_PERM=20000
N_BOOT=10000

def history(pair, seed, n=N):
    rng=np.random.default_rng(seed+1000*pair)
    if pair==0:
        return np.ones(n), -np.ones(n)
    if pair==1:
        return np.where(np.arange(n)%2==0,1.,-1.), np.ones(n)
    if pair==2:
        return (
            np.where(rng.random(n)<.12,-1.,1.),
            np.where(rng.random(n)<.06,1.,-1.)
        )
    return (
        np.sign(np.sin(np.linspace(0,18*np.pi,n))),
        np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))
    )

def extract(cfg, seed, u):
    r=simulate(np.r_[u,np.zeros(FUTURE)],cfg,seed=seed)
    i=N
    return {
        "state_prev":float(r["state"][i-2]),
        "state":float(r["state"][i-1]),
        "memory":float(r["memory"][i-1]),
        "pressure":float(r["pressure"][i-1]),
    }

def cont(cfg, ctx, seed):
    return simulate(
        np.zeros(FUTURE), cfg, seed=seed,
        initial_prev_state=ctx["state_prev"],
        initial_state=ctx["state"],
        initial_memory=ctx["memory"],
        initial_pressure=ctx["pressure"],
    )

def transform(donor, receiver, angle):
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

def signature(run):
    return run["state"][::STRIDE].astype(float)

def metrics(sig, ra, rb):
    da=float(np.linalg.norm(sig-ra))
    db=float(np.linalg.norm(sig-rb))
    signed_aff=(db-da)/max(da+db,1e-12)
    margin=db-da
    # Cosine delta is an independent geometric readout.
    ns=float(np.linalg.norm(sig))
    na=float(np.linalg.norm(ra))
    nb=float(np.linalg.norm(rb))
    if ns<1e-12 or na<1e-12 or nb<1e-12:
        cosine_delta=0.0
    else:
        cosine_delta=float(np.dot(sig,ra)/(ns*na)-np.dot(sig,rb)/(ns*nb))
    # Correct-direction sign for every metric: positive means closer/more aligned
    # to the donor-consistent reference.
    return {
        "signed_affinity":signed_aff,
        "distance_margin":margin,
        "cosine_delta":cosine_delta,
    }

def evaluate_blocks(cell, metric):
    block=(
        cell.groupby(["pair","history_seed"],as_index=False)
        .agg(value=(metric,"mean"))
    )
    observed=float(block["value"].mean())
    rng=np.random.default_rng(525252)
    null=np.empty(N_PERM)
    for i in range(N_PERM):
        vals=[]
        for _,g in block.groupby("pair"):
            x=g["value"].to_numpy()
            vals.extend(x*rng.choice([-1.0,1.0],size=len(x)))
        null[i]=np.mean(vals)
    p=float((1+np.sum(null>=observed))/(N_PERM+1))

    groups={pair:g["value"].to_numpy() for pair,g in block.groupby("pair")}
    boot=np.empty(N_BOOT)
    for i in range(N_BOOT):
        vals=[]
        for x in groups.values():
            idx=rng.integers(0,len(x),size=len(x))
            vals.extend(x[idx])
        boot[i]=np.mean(vals)

    return {
        "metric":metric,
        "observed_mean_30_minus_150":observed,
        "null_mean":float(null.mean()),
        "null_95th":float(np.quantile(null,0.95)),
        "permutation_p":p,
        "bootstrap_95_low":float(np.quantile(boot,0.025)),
        "bootstrap_95_high":float(np.quantile(boot,0.975)),
        "history_seed_blocks":int(len(block)),
        "history_pair_strata":4,
    }

def main():
    rows=[]
    for pp in PARAMS:
        cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
        for pair in range(4):
            ua,ub=history(pair,hs:=next(iter(HSEEDS)))
            # hs above is overwritten below only to keep lint/simple-path compatibility.
            for hs in HSEEDS:
                ua,ub=history(pair,hs)
                a=extract(cfg,hs,ua)
                b=extract(cfg,hs,ub)
                receiver={k:(a[k]+b[k])/2 for k in a}
                refs={}
                for dn,donor in [("A",a),("B",b)]:
                    st=transform(donor,receiver,0)
                    sigs=[signature(cont(cfg,st,s)) for s in CREF]
                    refs[dn]=np.mean(np.stack(sigs),axis=0)

                for mem in MEMS:
                    for pressure in PRESS:
                        rc=dict(receiver)
                        rc["memory"]=mem
                        rc["pressure"]=pressure
                        for angle in [ANGLE_A,ANGLE_B]:
                            for dn,donor in [("A",a),("B",b)]:
                                expected=1 if dn=="A" else -1
                                st=transform(donor,rc,angle)
                                for cs in CTEST:
                                    sig=signature(cont(cfg,st,cs+hs))
                                    mm=metrics(sig,refs["A"],refs["B"])
                                    for k,v in mm.items():
                                        mm[k]=expected*v
                                    rows.append({
                                        "param":pp["name"],"pair":pair,
                                        "history_seed":hs,"memory":mem,
                                        "pressure":pressure,"angle_deg":angle,
                                        "donor":dn,
                                        **mm,
                                    })

    raw=pd.DataFrame(rows)
    raw.to_csv(OUT/"raw.csv",index=False)

    cell=(
        raw.groupby(["param","pair","history_seed","memory","pressure","angle_deg"],as_index=False)
        .agg(
            signed_affinity=("signed_affinity","mean"),
            distance_margin=("distance_margin","mean"),
            cosine_delta=("cosine_delta","mean"),
        )
    )
    cell.to_csv(OUT/"paired_context_cells.csv",index=False)

    a=cell[cell.angle_deg==ANGLE_A].drop(columns=["angle_deg"]).rename(
        columns={
            "signed_affinity":"signed_affinity_30",
            "distance_margin":"distance_margin_30",
            "cosine_delta":"cosine_delta_30",
        }
    )
    b=cell[cell.angle_deg==ANGLE_B].drop(columns=["angle_deg"]).rename(
        columns={
            "signed_affinity":"signed_affinity_150",
            "distance_margin":"distance_margin_150",
            "cosine_delta":"cosine_delta_150",
        }
    )
    wide=a.merge(
        b,on=["param","pair","history_seed","memory","pressure"],how="inner"
    )
    for m in ["signed_affinity","distance_margin","cosine_delta"]:
        wide[m+"_contrast_30_150"]=wide[m+"_30"]-wide[m+"_150"]
    wide.to_csv(OUT/"paired_metrics.csv",index=False)

    summaries=[]
    for m in ["signed_affinity","distance_margin","cosine_delta"]:
        summaries.append(
            evaluate_blocks(
                wide[["pair","history_seed",f"{m}_contrast_30_150"]].rename(
                    columns={f"{m}_contrast_30_150":m}
                ),
                m,
            )
        )
    summary_df=pd.DataFrame(summaries)
    summary_df.to_csv(OUT/"metric_summary.csv",index=False)

    payload={
        "experiment":"state_geometry_metric_robustness_v35",
        "design":{
            "independent_history_seeds":list(HSEEDS),
            "blind_parameter_points":6,
            "history_pairs":4,
            "memory_values":MEMS,
            "pressure_values":PRESS,
            "angles_deg":[ANGLE_A,ANGLE_B],
            "radius":RADIUS,
            "future_input":"exactly zero",
            "reference_noise_seeds":list(CREF),
            "test_noise_seeds":list(CTEST),
            "primary":"30° minus 150° contrast at history-seed block level",
            "metrics":["signed_affinity","distance_margin","cosine_delta"],
            "null":"stratified sign flip within each history-pair stratum",
            "bootstrap":"stratified resampling of history-seed blocks"
        }
    }
    (OUT/"summary.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
    print(summary_df.to_string(index=False))

if __name__=="__main__":
    main()
