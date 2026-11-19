"""Exploratory replay on REAL paired model responses; never live-policy evidence.

Adds a cheap execution-failure rule and a gold-only diagnostic upper bound.
Developed after8B/14Boutcomes and during27Bcollection, not preregistered before
generation. No learned reputation or extra model calls. GPU-eval cost proxy
excludes load/idle/CPU/memory and must not be called billing.
"""
import json
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from thesis_pilot.core import digest

def read(p):return json.loads(p.read_text())

def main():
    small='qwen3:14b';big='qwen3.5:27b'
    source=ROOT/'results/thesis_modern_backbone_control_v1';plan=read(source/'plan.json');summary=read(source/'summary.json');tt=read(source/'traces_private.json')['rows']
    assert read(source/'collection_complete.json')['actual_new_calls']==16
    methods={a:{'correct':0,'calls':0,'gpu_eval_cost_proxy_usd':0.,'rescue_vs_modern':0,'harm_vs_modern':0} for a in ['direct14b','direct27b','invalid_only_regenerate','oracle_keep_or_regenerate_DIAGNOSTIC']}
    rows=[]
    def gpu_cost(o,rate):
        r=o['response'];return rate*(r.get('prompt_eval_duration',0)+r.get('eval_duration',0))/1e9
    for c in plan['public_cases']:
        i=c['id'];h=digest(i)[:16]
        so=read(ROOT/f'results/thesis_backbone_diversity_probe_v1/responses/{h}_qwen3_14b.json')['output']
        bo=read(source/'responses'/f'{h}.json')['output']
        sy=tt[i][small]['correct'];by=tt[i][big]['correct'];sv=so['verification']['hard_pass'];bv=bo['verification']['hard_pass']
        sc=gpu_cost(so,.000222);bc=gpu_cost(bo,.000542)
        oracle_call=not sy and by  # Uses GOLD: explicitly not deployable.
        decisions={'direct14b':(sy,1,sc),'direct27b':(by,1,bc),
          'invalid_only_regenerate':((by if bv else sy) if not sv else sy,1+int(not sv),sc+bc*int(not sv)),
          'oracle_keep_or_regenerate_DIAGNOSTIC':((by if bv else sy) if oracle_call else sy,1+int(oracle_call),sc+bc*int(oracle_call))}
        for a,(y,calls,cost) in decisions.items():
            m=methods[a];m['correct']+=int(y);m['calls']+=calls;m['gpu_eval_cost_proxy_usd']+=cost
            m['rescue_vs_modern']+=int(y and not by);m['harm_vs_modern']+=int(by and not y)
        rows.append({'id':i,'small_correct':sy,'modern_correct':by,'small_valid':sv,'modern_valid':bv,
                     'rule_calls_modern':not sv,'oracle_calls_modern_GOLD_ONLY':bool(oracle_call),'gpu_eval_cost_proxy_small':sc,'gpu_eval_cost_proxy_modern':bc})
    for a,m in methods.items():m['mean_calls']=m['calls']/16;m['gpu_eval_cost_proxy_relative_to_direct27b']=m['gpu_eval_cost_proxy_usd']/methods['direct27b']['gpu_eval_cost_proxy_usd']
    result={'scope':'Exploratory replay/upper-bound analysis on actual cached responses, NOT a live learned policy or superiority test',
            'n':16,'new_model_calls':0,'methods':methods,'rows':rows,
            'pricing_source':'https://modal.com/pricing','pricing_as_of':'2026-10-19','GPU_rates_per_second_usd':{'L4':.000222,'L40S':.000542},
            'excluded_costs':['model load','container startup/idle','CPU','memory','storage','evaluation/audits','cold model reload and batching effects'],
            'rule_uses_gold':False,'oracle_uses_gold':True,'learned_reputation_implemented':False,'noninferiority_demonstrated':False,
            'interpretation':'Oracle bound only quantifies potential; a deployable controller must choose using public state/history and beat the rule/learned controls on new reports. If rule already explains gains, do not credit reputation.'}
    (HERE/'repguard_modern_routing_headroom_2026-10-19.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))

if __name__=='__main__':main()
