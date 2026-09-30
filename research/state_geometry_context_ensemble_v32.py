from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_context_ensemble_v32"); OUT.mkdir(parents=True, exist_ok=True)

PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
HISTORY_SEEDS=range(70,80)
CONT_SEEDS=range(910,915)
N=300; FUTURE=60
RADIUS=1.1
ANGLES=[30,60,90,120,150]
MEMS=[-0.8,0.0,0.8]
PRESS=[0.0,1.0,2.0]
STRIDE=5

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

def transform(donor,receiver,radius,angle):
 d=np.array([donor["state_prev"]-receiver["state_prev"],donor["state"]-receiver["state"]])
 th=np.deg2rad(angle)
 R=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]])
 rd=radius*(R@d)
 c=dict(receiver)
 c["state_prev"]=receiver["state_prev"]+rd[0]
 c["state"]=receiver["state"]+rd[1]
 return c

def signature(run):
 # Compact temporal signature; avoids exact path matching and same-noise cancellation.
 return run["state"][::STRIDE].astype(float)

def score(sig,refa,refb):
 da=float(np.linalg.norm(sig-refa))
 db=float(np.linalg.norm(sig-refb))
 return float((db-da)/max(da+db,1e-12))

def main():
 rows=[]
 for pp in PARAMS:
  cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
  for pair in range(4):
   for hseed in HISTORY_SEEDS:
    ua,ub=history(pair,hseed)
    a=extract(cfg,hseed,ua); b=extract(cfg,hseed,ub)
    receiver_state={k:(a[k]+b[k])/2 for k in a}
    for mem in MEMS:
     for pressure in PRESS:
      rc=dict(receiver_state); rc["memory"]=mem; rc["pressure"]=pressure

      refs={}
      for donor_name,donor in [("A",a),("B",b)]:
       ref_sigs=[]
       ref_state=transform(donor,rc,RADIUS,0)
       for cseed in CONT_SEEDS:
        ref_sigs.append(signature(cont(cfg,ref_state,cseed)))
       refs[donor_name]=np.mean(np.stack(ref_sigs,axis=0),axis=0)

      for donor_name,donor in [("A",a),("B",b)]:
       expected=1 if donor_name=="A" else -1
       for angle in ANGLES:
        test_state=transform(donor,rc,RADIUS,angle)
        for cseed in CONT_SEEDS:
         sig=signature(cont(cfg,test_state,20000+ cseed + hseed))
         x=score(sig,refs["A"],refs["B"])
         rows.append({"param":pp["name"],"pair":pair,"history_seed":hseed,
          "memory_context":mem,"pressure_context":pressure,"donor":donor_name,
          "angle_deg":angle,"continuation_seed":cseed,
          "signed_affinity":expected*x,
          "correct":int(np.sign(x)==expected)})

 raw=pd.DataFrame(rows); raw.to_csv(OUT/"raw.csv",index=False)
 pooled=(raw.groupby(["memory_context","pressure_context","angle_deg"],as_index=False)
  .agg(identity_accuracy=("correct","mean"),signed_affinity=("signed_affinity","mean")))
 pooled.to_csv(OUT/"pooled.csv",index=False)

 summary=(pooled.groupby("angle_deg",as_index=False).agg(
  min_identity=("identity_accuracy","min"),
  max_identity=("identity_accuracy","max"),
  mean_identity=("identity_accuracy","mean")))
 summary["context_range"]=summary.max_identity-summary.min_identity
 summary.to_csv(OUT/"angle_context_summary.csv",index=False)

 payload={"experiment":"state_geometry_context_ensemble_v32",
  "purpose":"robust context transport test using independent continuation ensembles",
  "design":{"blind_parameter_points":6,"history_pairs":4,"history_seeds":list(HISTORY_SEEDS),
   "continuation_reference_seeds":list(CONT_SEEDS),"receiver_state":"common A/B midpoint",
   "memory_values":MEMS,"pressure_values":PRESS,"radius":RADIUS,"angles_deg":ANGLES,
   "future_input":"exactly zero","noise_std":0.01,
   "reference":"mean temporal signature of five independent unrotated A/B continuations",
   "test":"independent continuation noise seeds for each rotated condition",
   "signature":"state trajectory sampled every 5 steps"}}
 (OUT/"summary.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
 print(pooled.to_string(index=False))
 print("\nANGLE SUMMARY")
 print(summary.to_string(index=False))

if __name__=="__main__":
 main()
