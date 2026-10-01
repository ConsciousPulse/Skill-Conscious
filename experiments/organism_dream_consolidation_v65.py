from __future__ import annotations
import argparse, json, re, shutil
from pathlib import Path
import numpy as np
from src.ontto.bridge import DynamicStateBridge
from src.ontto.dynamics import Config as DynamicsConfig
from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore

POS="EXPERIENCE_POSITIVE route was stable."
NEG="EXPERIENCE_NEGATIVE route was unstable."
LESSON="CONSOLIDATED_LESSON stable route repeated."
CAND=(-1.0,1.0)

class Provider:
    def __init__(self):
        self.phase="wake"; self.label="positive"
    def chat(self,messages,temperature=0.7):
        ctx="\n".join(m.get("content","") for m in messages if isinstance(m,dict))
        if self.phase=="wake":
            return LLMResponse(text=f"MEMORY: {POS if self.label=='positive' else NEG}\nSELF_MODEL: I preserve continuity across experience.",raw={"phase":"wake"})
        p=ctx.count("EXPERIENCE_POSITIVE"); n=ctx.count("EXPERIENCE_NEGATIVE")
        return LLMResponse(text=f"MEMORY: {LESSON if p>=n else 'CONSOLIDATED_LESSON instability repeated.'}\nSELF_MODEL: Durante el sueño consolido las experiencias recientes.\nDREAM_SUMMARY: consolidation.",raw={"phase":"dream","p":p,"n":n})

def base_db(path,seed,warmup,experiences):
    s=MemoryStore(path)
    cfg=OrganismConfig(agent_id="receiver",dynamic_seed=seed,dream_every_cycles=10000,event_limit=16,self_observer_enabled=True,self_selection_enabled=False,semantic_dynamic_bridge_enabled=False,semantic_self_model_bridge_enabled=False,dream_semantic_bridge_enabled=False)
    p=Provider(); o=PersistentOrganism(cfg,s,p,lambda _:None)
    for _ in range(warmup):
        o.autonomous_wake_cycle()
    for i in range(experiences):
        p.phase="wake"; p.label="positive" if i < int(experiences*0.75) else "negative"
        o.wake_cycle(f"experience {i}")
    s.add_memory("receiver",POS,importance=.65); s.add_memory("receiver",NEG,importance=.65); s.save_state("receiver",o.state); s.conn.close()

def oracle(state,seed):
    b=DynamicStateBridge(DynamicsConfig(),seed=seed); out={}
    for sig in CAND:
        q=b.advance(previous_state=state.dynamic_prev_state,state=state.dynamic_state,memory=state.dynamic_memory,pressure=state.dynamic_pressure,signal=sig,steps=1,step_index=state.dynamic_steps)
        out[sig]=(abs(q.state),q.state)
    sig=min(CAND,key=lambda z:(out[z][0],abs(z)))
    return sig,out[sig][0]

def arm(db,seed,mode,cycles):
    s=MemoryStore(db); bridge=mode=="dream_bridge"; do_dream=mode!="no_dream"
    cfg=OrganismConfig(agent_id="receiver",dynamic_seed=seed,dream_every_cycles=10000,event_limit=16,self_observer_enabled=True,self_selection_enabled=True,self_selection_policy="self_model",self_selection_attractor_weight=.55,self_selection_coherence_weight=.45,self_selection_signals=CAND,semantic_dynamic_bridge_enabled=False,semantic_self_model_bridge_enabled=False,dream_semantic_bridge_enabled=bridge,dream_semantic_bridge_scale=1.0,dream_semantic_bridge_importance=.65)
    p=Provider(); o=PersistentOrganism(cfg,s,p,lambda _:None)
    before=s.load_state("receiver"); pre=before.dynamic_state
    ev=None
    if do_dream:
        p.phase="dream"; o.dream_cycle(); ev=s.recent_events("receiver",1)[0]
    after=s.load_state("receiver"); regrets=[]; hits=[]
    for _ in range(cycles):
        st=s.load_state("receiver"); os,od=oracle(st,seed); o.autonomous_wake_cycle(); a=s.load_state("receiver"); chosen=float(s.recent_events("receiver",1)[0]["payload"]["self_selection"]["chosen_signal"]); regrets.append(abs(a.dynamic_state)-od); hits.append(chosen==os)
    s.conn.close()
    return {"mode":mode,"pre":pre,"post":after.dynamic_state,"dream_delta":after.dynamic_state-pre,"mean_regret":float(np.mean(regrets)),"oracle_hit_rate":float(np.mean(hits)),"dream_event":ev["payload"] if ev else None}

def pval(x,seed):
    x=np.asarray(x,float); rng=np.random.default_rng(seed); obs=abs(float(x.mean())); z=rng.choice([-1.,1.],size=(20000,len(x))); null=np.abs((z*x).mean(1)); return float((np.count_nonzero(null>=obs)+1)/20001)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--replicates",type=int,default=24); ap.add_argument("--warmup",type=int,default=8); ap.add_argument("--experiences",type=int,default=8); ap.add_argument("--cycles",type=int,default=24); ap.add_argument("--out",default="results/organism_dream_consolidation_v65"); a=ap.parse_args()
    out=Path(a.out); shutil.rmtree(out,ignore_errors=True); out.mkdir(parents=True)
    rows=[]
    for r in range(a.replicates):
        seed=8501+r; b=out/f"base_{r}.db"; base_db(b,seed,a.warmup,a.experiences); arms={}
        for mode in ("no_dream","dream_no_bridge","dream_bridge"):
            db=out/f"{mode}_{r}.db"; shutil.copy2(b,db); arms[mode]=arm(db,seed,mode,a.cycles)
        rows.append({"replicate":r,"arms":arms,"bridge_regret":arms["dream_no_bridge"]["mean_regret"]-arms["dream_bridge"]["mean_regret"],"bridge_hit":arms["dream_bridge"]["oracle_hit_rate"]-arms["dream_no_bridge"]["oracle_hit_rate"],"dream_vs_no_dream":arms["dream_no_bridge"]["mean_regret"]-arms["no_dream"]["mean_regret"]})
    br=np.array([x["bridge_regret"] for x in rows]); bh=np.array([x["bridge_hit"] for x in rows]); dn=np.array([x["dream_vs_no_dream"] for x in rows])
    def m(mode,k): return float(np.mean([x["arms"][mode][k] for x in rows]))
    summary={"experiment":"organism_dream_consolidation_v65","replicates":a.replicates,"warmup_cycles":a.warmup,"experience_cycles":a.experiences,"evaluation_cycles":a.cycles,"mean_regret":{m0:m(m0,"mean_regret") for m0 in ("no_dream","dream_no_bridge","dream_bridge")},"oracle_hit_rate":{m0:m(m0,"oracle_hit_rate") for m0 in ("no_dream","dream_no_bridge","dream_bridge")},"dream_state_delta_mean":{m0:m(m0,"dream_delta") for m0 in ("no_dream","dream_no_bridge","dream_bridge")},"dream_bridge_regret_advantage":float(br.mean()),"paired_sign_flip_p_dream_bridge_regret":pval(br,65002),"dream_bridge_hit_advantage":float(bh.mean()),"paired_sign_flip_p_dream_bridge_hit":pval(bh,65003),"dream_vs_no_dream_regret_change":float(dn.mean()),"paired_sign_flip_p_dream_vs_no_dream_regret":pval(dn,65004),"all_dream_bridge_runs_have_bridge":all(x["arms"]["dream_bridge"]["dream_event"] is not None for x in rows)}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)); (out/"runs.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False)); print(json.dumps(summary,indent=2,ensure_ascii=False))
if __name__=="__main__": main()
