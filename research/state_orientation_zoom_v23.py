from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_orientation_zoom_v23");OUT.mkdir(parents=True,exist_ok=True)
PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
SEEDS=range(10);N=300;FUTURE=120;WINDOW=60
ANGLES=list(range(0,181,15))+list(range(195,360,15))

def history(pair,seed,n=N):
 rng=np.random.default_rng(seed+1000*pair)
 if pair==0:return np.ones(n),-np.ones(n)
 if pair==1:return np.where(np.arange(n)%2==0,1.,-1.),np.ones(n)
 if pair==2:return np.where(rng.random(n)<.12,-1.,1.),np.where(rng.random(n)<.06,1.,-1.)
 return np.sign(np.sin(np.linspace(0,18*np.pi,n))),np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))

def extract(cfg,seed,u):
 r=simulate(np.r_[u,np.zeros(FUTURE)],cfg,seed=seed);i=N
 return {"state_prev":float(r["state"][i-2]),"state":float(r["state"][i-1]),"memory":float(r["memory"][i-1]),"pressure":float(r["pressure"][i-1])}

def cont(cfg,ctx,seed):
 return simulate(np.zeros(FUTURE),cfg,seed=seed,initial_prev_state=ctx["state_prev"],initial_state=ctx["state"],initial_memory=ctx["memory"],initial_pressure=ctx["pressure"])

def affinity(run,ra,rb):
 da=float(np.mean(np.abs(run["state"][:WINDOW]-ra["state"][:WINDOW])));db=float(np.mean(np.abs(run["state"][:WINDOW]-rb["state"][:WINDOW])))
 return float((db-da)/max(da+db,1e-12))

def rotate(donor,common,deg):
 d=np.array([donor["state_prev"]-common["state_prev"],donor["state"]-common["state"]])
 th=np.deg2rad(deg);R=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]])
 rd=R@d;c=dict(common);c["state_prev"]=common["state_prev"]+rd[0];c["state"]=common["state"]+rd[1]
 return c

def main():
 rows=[]
 for pp in PARAMS:
  cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
  for pair in range(4):
   for seed in SEEDS:
    ua,ub=history(pair,seed);a=extract(cfg,seed,ua);b=extract(cfg,seed,ub)
    ra,rb=cont(cfg,a,seed),cont(cfg,b,seed);common={k:(a[k]+b[k])/2 for k in a}
    for donor_name,donor in [("A",a),("B",b)]:
     expected=1 if donor_name=="A" else -1
     for angle in ANGLES:
      run=cont(cfg,rotate(donor,common,angle),seed);x=affinity(run,ra,rb)
      rows.append({"param":pp["name"],"pair":pair,"seed":seed,"donor":donor_name,"angle_deg":angle,
       "affinity":x,"identity_accuracy":int(np.sign(x)==expected),"opposite_accuracy":int(np.sign(x)==-expected),
       "abs_affinity":abs(x)})
 raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
 pooled=raw.groupby("angle_deg",as_index=False).agg(identity_accuracy=("identity_accuracy","mean"),
  opposite_accuracy=("opposite_accuracy","mean"),affinity=("affinity","mean"),abs_affinity=("abs_affinity","mean"))
 by=raw.groupby(["param","angle_deg"],as_index=False).agg(identity_accuracy=("identity_accuracy","mean"),
  opposite_accuracy=("opposite_accuracy","mean"),affinity=("affinity","mean"))
 pooled.to_csv(OUT/"pooled.csv",index=False);by.to_csv(OUT/"by_param.csv",index=False)
 z=pooled.sort_values("angle_deg")
 # angular zero crossing of pooled affinity, linearly interpolated between adjacent samples
 crossings=[]
 vals=z[["angle_deg","affinity"]].to_numpy()
 for (a1,y1),(a2,y2) in zip(vals[:-1],vals[1:]):
  if y1==0 or y1*y2<0:
   aa=float(a1 if y1==0 else a1+(0-y1)*(a2-a1)/(y2-y1));crossings.append(aa)
 payload={"experiment":"state_orientation_zoom_v23","design":{"blind_parameter_points":6,"history_pairs":4,"seeds_per_pair":10,
 "angles_deg":ANGLES,"future_input":"exactly zero","receiver_memory_and_pressure":"common A/B midpoint",
 "equal_norm_rotation":True},"pooled":pooled.to_dict("records"),"by_param":by.to_dict("records"),"affinity_zero_crossings_deg":crossings}
 (OUT/"summary.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
 print(pooled.to_string(index=False));print("ZERO_CROSSINGS",crossings)

if __name__=="__main__":main()