from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_source_permutation_v18");OUT.mkdir(parents=True,exist_ok=True)
PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
SEEDS=range(10); N=300; FUTURE=120; WINDOW=60

def histories(seed,n=N):
 rng=np.random.default_rng(seed)
 return [
  np.ones(n),
  -np.ones(n),
  np.where(np.arange(n)%2==0,1.0,-1.0),
 ]

def extract(cfg,seed,u):
 r=simulate(np.r_[u,np.zeros(FUTURE)],cfg,seed=seed); i=N
 return {"state_prev":float(r["state"][i-2]),"state":float(r["state"][i-1]),
         "memory":float(r["memory"][i-1]),"pressure":float(r["pressure"][i-1])}

def cont(cfg,ctx,seed):
 return simulate(np.zeros(FUTURE),cfg,seed=seed,initial_prev_state=ctx["state_prev"],
                 initial_state=ctx["state"],initial_memory=ctx["memory"],initial_pressure=ctx["pressure"])

def q(x,bits):
 levels=2**bits; step=2.0/(levels-1); y=np.clip(x,-1,1)
 return float(-1+np.round((y+1)/step)*step)

def dist(run,ref): return float(np.mean(np.abs(run["state"][:WINDOW]-ref["state"][:WINDOW])))

def nearest(run,refs):
 ds=[dist(run,r) for r in refs]
 return int(np.argmin(ds)),ds

def main():
 rows=[]
 for pp in PARAMS:
  cfg=Config(**{k:v for k,v in pp.items() if k!="name"},noise_std=.01)
  for seed in SEEDS:
   hs=histories(seed)
   ctxs=[extract(cfg,seed,u) for u in hs]
   refs=[cont(cfg,c,seed) for c in ctxs]
   common={k:float(np.mean([c[k] for c in ctxs])) for k in ctxs[0]}
   for source in range(3):
    for bits in (None,3,4,6):
     donor=ctxs[source]; c=dict(common)
     if bits is None:
      c["state_prev"]=donor["state_prev"]; c["state"]=donor["state"]
     else:
      c["state_prev"]=q(donor["state_prev"],bits); c["state"]=q(donor["state"],bits)
     run=cont(cfg,c,seed)
     pred,ds=nearest(run,refs)
     rows.append({"param":pp["name"],"seed":seed,"source":source,"bits":bits if bits else 0,
                  "predicted_source":pred,"correct":int(pred==source),
                  "d_source":ds[source],"d_best":min(ds),"margin":sorted(ds)[1]-sorted(ds)[0]})
   # Explicit pairwise swap test at 3 bits: receiver labels are irrelevant; classification should follow source.
   for source in range(3):
    for nominal in range(3):
     c=dict(common); donor=ctxs[source]; c["state_prev"]=q(donor["state_prev"],3); c["state"]=q(donor["state"],3)
     run=cont(cfg,c,seed); pred,ds=nearest(run,refs)
     rows.append({"param":pp["name"],"seed":seed,"source":source,"bits":3,
                  "predicted_source":pred,"correct":int(pred==source),"nominal_receiver":nominal,
                  "swap_test":1,"d_source":ds[source],"d_best":min(ds),"margin":sorted(ds)[1]-sorted(ds)[0]})
 raw=pd.DataFrame(rows); raw.to_csv(OUT/"raw.csv",index=False)
 core=raw[raw.get("swap_test",0)!=1].copy() if "swap_test" in raw.columns else raw
 grouped=core.groupby(["bits"],as_index=False).agg(source_accuracy=("correct","mean"),
  mean_margin=("margin","mean"),mean_source_distance=("d_source","mean"))
 grouped.to_csv(OUT/"pooled.csv",index=False)
 by=core.groupby(["param","bits"],as_index=False).agg(source_accuracy=("correct","mean"),
  mean_margin=("margin","mean"),mean_source_distance=("d_source","mean"))
 by.to_csv(OUT/"by_param.csv",index=False)
 swap=raw[raw["swap_test"]==1].groupby(["source","nominal_receiver"],as_index=False).agg(correct=("correct","mean"),mean_margin=("margin","mean"))
 swap.to_csv(OUT/"swap_matrix.csv",index=False)
 payload={"experiment":"state_source_permutation_v18","design":{"blind_parameter_points":6,"seeds":10,"sources":3,
  "future_input":"exactly zero","receiver_memory_and_pressure":"common three-history mean","bits":[0,3,4,6]},
  "pooled":grouped.to_dict("records"),"by_param":by.to_dict("records"),"swap_matrix":swap.to_dict("records")}
 (OUT/"summary.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
 print("POOLED"); print(grouped.to_string(index=False)); print("\nSWAP"); print(swap.to_string(index=False))

if __name__=="__main__": main()