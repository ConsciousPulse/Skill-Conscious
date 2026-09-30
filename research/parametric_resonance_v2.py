from pathlib import Path
import itertools,json
import numpy as np,pandas as pd
from src.ontto.parametric_v2_core import *

OUT=Path("results/parametric_resonance_v2"); OUT.mkdir(parents=True,exist_ok=True)
CENTER={"beta_memory":0.998891,"relaxation":1.1375,"pressure_gain":0.175,"cross_gain":0.25}
SEEDS=list(range(20))

def main():
    # Second zoom around the v1 resonance ridge.
    bs=np.round(np.linspace(0.99810,0.99945,25),6)
    rs=np.round(np.linspace(1.07,1.205,10),6)
    ps=np.round(np.linspace(0.125,0.225,6),6)
    xs=np.round(np.linspace(0.15,0.35,5),6)
    rows=[score({"beta_memory":float(b),"relaxation":float(r),"pressure_gain":float(p),"cross_gain":float(x)})
          for b,r,p,x in itertools.product(bs,rs,ps,xs)]
    z=pd.DataFrame(rows).sort_values("score",ascending=False)
    z.to_csv(OUT/"zoom2.csv",index=False)
    cand={k:float(z.iloc[0][k]) for k in CENTER}
    # Boundary scan at the best local point.
    fb=np.round(np.linspace(0.9965,0.99949,100),6)
    fr=[]
    for b in fb:
        p={**cand,"beta_memory":float(b)}; c=make_cfg(p)
        fr.append({**p,"path_gap":path_gap(c,0,0),"critical_lift":critical_lift(c,0,0)})
    f=pd.DataFrame(fr); f.to_csv(OUT/"fine_boundary.csv",index=False)
    fits={}
    for name,d in {"minus":-0.025,"center":0.0,"plus":0.025}.items():
        p={**cand,"pressure_gain":float(np.clip(cand["pressure_gain"]+d,0.01,0.8))}
        gaps=[path_gap(make_cfg({**p,"beta_memory":float(b)}),0,0) for b in fb]
        fits[name]=expfit(fb,np.asarray(gaps))
    # Mechanism ablation, two independent path protocols and two critical protocols.
    ablations={"full":{},"no_memory":{"use_memory":False},"no_pressure":{"use_pressure":False},
               "no_cross":{"use_cross":False},"no_x":{"use_x":False},"no_attractor":{"use_attractor":False}}
    ar=[]
    for name,flags in ablations.items():
        for seed in SEEDS:
            c=make_cfg(cand,0.01,**flags)
            ar.append({"label":name,"seed":seed,
                "path_gap":float(np.mean([path_gap(c,seed,k) for k in (0,4)])),
                "critical_lift":float(np.mean([critical_lift(c,seed,k) for k in (0,4)]))})
    a=pd.DataFrame(ar); a.to_csv(OUT/"ablations.csv",index=False)
    full=a[a.label=="full"]; asum=[]
    for name in ablations:
        q=a[a.label==name]
        asum.append({"label":name,"path_gap_mean":float(q.path_gap.mean()),
            "path_gap_sd":float(q.path_gap.std(ddof=1)),
            "critical_lift_mean":float(q.critical_lift.mean()),
            "critical_lift_sd":float(q.critical_lift.std(ddof=1)),
            "path_gap_retention":float(q.path_gap.mean()/max(full.path_gap.mean(),1e-12)),
            "critical_lift_retention":float(q.critical_lift.mean()/max(full.critical_lift.mean(),1e-12))})
    asumf=pd.DataFrame(asum); asumf.to_csv(OUT/"ablation_summary.csv",index=False)
    # Six-protocol, 20-seed validation against baseline.
    cv=pd.DataFrame(validate(cand),columns=["seed","protocol","path_gap","critical_lift"])
    bp={"beta_memory":0.92,"relaxation":0.32,"pressure_gain":0.55,"cross_gain":0.85}
    bv=pd.DataFrame(validate(bp),columns=cv.columns)
    cv.to_csv(OUT/"candidate_validation.csv",index=False); bv.to_csv(OUT/"baseline_validation.csv",index=False)
    bidx=int(f.path_gap.idxmax())
    summary={"experiment":"parametric_resonance_v2","v1_center":CENTER,"candidate":cand,
      "zoom2_points":int(len(z)),"zoom2_top20":z.head(20).to_dict("records"),
      "fine_max":{"beta":float(f.loc[bidx,"beta_memory"]),"path_gap":float(f.loc[bidx,"path_gap"]),
        "critical_lift":float(f.loc[bidx,"critical_lift"])},"exponential_fits":fits,
      "ablation_summary":asum,"candidate_validation":{
        "path_gap_mean":float(cv.path_gap.mean()),"path_gap_sd":float(cv.path_gap.std(ddof=1)),
        "critical_lift_mean":float(cv.critical_lift.mean()),"critical_lift_sd":float(cv.critical_lift.std(ddof=1)),
        "positive_fraction":float(np.mean(cv.critical_lift>0)),"min_critical_lift":float(cv.critical_lift.min())},
      "baseline_validation":{
        "path_gap_mean":float(bv.path_gap.mean()),"path_gap_sd":float(bv.path_gap.std(ddof=1)),
        "critical_lift_mean":float(bv.critical_lift.mean()),"critical_lift_sd":float(bv.critical_lift.std(ddof=1)),
        "positive_fraction":float(np.mean(bv.critical_lift>0)),"min_critical_lift":float(bv.critical_lift.min())}}
    summary["candidate_vs_baseline"]={
      "path_gap_amplification":summary["candidate_validation"]["path_gap_mean"]/max(summary["baseline_validation"]["path_gap_mean"],1e-12),
      "critical_lift_ratio":summary["candidate_validation"]["critical_lift_mean"]/max(summary["baseline_validation"]["critical_lift_mean"],1e-12)}
    summary["interpretation"]="V2 maps the local resonance ridge, tests exponential scaling on nearby pressure slices, and ablates mechanisms. These are computational observables, not proof of consciousness."
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    print("="*88); print("CONSCIENCIA PARA IA  PARAMETRIC RESONANCE V2"); print("="*88)
    print("CANDIDATE",json.dumps(cand)); print("EXP_FITS",json.dumps(fits))
    print("ABLATIONS"); print(asumf.to_string(index=False))
    print("CANDIDATE_VALIDATION",json.dumps(summary["candidate_validation"]))
    print("BASELINE_VALIDATION",json.dumps(summary["baseline_validation"]))
    print("AMPLIFICATION",json.dumps(summary["candidate_vs_baseline"]))
if __name__=="__main__": main()
