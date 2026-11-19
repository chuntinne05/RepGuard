"""Register a metadata-selected native SQL development/readiness study."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import zipfile

from .runtime import INSTRUCTION, MODELS, digest, sha, write


def main():
    root = Path(__file__).resolve().parents[2]; out = root / 'results/specbridge_v6'
    dest = out / 'registered_plan.json'
    if dest.exists(): raise RuntimeError('Never overwrite registration')
    qualification = json.loads((out / 'qualification.json').read_text())
    if not qualification['go_for_bounded_development_baseline']: raise RuntimeError('Qualification gate failed')
    source = root / 'results/relational_v5/source_intake/SpecBridge'
    split = json.loads((source / 'metadata_split.json').read_text())
    dev = [r for r in split['metadata'] if r['split'] == 'development']
    key = lambda r: digest(['specbridge-v6-20261109', r['id']])
    selected = []; counts = Counter()
    # Metadata-only diversity, no reference SQL/results in sample selection.
    types = Counter(r['choice_type'] for r in dev)
    for kind in sorted(types, key=lambda k:(types[k],k)):
        candidates = sorted((r for r in dev if r['choice_type'] == kind and counts[r['database']] < 4), key=key)
        if candidates:
            row = candidates[0]; selected.append(row); counts[row['database']] += 1
    for db in sorted({r['database'] for r in dev}):
        candidates = sorted((r for r in dev if r['database'] == db and r not in selected), key=key)
        selected.extend(candidates[:4-counts[db]])
    selected.sort(key=key)
    if len(selected) != 12 or any(n != 4 for n in Counter(r['database'] for r in selected).values()):
        raise RuntimeError('Selection balance failed')
    cases = []
    for row in selected:
        public = json.loads((source / 'public/development' / (row['id'] + '.json')).read_text())
        if set(public) != {'id','database','requests','context'}:
            raise RuntimeError('Unexpected public prompt fields')
        for reading in ('A','B'):
            cases.append({'case_id':row['id']+'__'+reading,'task_id':row['id'],'reading':reading,
                          'database':row['database'],'question':public['requests']['specific_'+reading],'context':public['context']})
    packet = {'cases':cases}
    write(out / 'public_packet.json', packet)
    runtime_names = ('__init__.py','runtime.py','worker.py')
    database_receipt = json.loads((source / 'external_preparation.json').read_text())
    plan = {'registered_utc':datetime.now(timezone.utc).isoformat(),'study':'SpecBridge_v6_native_development_readiness',
            'purpose':'Native producer/self/cross execution feasibility and actual error bank, NOT proof of V5 checker effectiveness or new-method superiority.',
            'selected_tasks':selected,'selection':'Rare-choice metadata first then hash fill;4tasks perdevelopmentDB;bothspecified interpretations;no model outcomes/reference SQL consulted for selection',
            'task_count':12,'specified_cases':24,'database_count':3,'choice_types':dict(Counter(r['choice_type'] for r in selected)),
            'models':MODELS,'workflows':['A','B','AA','BB','AB','BA'],'max_model_calls':144,'calls_per_new_trajectory':1,
            'policy_calls_including_parent':{'A':1,'B':1,'AA':2,'BB':2,'AB':2,'BA':2},
            'runtime_sqlite':'3.42.0','sqlean':'0.21.5.3','ollama':'0.40.6','context':32768,'max_output':8192,'temperature':0,'seed':20261109,'thinking':False,
            'review_information':'Original specified request/schema/docs plus actual earlier SQL/rawresponse and execution state/8rowpreview. Earlier model identity hidden. No grader labels, expected values or reference SQL.',
            'automatic_generation_retries':0,'stop_policy':'Provider/transport/integrity exception stops corpus, unresolved attempts never blindly repeated; invalidJSON/SQL scored as failed task, no extra generation.',
            'primary_readout':'Descriptive native interpretation correctness perworkflow, paired rescues/harms and taskwise counts; no significance/superiority claim from12tasks/3DB.',
            'frontier_baseline':'Gemini3.8Flash synthetic timeout120s with unknown provider outcome; no corpus sent, no blind retry; frontier baseline missing.',
            'v5_checker_used':False,'scientific_expansion_gate':'NOT_OPENED','history_fitted':False,'human_annotations_added':0,
            'public_packet_digest':digest(packet),'public_packet_file_sha256':sha(out/'public_packet.json'),
            'qualification_sha256':sha(out/'qualification.json'),'instruction':INSTRUCTION,
            'source_databases':database_receipt['downloaded_development_databases'],
            'source_hashes':{str(p.relative_to(root)):sha(p) for p in Path(__file__).parent.glob('*.py')},
            'runtime_hashes':{n:sha(Path(__file__).parent/n) for n in runtime_names},
            'reserved_validation_or_confirmation_used':False,'upstream_source_revision':database_receipt['revision']}
    plan['plan_id'] = digest(plan)[:24]
    write(dest, plan); write(root/'docs/reports/2026-11-09/registered_specbridge_v6.json', plan)
    with zipfile.ZipFile(out/'frozen_source.zip','x',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in plan['source_hashes']: archive.write(root/path,path)
    print(json.dumps({k:plan[k] for k in ('plan_id','task_count','specified_cases','choice_types','max_model_calls')},indent=2))


if __name__ == '__main__': main()
