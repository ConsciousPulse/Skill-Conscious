from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_loso_v36")
OUT.mkdir(parents=True, exist_ok=True)

PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]

HSEEDS=range(110,120)
CREF=range(5400,5405)
CTEST=range(6400,6405)
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
    if pair==0:
        return np.ones(n),-np.ones(n)
    if pair==1:
        return np.where(np.arange(n)%2==0,1.,-1.),np.ones(n)
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
        donor["state"]-receiver["state"]
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

def metrics(sig,ra,rb):
    da=float(np.linalg.norm(sig-ra))
    db=float(np.linalg.norm(sig-rb))
    signed=(db-da)/max(da+db,1e-12)
    margin=db-da
    ns=float(np.linalg.norm(sig))
    na=float(np.linalg.norm(ra))
    nb=float(np.linalg.norm(rb))
    cosine=0.0 if min(ns,na,nb)<1e-12 else float(
        np.dot(sig,ra)/(ns*na)-np.dot(sig,rb)/(ns*nb)
    )
    return signed,margin,cosine

def stratified_null(block,metric,exclude_pair=None):
    if exclude_pair is not None:
        block=block[block.pair!=exclude_pair].copy()
    mat=block.pivot(index="pair",columns="history_seed",values=metric).to_numpy()
    obs=float(mat.mean())
    rng=np.random.default_rng(736273)
    signs=rng.choice(np.array([-1.,1.]),size=(N_PERM,)+mat.shape)
    null=(signs*mat[None,:,:]).reshape(N_PERM,-1).mean(axis=1)
    p=float((1+np.sum(null>=obs))/(N_PERM+1))
    boot=np.empty(N_BOOT)
    for i in range(N_BOOT):
        sampled_rows=[]
        for row in mat:
            idx=rng.integers(0,len(row),size=len(row))
            sampled_rows.extend(row[idx])
        boot[i]=float(np.mean(sampled_rows))
    return obs,float(null.mean()),float(np.quantile(null,.95)),p,float(np.quantile(boot,.025)),float(np.quantile(boot,.975)),int(mat.size)

def main():
    rows=[]
    for pp in PARAMS:
        cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
        for pair in range(4):
            for hs in HSEEDS:
                ua,ub=history(pair,hs)
                a=extract(cfg,hs,ua)
                b=extract(cfg,hs,ub)
                receiver={k:(a[k]+b[k])/2 for k in a}
                refs={}
                for dn,donor in [("A",a),("B",b)]:
                    st=transform(donor,receiver,0)
                    refs[dn]=np.mean(np.stack([signature(cont(cfg,st,s)) for s in CREF]),axis=0)
                for mem in MEMS:
                    for pressure in PRESS:
                        rc=dict(receiver)
                        rc["memory"]=mem
                        rc["pressure"]=pressure
                        for angle in ANGLES:
                            acc=np.zeros(3)
                            count=0
                            for dn,donor in [("A",a),("B",b)]:
                                expected=1 if dn=="A" else -1
                                st=transform(donor,rc,angle)
                                for cs in CTEST:
                                    sig=signature(cont(cfg,st,cs+hs))
                                    acc += expected*np.asarray(metrics(sig,refs["A"],refs["B"]))
                                    count += 1
                            vals=acc/count
                            rows.append([pp["name"],pair,hs,mem,pressure,angle,*vals])

    cell=pd.DataFrame(rows,columns=[
        "param","pair","history_seed","memory","pressure","angle_deg",
        "signed_affinity","distance_margin","cosine_delta"
    ])
    a=cell[cell.angle_deg==30].drop(columns="angle_deg").rename(columns={
        "signed_affinity":"signed_affinity_30",
        "distance_margin":"distance_margin_30",
        "cosine_delta":"cosine_delta_30"
    })
    b=cell[cell.angle_deg==150].drop(columns="angle_deg").rename(columns={
        "signed_affinity":"signed_affinity_150",
        "distance_margin":"distance_margin_150",
        "cosine_delta":"cosine_delta_150"
    })
    wide=a.merge(b,on=["param","pair","history_seed","memory","pressure"])
    for m in ["signed_affinity","distance_margin","cosine_delta"]:
        wide[m+"_contrast_30_150"]=wide[m+"_30"]-wide[m+"_150"]
    block=wide.groupby(["pair","history_seed"],as_index=False)[
        ["signed_affinity_contrast_30_150","distance_margin_contrast_30_150","cosine_delta_contrast_30_150"]
    ].mean()

    summaries=[]
    for metric in [
        "signed_affinity_contrast_30_150",
        "distance_margin_contrast_30_150",
        "cosine_delta_contrast_30_150"
    ]:
        full=stratified_null(block.rename(columns={metric:"value"})[["pair","history_seed","value"]],"value")
        summaries.append(["full",metric,*full])
        for heldout in range(4):
            res=stratified_null(block.rename(columns={metric:"value"})[["pair","history_seed","value"]],"value",exclude_pair=heldout)
            summaries.append([f"leave_out_pair_{heldout}",metric,*res])

    summary=pd.DataFrame(summaries,columns=[
        "analysis","metric","observed_mean","null_mean","null_95th",
        "permutation_p","bootstrap_95_low","bootstrap_95_high","history_seed_blocks"
    ])

    context=wide.groupby(["memory","pressure"],as_index=False)[
        ["signed_affinity_contrast_30_150","distance_margin_contrast_30_150","cosine_delta_contrast_30_150"]
    ].mean()

    cell.to_csv(OUT/"paired_context_cells.csv",index=False)
    wide.to_csv(OUT/"paired_metrics.csv",index=False)
    block.to_csv(OUT/"history_blocks.csv",index=False)
    summary.to_csv(OUT/"loso_summary.csv",index=False)
    context.to_csv(OUT/"context_summary.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps({
        "experiment":"state_geometry_loso_v36",
        "design":{
            "independent_history_seeds":list(HSEEDS),
            "blind_parameter_points":6,
            "history_pairs":4,
            "memory_values":MEMS,
            "pressure_values":PRESS,
            "angles_deg":ANGLES,
            "radius":RADIUS,
            "future_input":"exactly zero",
            "reference_noise_seeds":list(CREF),
            "test_noise_seeds":list(CTEST),
            "primary":"30° minus 150° at history-seed block level",
            "leave_one_history_pair_out":True,
            "null":"stratified sign flip by remaining history-pair strata"
        }
    },indent=2),encoding="utf-8")
    print(summary.to_string(index=False))

if __name__=="__main__":
    main()
