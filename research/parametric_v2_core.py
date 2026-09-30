from __future__ import annotations
import numpy as np
from src.ontto.dynamics import Config, simulate

def make_cfg(p, noise=0.0, **flags):
    return Config(beta_memory=p["beta_memory"], relaxation=p["relaxation"],
        pressure_gain=p["pressure_gain"], cross_gain=p["cross_gain"],
        noise_std=noise, **flags)

def path_gap(cfg, seed, protocol=0, steps=520):
    suffix=np.sin(np.linspace(0,4*np.pi,220))*0.7
    n=steps-len(suffix); rng=np.random.default_rng(seed+10000*protocol)
    if protocol==0: a=np.ones(n); b=-np.ones(n)
    elif protocol==1: a=np.where(np.arange(n)%2==0,1.,-1.); b=np.ones(n)
    elif protocol==2: a=np.where(rng.random(n)<.15,-1.,1.); b=np.where(rng.random(n)<.05,1.,-1.)
    elif protocol==3: a=np.sign(np.sin(np.linspace(0,18*np.pi,n))); b=np.sign(np.sin(np.linspace(0,6*np.pi,n)+1.7))
    elif protocol==4: a=np.where(np.arange(n)%7<3,1.,-1.); b=np.where(np.arange(n)%11<8,-1.,1.)
    else: a=np.sin(np.linspace(0,10*np.pi,n)); b=np.cos(np.linspace(0,6*np.pi,n))
    A=simulate(np.r_[a,suffix],cfg,seed=seed); B=simulate(np.r_[b,suffix],cfg,seed=seed)
    return float(np.mean(np.abs(A["state"][-180:]-B["state"][-180:])))
def critical_lift(cfg, seed, protocol=0, steps=800, warmup=250):
    u=np.zeros(steps)
    if protocol==0: u[120:180]=.7; u[350:430]=-1.; u[600:650]=.4
    elif protocol==1: u[80:130]=-.8; u[280:340]=1.; u[500:570]=.6; u[700:730]=-.4
    elif protocol==2: u[150:230]=np.linspace(0,1,80); u[420:500]=np.linspace(1,-1,80); u[650:690]=.8
    elif protocol==3: u[100:200]=np.sin(np.linspace(0,3*np.pi,100)); u[400:520]=-.6; u[650:760]=.5*np.sin(np.linspace(0,2*np.pi,110))
    elif protocol==4: u[140:220]=1.; u[300:390]=-.4; u[520:610]=.8; u[690:760]=-.9
    else: u[90:170]=np.sin(np.linspace(0,2*np.pi,80)); u[360:470]=np.linspace(-1,1,110); u[600:700]=-.3
    R=simulate(u,cfg,seed=seed); q=R["q"][warmup:]; c=R["cross"][warmup:]
    hi=c>=np.quantile(c,.75); lo=c<=np.quantile(c,.25)
    return float(np.mean((q=="X")[hi])-np.mean((q=="X")[lo]))
def score(p):
    c=make_cfg(p); g=path_gap(c,0,0); l=critical_lift(c,0,0)
    return {**p,"path_gap":g,"critical_lift":l,"score":g*max(l,0)}
def validate(p,seeds=range(20),protocols=range(6)):
    rows=[]
    for seed in seeds:
        c=make_cfg(p,.01)
        for k in protocols:
            rows.append((seed,k,path_gap(c,seed,k),critical_lift(c,seed,k)))
    return rows
def expfit(beta,gap,threshold=.9975):
    m=np.isfinite(beta)&np.isfinite(gap)&(gap>0)&(beta>=threshold)
    x=beta[m]; y=np.log(gap[m]); s,i=np.polyfit(x,y,1); pred=i+s*x
    r2=float(1-np.sum((y-pred)**2)/np.sum((y-y.mean())**2))
    return {"threshold":threshold,"n_points":int(len(x)),"log_slope":float(s),"r2":r2,"multiplier_per_0_01_beta":float(np.exp(.01*s))}
