"""A real prototype: source-grounded answers with history-aware delegation.

New question -> actual Modal Ollama inference -> actual arithmetic verification.
No cached screen response and no current-question gold is used by the controller.
"""
import argparse
import json
import math
import time
import uuid
from pathlib import Path
from .core import AGENTS,base_features,correct,digest,verify
from .analysis import predict,reputation
from .pipeline import jobs,validate,atomic
from .serving_checks import review_units

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'results/thesis_real_pilot_v2'
APP='repguard-thesis-real-pilot-20261018'


def run(case_index,question,mode,document=None,contract='frozen'):
    import modal
    if contract not in ['frozen','explicit_status','schema_prompt','typed_tools']:raise ValueError('Unknown live contract')
    if contract!='frozen' and mode!='always_b':raise ValueError('New contracts are uncalibrated B baselines only')
    history=[];scored={};context=None;public=None
    if contract=='frozen':
        packet=json.loads((OUT/'packet_private.json').read_text())
        artifact=json.loads((OUT/'cloud/evaluation/analysis_private.json').read_text());validate(artifact)
        context=artifact['learner_artifacts']['RepGuard']
        public=packet['visible'];history=[c for c in public['cases'] if public['partition'][c['id']]=='history']
        history_ids={c['id'] for c in history}
        for index,(agent,case) in enumerate(jobs(public)):
            if case['id'] not in history_ids:continue
            row=json.loads((OUT/f'cloud/responses/case_{index:04d}.json').read_text());validate(row)
            checks=verify(case,row['response']['message']['content'])
            # Only previously audited HISTORY targets enter live competence features.
            scored[(case['id'],agent['id'])]={'correct':correct(checks['value'],packet['evaluation']['gold'][case['id']])}
    elif document is None:
        public=json.loads((OUT/'cloud/responses/visible.json').read_text())
    case=(dict(document) if isinstance(document,dict) else json.loads(Path(document).read_text())) if document else dict(public['cases'][case_index])
    if question:case['question']=question
    case['id']='live-'+uuid.uuid4().hex
    def probability(agent_id,check):
        if contract!='frozen':return None
        x=base_features(case,check,agent_id)+reputation(case,agent_id,history,scored)
        p=predict(context['model'],x)
        return predict(context['calibrator'],[math.log(max(1e-6,p)/max(1e-6,1-p))])
    server=modal.Cls.from_name(APP,'LiveOllama')()
    def invoke(agent_id):
        return server.typed_solve.remote(case) if contract=='typed_tools' else server.solve.remote(case,agent_id,contract)
    results=[];first='B' if mode=='always_b' else 'A'
    result=invoke(first);result['verification']=review_units(result['verification']);result['estimated_correctness']=probability(first,result['verification']);results.append(result)
    threshold=context['threshold'] if context else None
    if mode=='repguard' and (not result['verification']['hard_pass'] or result['estimated_correctness']<threshold):
        result=invoke('B');result['verification']=review_units(result['verification']);result['estimated_correctness']=probability('B',result['verification']);results.append(result)
    check=result['verification']
    approved=check['hard_pass'] and (mode!='repguard' or result['estimated_correctness']>=threshold)
    report={'id':case['id'],'question':case['question'],'report':case['report'],
            'mode':mode,'contract':contract,'status':'candidate_with_checks' if approved else 'needs_review',
            'candidate':None if check.get('unit_review_required') else check['display_value'],
            'untrusted_display_value':check['display_value'],
            'mechanical_checks_passed':check['hard_pass'],'review_reasons':check['errors'],
            'estimated_correctness':result['estimated_correctness'],
            'probability_notice':('New contract has NO fitted correctness calibration' if contract!='frozen' else 'Small development-pilot calibration; NOT a correctness guarantee'),
            'selected_agent':result['agent'],'actual_model_calls':len(results),
            'input_tokens':sum(r['response'].get('prompt_eval_count',0) for r in results),
            'output_tokens':sum(r['response'].get('eval_count',0) for r in results),
            'sources':check['sources'],'program':check['answer'],'trace':results,
            'runtime_case_has_gold':False,'used_cached_solver_output':False,
            'uses_history_audits':len(history) if contract=='frozen' else 0,'created_epoch':time.time()}
    target=ROOT/'results/thesis_live_prototype'/f"{case['id']}.json";atomic(target,report)
    print(json.dumps({k:v for k,v in report.items() if k!='trace'},ensure_ascii=False,indent=2))
    print('Full actual response trace:',target)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',type=int,default=80)
    p.add_argument('--question');p.add_argument('--document',help='Gold-free JSON: id/report/question/table/pre_text/post_text')
    p.add_argument('--mode',choices=['repguard','always_a','always_b'],default='repguard')
    p.add_argument('--contract',choices=['frozen','explicit_status','schema_prompt','typed_tools'],default='frozen')
    args=p.parse_args()
    if not 0<=args.case<100:raise ValueError('Case index must be in0..99')
    run(args.case,args.question,args.mode,args.document,args.contract)
