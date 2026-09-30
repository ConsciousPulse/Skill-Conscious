from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_context_effects_v31"); OUT.mkdir(parents=True, exist_ok=True)

PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
SEEDS=range(60,70)
N=300; FUTURE=120; WINDOW=60; RADIUS=1.1
ANGLES=[30,90,150]
MEMS=[-0.8,-0.4,0.0,0.4,0.8]
PRESS=[0.0,0.5,1.0,1.5,2.0]

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
 c=dict(receiver); c["state_prev"]=receiver["state_prev"]+rd[0]; c["state"]=receiver["state"]+rd[1]
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
    ua,ub=history(pair,seed)
    a=extract(cfg,seed,ua); b=extract(cfg,seed,ub)
    receiver_state={k:(a[k]+b[k])/2 for k in a}
    for mem in MEMS:
     for pressure in PRESS:
      rc=dict(receiver_state); rc["memory"]=mem; rc["pressure"]=pressure
      refs={angle:(cont(cfg,transform(a,rc,RADIUS,angle),seed+12000),
                   cont(cfg,transform(b,rc,RADIUS,angle),seed+12000)) for angle in ANGLES}
      # The reference continuation for each context is the unrotated local donor geometry.
      for angle in ANGLES:
       ra,rb=refs[angle]
       for donor_name,donor in [("A",a),("B",b)]:
        expected=1 if donor_name=="A" else -1
        c=transform(donor,rc,RADIUS,angle)
        run=cont(cfg,c,seed+12000)
        x=affinity(run,ra,rb)
        rows.append({"param":pp["name"],"pair":pair,"seed":seed,
                     "memory_context":mem,"pressure_context":pressure,
                     "angle_deg":angle,"donor":donor_name,
                     "signed_affinity":expected*x,
                     "correct":int(np.sign(x)==expected)})
 raw=pd.DataFrame(rows); raw.to_csv(OUT/"raw.csv",index=False)
 pooled=(raw.groupby(["memory_context","pressure_context","angle_deg"],as_index=False)
   .agg(signed_affinity=("signed_affinity","mean"),identity_accuracy=("correct","mean")))
 pooled.to_csv(OUT/"pooled.csv",index=False)

 center=pooled[(pooled.memory_context==0.0)&(pooled.pressure_context==1.0)].set_index("angle_deg")["signed_affinity"]
 mem_rows=[]
 for angle in ANGLES:
  base=float(center.loc[angle])
  for mem in MEMS:
   cur=float(pooled[(pooled.memory_context==mem)&(pooled.pressure_context==1.0)&(pooled.angle_deg==angle)].signed_affinity.iloc[0])
   mem_rows.append({"angle_deg":angle,"memory":mem,"baseline_signed_affinity":base,
                    "signed_affinity":cur,"paired_memory_effect":cur-base})
 pressure_rows=[]
 for angle in ANGLES:
  base=float(center.loc[angle])
  for pressure in PRESS:
   cur=float(pooled[(pooled.memory_context==0.0)&(pooled.pressure_context==pressure)&(pooled.angle_deg==angle)].signed_affinity.iloc[0])
   pressure_rows.append({"angle_deg":angle,"pressure":pressure,"baseline_signed_affinity":base,
                         "signed_affinity":cur,"paired_pressure_effect":cur-base})

 inter_rows=[]
 for angle in ANGLES:
  base=float(center.loc[angle])
  for mem in MEMS:
   for pressure in PRESS:
    cur=float(pooled[(pooled.memory_context==mem)&(pooled.pressure_context==pressure)&(pooled.angle_deg==angle)].signed_affinity.iloc[0])
    mem_only=float(pooled[(pooled.memory_context==mem)&(pooled.pressure_context==1.0)&(pooled.angle_deg==angle)].signed_affinity.iloc[0])
    press_only=float(pooled[(pooled.memory_context==0.0)&(pooled.pressure_context==pressure)&(pooled.angle_deg==angle)].signed_affinity.iloc[0])
    inter_rows.append({"angle_deg":angle,"memory":mem,"pressure":pressure,
                       "two_way_interaction":cur-mem_only-press_only+base})
 pd.DataFrame(mem_rows).to_csv(OUT/"memory_effects.csv",index=False)
 pd.DataFrame(pressure_rows).to_csv(OUT/"pressure_effects.csv",index=False)
 pd.DataFrame(inter_rows).to_csv(OUT/"interaction_effects.csv",index=False)

 payload={"experiment":"state_geometry_context_effects_v31",
  "purpose":"paired causal decomposition of memory and pressure context effects on state geometry",
  "design":{"blind_parameter_points":6,"history_pairs":4,"seeds":list(SEEDS),
            "receiver_state":"common A/B midpoint","radius":RADIUS,"angles_deg":ANGLES,
            "memory_values":MEMS,"pressure_values":PRESS,
            "reference_context":"memory 0.0, pressure 1.0",
            "future_input":"exactly zero","noise_std":0.01,
            "primary":"within-seed paired signed-affinity differences"}}
 (OUT/"summary.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
 print(pooled.to_string(index=False))
 print("\nMemory effects")
 print(pd.DataFrame(mem_rows).to_string(index=False))
 print("\nPressure effects")
 print(pd.DataFrame(pressure_rows).to_string(index=False))

if __name__=="__main__":
 main()
