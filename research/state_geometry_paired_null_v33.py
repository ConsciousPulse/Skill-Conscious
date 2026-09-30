from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_paired_null_v33"); OUT.mkdir(parents=True, exist_ok=True)

PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
HSEEDS=range(80,90)
CSEEDS=range(1200,1205)
N=300; FUTURE=60; RADIUS=1.1; STRIDE=5
ANGLES=[30,60,90,120,150]
MEMS=[-0.8,0.0,0.8]
PRESS=[0.0,1.0,2.0]
N_PERM=2000

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

def score(sig,refa,refb):
 da=np.linalg.norm(sig-refa); db=np.linalg.norm(sig-refb)
 return float((db-da)/max(da+db,1e-12))

def main():
 rows=[]
 for pp in PARAMS:
  cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
  for pair in range(4):
   for hs in HSEEDS:
    ua,ub=history(pair,hs); a=extract(cfg,hs,ua); b=extract(cfg,hs,ub)
    receiver_state={k:(a[k]+b[k])/2 for k in a}
    for mem in MEMS:
     for pressure in PRESS:
      rc=dict(receiver_state); rc["memory"]=mem; rc["pressure"]=pressure
      ref_sigs={dn:[] for dn in ["A","B"]}
      for dn,donor in [("A",a),("B",b)]:
       st=transform(donor,rc,0)
       for cs in CSEEDS:
        ref_sigs[dn].append(signature(cont(cfg,st,cs)))
      refa=np.mean(np.stack(ref_sigs["A"]),axis=0)
      refb=np.mean(np.stack(ref_sigs["B"]),axis=0)
      for angle in ANGLES:
       for dn,donor in [("A",a),("B",b)]:
        expected=1 if dn=="A" else -1
        st=transform(donor,rc,angle)
        vals=[]
        for cs in CSEEDS:
         sig=signature(cont(cfg,st,20000+cs+hs))
         vals.append(expected*score(sig,refa,refb))
        rows.append({"param":pp["name"],"pair":pair,"history_seed":hs,
          "memory":mem,"pressure":pressure,"angle_deg":angle,
          "signed_affinity":float(np.mean(vals)),
          "identity":float(np.mean(np.array(vals)>0))})
 raw=pd.DataFrame(rows)
 raw.to_csv(OUT/"raw.csv",index=False)

 # Pair angular contrast within each identical history/context cell.
 wide=raw.pivot_table(index=["param","pair","history_seed","memory","pressure"],
                       columns="angle_deg",values="signed_affinity").reset_index()
 wide["contrast_30_150"]=wide[30]-wide[150]
 wide["contrast_60_120"]=wide[60]-wide[120]
 wide.to_csv(OUT/"paired_contrasts.csv",index=False)

 obs=float(wide["contrast_30_150"].mean())
 rng=np.random.default_rng(424242)
 null=np.empty(N_PERM)
 vals=wide[[30,150]].to_numpy(float)
 for i in range(N_PERM):
  swap=rng.integers(0,2,size=len(vals)).astype(bool)
  diff=vals[:,0]-vals[:,1]
  null[i]=np.mean(np.where(swap,-diff,diff))
 p=float((1+np.sum(null>=obs))/(N_PERM+1))
 effect=float(obs)
 q95=float(np.quantile(null,.95))
 summary={
  "observed_mean_contrast_30_minus_150":effect,
  "permutation_null_mean":float(null.mean()),
  "permutation_null_95th":q95,
  "one_sided_p":p,
  "n_matched_units":int(len(wide)),
  "n_permutations":N_PERM
 }
 pd.DataFrame([summary]).to_csv(OUT/"permutation_summary.csv",index=False)

 ctx=(wide.groupby(["memory","pressure"],as_index=False)
   .agg(mean_contrast_30_150=("contrast_30_150","mean"),
        mean_contrast_60_120=("contrast_60_120","mean")))
 ctx.to_csv(OUT/"context_contrasts.csv",index=False)

 payload={"experiment":"state_geometry_paired_null_v33",
  "purpose":"paired angular contrast with within-unit angle permutation null",
  "design":{"blind_parameter_points":6,"history_pairs":4,"history_seeds":list(HSEEDS),
    "continuation_reference_seeds":list(CSEEDS),"receiver_state":"common A/B midpoint",
    "memory_values":MEMS,"pressure_values":PRESS,"radius":RADIUS,"angles_deg":ANGLES,
    "future_input":"exactly zero","noise_std":0.01,"signature_stride":STRIDE,
    "primary":"within-unit signed-affinity contrast 30° minus 150°",
    "null":"independent permutation of the two angle labels within each matched unit"}}
 (OUT/"summary.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
 print("SUMMARY",summary)
 print("\nCONTEXT")
 print(ctx.to_string(index=False))

if __name__=="__main__": main()
