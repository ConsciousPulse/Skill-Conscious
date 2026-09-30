from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_counterfactual_v19");OUT.mkdir(parents=True,exist_ok=True)
PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
SEEDS=range(10); N=300; FUTURE=120; WINDOW=60

def history(pair,seed,n=N):
 rng=np.random.default_rng(seed+1000*pair)
 if pair==0:return np.ones(n),-np.ones(n)
 if pair==1:return np.where(np.arange(n)%2==0,1.,-1.),np.ones(n)
 if pair==2:return np.where(rng.random(n)<.12,-1.,1.),np.where(rng.random(n)<.06,1.,-1.)
 return np.sign(np.sin(np.linspace(0,18*np.pi,n))),np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))

def extract(cfg,seed,u):
 r=simulate(np.r_[u,np.zeros(FUTURE)],cfg,seed=seed);i=N
 return {"state_prev":float(r["state"][i-2]),"state":float(r["state"][i-1]),
         "memory":float(r["memory"][i-1]),"pressure":float(r["pressure"][i-1])}

def cont(cfg,ctx,seed):
 return simulate(np.zeros(FUTURE),cfg,seed=seed,initial_prev_state=ctx["state_prev"],
                 initial_state=ctx["state"],initial_memory=ctx["memory"],initial_pressure=ctx["pressure"])

def aff(run,ra,rb):
 da=float(np.mean(np.abs(run["state"][:WINDOW]-ra["state"][:WINDOW])))
 db=float(np.mean(np.abs(run["state"][:WINDOW]-rb["state"][:WINDOW])))
 return float((db-da)/max(da+db,1e-12))

def transform(donor,common,mode,bits=3):
 c=dict(common)
 if mode=="intact": c["state_prev"],c["state"]=donor["state_prev"],donor["state"]
 elif mode=="erase": pass
 elif mode=="invert":
  c["state_prev"]=common["state_prev"]-(donor["state_prev"]-common["state_prev"])
  c["state"]=common["state"]-(donor["state"]-common["state"])
 elif mode=="invert_quantized":
  c["state_prev"]=common["state_prev"]-(donor["state_prev"]-common["state_prev"])
  c["state"]=common["state"]-(donor["state"]-common["state"])
  def q(x):
   levels=2**bits;step=2/(levels-1);y=np.clip(x,-1,1)
   return float(-1+np.round((y+1)/step)*step)
  c["state_prev"],c["state"]=q(c["state_prev"]),q(c["state"])
 else: raise ValueError(mode)
 return c

def main():
 rows=[]
 for pp in PARAMS:
  cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
  for pair in range(4):
   for seed in SEEDS:
    ua,ub=history(pair,seed);a=extract(cfg,seed,ua);b=extract(cfg,seed,ub)
    ra,rb=cont(cfg,a,seed),cont(cfg,b,seed)
    common={k:(a[k]+b[k])/2 for k in a}
    for donor_name,donor in [("A",a),("B",b)]:
     expected=1 if donor_name=="A" else -1
     for mode in ["intact","erase","invert","invert_quantized"]:
      c=transform(donor,common,mode,3);run=cont(cfg,c,seed);x=aff(run,ra,rb)
      rows.append({"param":pp["name"],"pair":pair,"seed":seed,"donor":donor_name,"mode":mode,
       "affinity":x,"abs_affinity":abs(x),"correct":int(np.sign(x)==expected),
       "flip_correct":int(np.sign(x)==-expected),
       "prediction_mae":float(np.mean(np.abs(run["state"][:WINDOW]-(ra if donor_name=="A" else rb)["state"][:WINDOW])))})
 raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
 summary=raw.groupby(["mode"],as_index=False).agg(identity_accuracy=("correct","mean"),
  flipped_identity_accuracy=("flip_correct","mean"),abs_affinity=("abs_affinity","mean"),affinity=("affinity","mean"),prediction_mae=("prediction_mae","mean"))
 by=raw.groupby(["param","mode"],as_index=False).agg(identity_accuracy=("correct","mean"),
  flipped_identity_accuracy=("flip_correct","mean"),abs_affinity=("abs_affinity","mean"),affinity=("affinity","mean"))
 summary.to_csv(OUT/"pooled.csv",index=False);by.to_csv(OUT/"by_param.csv",index=False)
 payload={"experiment":"state_counterfactual_v19","design":{"blind_parameter_points":6,"history_pairs":4,"seeds_per_pair":10,
 "future_input":"exactly zero","receiver_memory_and_pressure":"common A/B midpoint","counterfactual":"reflect donor state around common state",
 "quantized_bits":3},"pooled":summary.to_dict("records"),"by_param":by.to_dict("records")}
 (OUT/"summary.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
 print(summary.to_string(index=False));print("\nBY PARAM");print(by.to_string(index=False))

if __name__=="__main__": main()