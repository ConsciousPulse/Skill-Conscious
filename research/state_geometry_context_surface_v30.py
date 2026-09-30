from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_context_surface_v30"); OUT.mkdir(parents=True, exist_ok=True)

PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
SEEDS=range(50,60)
N=300; FUTURE=120; WINDOW=60
RADIUS=1.1
ANGLES=[30,60,90,120,150]
MEMORY_VALUES=[-0.8,-0.4,0.0,0.4,0.8]
PRESSURE_VALUES=[0.0,0.5,1.0,1.5,2.0]

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
 d=np.array([donor["state_prev"]-receiver["state_prev"],
             donor["state"]-receiver["state"]])
 th=np.deg2rad(angle)
 R=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]])
 rd=radius*(R@d)
 c=dict(receiver)
 c["state_prev"]=receiver["state_prev"]+rd[0]
 c["state"]=receiver["state"]+rd[1]
 return c

def affinity(run,ra,rb):
 da=float(np.mean(np.abs(run["state"][:WINDOW]-ra["state"][:WINDOW])))
 db=float(np.mean(np.abs(run["state"][:WINDOW]-rb["state"][:WINDOW])))
 return float((db-da)/max(da+db,1e-12))

def main():
 rows=[]
 for pp in PARAMS:
  cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
  for pair in range(4):
   for seed in SEEDS:
    ua,ub=history(pair,seed); a=extract(cfg,seed,ua); b=extract(cfg,seed,ub)
    receiver_state={k:(a[k]+b[k])/2 for k in a}
    for mi,mem in enumerate(MEMORY_VALUES):
     for pi,pressure in enumerate(PRESSURE_VALUES):
      rc=dict(receiver_state); rc["memory"]=mem; rc["pressure"]=pressure
      # Local A/B references are generated in this same nuisance context.
      ra=cont(cfg,transform(a,rc,RADIUS,0),seed+12000)
      rb=cont(cfg,transform(b,rc,RADIUS,0),seed+12000)
      for donor_name,donor in [("A",a),("B",b)]:
       expected=1 if donor_name=="A" else -1
       for angle in ANGLES:
        c=transform(donor,rc,RADIUS,angle)
        run=cont(cfg,c,seed+12000)
        x=affinity(run,ra,rb)
        rows.append({
          "param":pp["name"],"pair":pair,"seed":seed,
          "memory_context":mem,"pressure_context":pressure,
          "memory_index":mi,"pressure_index":pi,
          "donor":donor_name,"angle_deg":angle,
          "affinity":x,"signed_affinity":expected*x,
          "correct":int(np.sign(x)==expected)
        })
 raw=pd.DataFrame(rows); raw.to_csv(OUT/"raw.csv",index=False)
 pooled=(raw.groupby(["memory_context","pressure_context","angle_deg"],as_index=False)
   .agg(identity_accuracy=("correct","mean"),
        signed_affinity=("signed_affinity","mean"),
        abs_affinity=("affinity","mean")))
 pooled.to_csv(OUT/"pooled.csv",index=False)

 angle_summary=(pooled.groupby(["memory_context","pressure_context"],as_index=False)
   .agg(mean_identity=("identity_accuracy","mean"),
        mean_signed_affinity=("signed_affinity","mean")))
 angle_summary.to_csv(OUT/"context_summary.csv",index=False)

 interaction=[]
 for angle in ANGLES:
  z=pooled[pooled.angle_deg==angle]
  interaction.append({
    "angle_deg":angle,
    "identity_min":float(z.identity_accuracy.min()),
    "identity_max":float(z.identity_accuracy.max()),
    "identity_range":float(z.identity_accuracy.max()-z.identity_accuracy.min()),
    "signed_affinity_min":float(z.signed_affinity.min()),
    "signed_affinity_max":float(z.signed_affinity.max()),
    "signed_affinity_range":float(z.signed_affinity.max()-z.signed_affinity.min())
  })
 pd.DataFrame(interaction).to_csv(OUT/"angle_interaction.csv",index=False)

 payload={
  "experiment":"state_geometry_context_surface_v30",
  "purpose":"measure state-geometry response across donor-independent synthetic memory/pressure contexts",
  "design":{
   "blind_parameter_points":6,"history_pairs":4,"seeds":list(SEEDS),
   "receiver_state":"common A/B midpoint",
   "memory_values":MEMORY_VALUES,"pressure_values":PRESSURE_VALUES,
   "radius":RADIUS,"angles_deg":ANGLES,
   "future_input":"exactly zero","noise_std":0.01,
   "primary_metric":"identity_accuracy and signed_affinity",
   "context_donor_link":"none",
   "note":"180 degree condition intentionally excluded because midpoint geometry makes it an exact donor swap"
  }
 }
 (OUT/"summary.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
 print(pooled.to_string(index=False))
 print("\nANGLE INTERACTION")
 print(pd.DataFrame(interaction).to_string(index=False))

if __name__=="__main__":
 main()
