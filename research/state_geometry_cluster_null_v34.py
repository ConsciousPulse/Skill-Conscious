from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_cluster_null_v34"); OUT.mkdir(parents=True, exist_ok=True)

PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]

HSEEDS=range(90,100)
CREF=range(1400,1405)
CTEST=range(2400,2405)
N=300; FUTURE=60; RADIUS=1.1; STRIDE=5
MEMS=[-0.8,0.0,0.8]
PRESS=[0.0,1.0,2.0]
ANGLES=[30,60,90,120,150]
N_PERM=20000
N_BOOT=10000

def history(pair,seed,n=N):
 rng=np.random.default_rng(seed+1000*pair)
 if pair==0:return np.ones(n),-np.ones(n)
 if pair==1:return np.where(np.arange(n)%2==0,1.,-1.),np.ones(n)
 if pair==2:return np.where(rng.random(n)<.12,-1.,1.),np.where(rng.random(n)<.06,1.,-1.)
 return np.sign(np.sin(np.linspace(0,18*np.pi,n))),np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))

def extract(cfg,seed,u):
 r=simulate(np.r_[u,np.zeros(FUTURE)],cfg,seed=seed); i=N
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
 da=np.linalg.norm(sig-ra); db=np.linalg.norm(sig-rb)
 return float((db-da)/max(da+db,1e-12))

def main():
 rows=[]
 for pp in PARAMS:
  cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
  for pair in range(4):
   for hs in HSEEDS:
    ua,ub=history(pair,hs); a=extract(cfg,hs,ua); b=extract(cfg,hs,ub)
    receiver={k:(a[k]+b[k])/2 for k in a}
    refs={}
    for dn,donor in [("A",a),("B",b)]:
     st=transform(donor,receiver,0)
     sigs=[signature(cont(cfg,st,s)) for s in CREF]
     refs[dn]=np.mean(np.stack(sigs),axis=0)
    for mem in MEMS:
     for pressure in PRESS:
      rc=dict(receiver); rc["memory"]=mem; rc["pressure"]=pressure
      for angle in ANGLES:
       for dn,donor in [("A",a),("B",b)]:
        expected=1 if dn=="A" else -1
        st=transform(donor,rc,angle)
        for cs in CTEST:
         sig=signature(cont(cfg,st,cs+hs))
         x=score(sig,refs["A"],refs["B"])
         rows.append({"param":pp["name"],"pair":pair,"history_seed":hs,
          "memory":mem,"pressure":pressure,"angle_deg":angle,
          "donor":dn,"signed_affinity":expected*x})
 raw=pd.DataFrame(rows)
 raw.to_csv(OUT/"raw.csv",index=False)

 cell=(raw.groupby(["param","pair","history_seed","memory","pressure","angle_deg"],as_index=False)
       .agg(signed_affinity=("signed_affinity","mean")))
 wide=cell.pivot_table(index=["param","pair","history_seed","memory","pressure"],
                        columns="angle_deg",values="signed_affinity").reset_index()
 # Restore numeric angle columns for stable downstream handling.
 for a in ANGLES:
  wide[str(a)] = wide[a]
 wide["contrast_30_150"]=wide["30"]-wide["150"]
 wide["contrast_60_120"]=wide["60"]-wide["120"]
 wide.to_csv(OUT/"paired_context_cells.csv",index=False)

 # Collapse repeated parameter/context cells into one value per history-seed block.
 block=(wide.groupby(["pair","history_seed"],as_index=False)
        .agg(contrast_30_150=("contrast_30_150","mean"),
             contrast_60_120=("contrast_60_120","mean")))
 observed=float(block["contrast_30_150"].mean())

 # Stratified sign-flip null: 10 history seeds inside each of 4 history-pair strata.
 rng=np.random.default_rng(424242)
 null=np.empty(N_PERM)
 for i in range(N_PERM):
  signed=[]
  for pair,g in block.groupby("pair"):
   vals=g["contrast_30_150"].to_numpy()
   signs=rng.choice([-1.0,1.0],size=len(vals))
   signed.extend(vals*signs)
  null[i]=np.mean(signed)
 p=float((1+np.sum(null>=observed))/(N_PERM+1))

 # Cluster bootstrap over history-seed blocks, preserving pair strata.
 boot=np.empty(N_BOOT)
 groups={pair:g["contrast_30_150"].to_numpy() for pair,g in block.groupby("pair")}
 for i in range(N_BOOT):
  vals=[]
  for pair,x in groups.items():
   idx=rng.integers(0,len(x),size=len(x))
   vals.extend(x[idx])
  boot[i]=np.mean(vals)
 ci_low=float(np.quantile(boot,0.025)); ci_high=float(np.quantile(boot,0.975))

 summary={
  "observed_mean_contrast_30_minus_150":observed,
  "cluster_null_mean":float(null.mean()),
  "cluster_null_95th":float(np.quantile(null,0.95)),
  "cluster_permutation_p":p,
  "bootstrap_95_low":ci_low,
  "bootstrap_95_high":ci_high,
  "history_seed_blocks":int(len(block)),
  "history_pair_strata":4,
  "permutations":N_PERM,
  "bootstraps":N_BOOT,
 }
 pd.DataFrame([summary]).to_csv(OUT/"cluster_summary.csv",index=False)

 ctx=(wide.groupby(["memory","pressure"],as_index=False)
      .agg(mean_contrast_30_150=("contrast_30_150","mean"),
           mean_contrast_60_120=("contrast_60_120","mean")))
 ctx.to_csv(OUT/"context_summary.csv",index=False)

 (OUT/"summary.json").write_text(json.dumps({
  "experiment":"state_geometry_cluster_null_v34",
  "design":{"independent_history_seeds":list(HSEEDS),"blind_parameter_points":6,
   "history_pairs":4,"memory_values":MEMS,"pressure_values":PRESS,
   "angles_deg":ANGLES,"radius":RADIUS,"future_input":"exactly zero",
   "reference_noise_seeds":list(CREF),"test_noise_seeds":list(CTEST),
   "primary":"30° minus 150° signed-affinity at history-seed block level",
   "null":"stratified sign flip within each history-pair stratum",
   "bootstrap":"stratified resampling of history-seed blocks"}},
  indent=2),encoding="utf-8")
 print("CLUSTER SUMMARY")
 print(pd.DataFrame([summary]).to_string(index=False))
 print("\nCONTEXT")
 print(ctx.to_string(index=False))

if __name__=="__main__":
 main()
