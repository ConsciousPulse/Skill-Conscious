from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_recovery_v20");OUT.mkdir(parents=True,exist_ok=True)
PARAMS=[
 {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
 {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
 {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
 {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
 {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
 {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
SEEDS=range(10); N=300; FUTURE=180; WINDOW=60

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

def dist(run,ref,start=0): return float(np.mean(np.abs(run["state"][start:start+WINDOW]-ref["state"][start:start+WINDOW])))

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
     # Start from an erased state, then restore the donor state after a delay.
     base=dict(common)
     intact=ra if donor_name=="A" else rb
     ref_other=rb if donor_name=="A" else ra
     expected=1 if donor_name=="A" else -1
     for delay in [0,5,10,20,40,80]:
      run_full=cont(cfg,base,seed)
      # Manual delayed restoration by first simulating from common context, then restarting from donor state at delay.
      first=cont(cfg,base,seed)
      idx=min(delay,FUTURE-2)
      donor_ctx=donor
      tail=simulate(np.zeros(FUTURE-idx),cfg,seed=seed,initial_prev_state=donor_ctx["state_prev"],
                    initial_state=donor_ctx["state"],initial_memory=first["memory"][idx],initial_pressure=first["pressure"][idx])
      # Concatenate history from erased phase with recovered donor-state tail.
      combined=np.concatenate([first["state"][:idx],tail["state"]])
      dr=float(np.mean(np.abs(combined[:WINDOW]-(intact["state"][:WINDOW]))))
      do=float(np.mean(np.abs(combined[:WINDOW]-(ref_other["state"][:WINDOW]))))
      x=float((do-dr)/max(do+dr,1e-12))
      rows.append({"param":pp["name"],"pair":pair,"seed":seed,"donor":donor_name,"delay":delay,
                   "affinity":x,"correct":int(np.sign(x)==expected),"abs_affinity":abs(x)})
 raw=pd.DataFrame(rows);raw.to_csv(OUT/"raw.csv",index=False)
 pooled=raw.groupby("delay",as_index=False).agg(identity_accuracy=("correct","mean"),
  abs_affinity=("abs_affinity","mean"),affinity=("affinity","mean"))
 by=raw.groupby(["param","delay"],as_index=False).agg(identity_accuracy=("correct","mean"),
  abs_affinity=("abs_affinity","mean"),affinity=("affinity","mean"))
 pooled.to_csv(OUT/"pooled.csv",index=False);by.to_csv(OUT/"by_param.csv",index=False)
 payload={"experiment":"state_recovery_v20","design":{"blind_parameter_points":6,"history_pairs":4,"seeds_per_pair":10,
 "delays":[0,5,10,20,40,80],"future_input":"zero","intervention":"erase state initially, restore donor state after delay"},
 "pooled":pooled.to_dict("records"),"by_param":by.to_dict("records")}
 (OUT/"summary.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
 print(pooled.to_string(index=False))

if __name__=="__main__": main()