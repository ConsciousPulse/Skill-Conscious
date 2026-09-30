from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_noise_v27"); OUT.mkdir(parents=True, exist_ok=True)
PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
SEEDS=range(20,30)
N=300; FUTURE=120; WINDOW=60
NOISES=[0.0,0.005,0.01,0.025,0.05,0.10]
RADII=[0.5,1.1]
ANGLES=[0,90,180]

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

def transform(donor,common,radius,angle):
 d=np.array([donor["state_prev"]-common["state_prev"],donor["state"]-common["state"]])
 th=np.deg2rad(angle)
 R=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]])
 rd=radius*(R@d)
 c=dict(common); c["state_prev"]=common["state_prev"]+rd[0]; c["state"]=common["state"]+rd[1]
 return c

def aff(run,ra,rb):
 da=float(np.mean(np.abs(run["state"][:WINDOW]-ra["state"][:WINDOW])))
 db=float(np.mean(np.abs(run["state"][:WINDOW]-rb["state"][:WINDOW])))
 return (db-da)/max(da+db,1e-12)

def main():
 rows=[]
 for pp in PARAMS:
  base_cfg={k:v for k,v in pp.items() if k!="name"}
  for noise in NOISES:
   cfg=Config(**base_cfg,noise_std=noise)
   for pair in range(4):
    for seed in SEEDS:
     ua,ub=history(pair,seed); a=extract(cfg,seed,ua); b=extract(cfg,seed,ub)
     ra,rb=cont(cfg,a,seed),cont(cfg,b,seed)
     common={k:(a[k]+b[k])/2 for k in a}
     for donor_name,donor in [("A",a),("B",b)]:
      expected=1 if donor_name=="A" else -1
      for radius in RADII:
       for angle in ANGLES:
        c=transform(donor,common,radius,angle)
        run=cont(cfg,c,seed)
        x=aff(run,ra,rb)
        rows.append({"param":pp["name"],"noise_std":noise,"pair":pair,"seed":seed,
                     "donor":donor_name,"radius":radius,"angle_deg":angle,
                     "affinity":x,"correct":int(np.sign(x)==expected)})
 raw=pd.DataFrame(rows); raw.to_csv(OUT/"raw.csv",index=False)
 pooled=(raw.groupby(["noise_std","radius","angle_deg"],as_index=False)
   .agg(identity_accuracy=("correct","mean"),affinity=("affinity","mean")))
 pooled.to_csv(OUT/"pooled.csv",index=False)
 pivot=pooled.pivot_table(index=["noise_std","radius"],columns="angle_deg",values="identity_accuracy").reset_index()
 pivot.to_csv(OUT/"angular_noise_summary.csv",index=False)
 payload={"experiment":"state_geometry_noise_v27",
  "design":{"blind_parameter_points":6,"history_pairs":4,"seeds":list(SEEDS),
   "noise_std":NOISES,"radii":RADII,"angles_deg":ANGLES,"future_input":"exactly zero",
   "receiver_memory_and_pressure":"common A/B midpoint","primary_metric":"identity_accuracy"}}
 (OUT/"summary.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
 print(pooled.to_string(index=False))
if __name__=="__main__":main()
