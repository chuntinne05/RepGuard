"""Freeze a bounded engineering pilot after source/scorer preflight."""
from datetime import datetime,timezone
from pathlib import Path
import json

from .agent import INSTRUCTION,MODELS,digest,write
from .tools import sha,relation_fingerprint


def main():
    root=Path(__file__).resolve().parents[2];out=root/'results/workspace_v4';dest=out/'registered_plan.json'
    if dest.exists():raise RuntimeError('Never overwrite registration')
    ready=json.loads((out/'readiness_amendment.json').read_text())
    if not ready['all_source_checks_pass_after_declared_amendment']:raise RuntimeError('Source gate failed')
    packet=json.loads((out/'public_packet.json').read_text())
    runtime=('__init__.py','tools.py','agent.py','worker.py')
    plan={'registered_utc':datetime.now(timezone.utc).isoformat(),'study':'workspace_v4_adapted_dataspace_tool_readiness_pilot',
          'purpose':'Engineering feasibility and real error bank, NOT scientific superiority/transfer confirmation or a new-method result.',
          'tasks':[t['id'] for t in packet['tasks']],'input_amended_tasks':['task_391'],'source_group_warning':'6tasks,4coarse source families; fund/macro tasks overlap source schemas, not6independent domains.',
          'models':MODELS,'frontier_baseline':'Gemini4Argon synthetic diagnostic HTTP429quota0; absent from this engineering run, required later for strong-baseline confirmation.',
          'initial_call_cap':8,'review_call_cap':4,'initial_token_cap':64000,'review_token_cap':64000,
          'token_cap_semantics':'Observed input+output stop check after each non-final response; hard per-call context32768/output2048 and call caps. Realized tokens reported, no equal-realized-compute claim.',
          'max_model_calls':192,'final_workflows':['A','B','AA','BB','AB','BA'],'policy_call_ceilings':{'direct':8,'self_or_cross':12},
          'temperature':0,'seed':20261109,'thinking':False,'ollama':'0.40.6','gpu':'L40S','automatic_generation_retries':0,
          'operational_stop':'Any transport/provider/integrity exception stops collection; no unresolved started generation retried automatically. Tool/schema errors consume a new step.',
          'outcomes':['official relation score under declared input amendment','saved output completeness','source/execution lineage','tool/schema errors','calls/tokens/service time','paired cross-minus-self descriptive counts only'],
          'primary_descriptive':'balanced cross-vs-self task correctness contrast, no significance/superiority claim at6tasks',
          'scientific_expansion_gate':'NOT_OPENED; this run cannot authorize history, scientific confirmation or product safety claims.',
          'adaptations':['CSV/recordJSON and originalSQLite materialized into one source-traced SQL view','PDF extracted text with page IDs, no screenshot vision','task391explicit date output requirement added after source-only preflight','final output references actual exported table artifacts'],
          'oracle_boundary':'Published public references/scorer only offline; no gold/config/reference reconstruction code mounted in model or tool runtime.',
          'public_packet_digest':digest(packet),'public_packet_file_sha256':sha(out/'public_packet.json'),
          'runtime_hashes':{n:sha(Path(__file__).parent/n) for n in runtime},
          'source_hashes':{str(p.relative_to(root)):sha(p) for p in Path(__file__).parent.glob('*.py')},
          'derived_relation_sha256':{t['id']:relation_fingerprint(out/'derived_v2'/t['id']/'workspace.sqlite') for t in packet['tasks']},
          'instruction':INSTRUCTION,'human_annotations_added':0,'history_fitted':False}
    plan['plan_id']=digest(plan)[:24];write(dest,plan);write(root/'docs/reports/2026-11-09/registered_workspace_v4.json',plan)
    print(json.dumps({k:plan[k] for k in ('plan_id','registered_utc','tasks','max_model_calls','purpose')},indent=2))


if __name__=='__main__':main()
