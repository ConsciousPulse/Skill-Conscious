from pathlib import Path
import json, numpy as np, pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from src.ontto.dynamics import Config, simulate

OUT=Path("results/state_geometry_probe_generalization_v46"); OUT.mkdir(parents=True,exist_ok=True)
P=[
("p1",.9967,1.15,.125,.15),("p2",.9971,1.20,.150,.20),
("p3",.9976,1.10,.125,.20),("p4",.9979,1.18,.150,.15),
("p5",.9982,1.12,.175,.20),("p6",.9989,1.18,.150,.20)]
H=range(800,810); NS=range(20400,20402); N=300; F=60; S=5
PROBES={"A":np.r_[np.ones(10),-np.ones(10),np.zeros(10),.5*np.ones(10),-.5*np.ones(10),np.zeros(10)],
"B":np.r_[np.zeros(10),np.ones(10),np.zeros(10),-np.ones(10),.25*np.ones(10),np.zeros(10)],
"C":np.r_[.5*np.ones(10),np.zeros(10),-np.ones(10),np.zeros(10),.75*np.ones(10),-.25*np.ones(10)]}

def hist(k,seed):
 r=np.random.default_rng(seed+1000*k)
 if k==0:return np.ones(N),-np.ones(N)
 if k==1:return np.where(np.arange(N)%2==0,1.,-1.),np.ones(N)
 if k==2:return np.where(r.random(N)<.12,-1.,1.),np.where(r.random(N)<.06,1.,-1.)
 return np.sign(np.sin(np.linspace(0,18*np.pi,N))),np.sign(np.sin(np.linspace(0,6*np.pi,N)+1.7))
def ctx(cfg,seed,k):
 a=simulate(np.r_[hist(k,seed)[0],np.zeros(F)],cfg,seed=seed); b=simulate(np.r_[hist(k,seed)[1],np.zeros(F)],cfg,seed=seed+77); i=N
 return {"state_prev":float((a["state"][i-2]+b["state"][i-2])/2),"state":float((a["state"][i-1]+b["state"][i-1])/2),"memory":float((a["memory"][i-1]+b["memory"][i-1])/2),"pressure":float((a["pressure"][i-1]+b["pressure"][i-1])/2)}
def feat(run):
 x=run["state"][::S].astype(float); return x/max(np.linalg.norm(x),1e-12)
def run(cfg,c,probe,seed): return simulate(probe,cfg,seed=seed,initial_prev_state=c["state_prev"],initial_state=c["state"],initial_memory=c["memory"],initial_pressure=c["pressure"])
def fit(X,y):
 m=Pipeline([("z",StandardScaler()),("c",LogisticRegression(max_iter=2000,random_state=0))]);m.fit(X,y);return m

def main():
 rows=[]
 for pi,(name,beta,rel,pg,cg) in enumerate(P):
  cfg=Config(beta_memory=beta,relaxation=rel,pressure_gain=pg,cross_gain=cg,noise_std=.01)
  for held_probe in PROBES:
   X=[];y=[]
   for qi in range(6):
    if qi==pi:continue
    cfg2=Config(beta_memory=P[qi][1],relaxation=P[qi][2],pressure_gain=P[qi][3],cross_gain=P[qi][4],noise_std=.01)
    for pr in PROBES:
     if pr==held_probe:continue
     for k in range(4):
      for hs in H:
       c=ctx(cfg2,hs,k)
       for ns in NS:
        X.append(feat(run(cfg2,c,PROBES[pr],ns+hs)));y.append(k)
   m=fit(np.asarray(X),np.asarray(y))
   yy=[];pp=[]
   for k in range(4):
    for hs in H:
     c=ctx(cfg,hs,k)
     for ns in NS:
      yy.append(k);pp.append(int(m.predict(feat(run(cfg,c,PROBES[held_probe],ns+hs)).reshape(1,-1))[0]))
   rows.append({"held_param":name,"held_probe":held_probe,"accuracy":float(np.mean(np.asarray(yy)==pp))})
 df=pd.DataFrame(rows); df.to_csv(OUT/"cross_probe_accuracy.csv",index=False)
 summary={"experiment":"state_geometry_probe_generalization_v46","reference_free":True,"chance":.25,"held_out_parameters":6,"held_out_probes":3,
 "mean_accuracy":float(df.accuracy.mean()),"sd_accuracy":float(df.accuracy.std(ddof=1)),"fold_min":float(df.accuracy.min()),"fold_max":float(df.accuracy.max()),
 "protocol":"For each held-out parameter and held-out probe, the classifier trains on the other five parameters and the other two deterministic probes, then predicts the unseen probe from future state trajectory only."}
 (OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
