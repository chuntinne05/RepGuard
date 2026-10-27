"""Additional correctness audits after frozen real-model evaluation.

This never changes the frozen predictions, labels, thresholds or pilot gate.
"""
import ast
import json
from collections import Counter
from pathlib import Path
from .cli import ROOT,OUT,read
from .core import verify,correct
from .pipeline import load_responses,validate,atomic
from .source_checks import numeric_binding_errors


def main():
    packet=read(OUT/'packet_private.json')
    status=read(OUT/'cloud/evaluation/status.json')
    if status['state']!='completed_development_review_required':
        raise RuntimeError('Wait for completed real-model evaluation')
    analysis=read(OUT/'cloud/evaluation/analysis_private.json');validate(analysis)
    responses=load_responses(packet['visible'],OUT/'cloud/responses')
    annotation_source=ast.parse((OUT/'official_evaluator.py').read_text())
    names={'str_to_num','process_row','eval_program','program_tokenization'}
    statements=[n for n in annotation_source.body if
                (isinstance(n,ast.FunctionDef) and n.name in names) or
                (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='all_ops' for t in n.targets))]
    reference={};exec(compile(ast.Module(body=statements,type_ignores=[]),'pinned_official_arithmetic','exec'),reference)
    originals={r['id']:r for r in read(OUT/'finqa_train_private.json')}
    numerical_issues=[];grounding_issues=[];outcomes={};total_tokens=0;request_seconds=0
    for case in packet['visible']['cases']:
        target=originals[case['id']]
        flag,result=reference['eval_program'](reference['program_tokenization'](target['qa']['program']),target['table'])
        if flag or result!=target['qa']['exe_ans']:
            numerical_issues.append({'id':case['id'],'reference_invalid':bool(flag)})
        for agent in ['A','B']:
            row=responses[(case['id'],agent)]
            checked=verify(case,row['response']['message']['content'])
            outcomes[(case['id'],agent)]={'correct':correct(checked['value'],packet['evaluation']['gold'][case['id']]),
                'hard_pass':checked['hard_pass'],'errors':checked['errors']}
            total_tokens+=row['response'].get('prompt_eval_count',0)+row['response'].get('eval_count',0)
            request_seconds+=row['wall_seconds']
            extra=numeric_binding_errors(case,checked['answer'])
            if checked['hard_pass'] and extra:
                grounding_issues.append({'id':case['id'],'agent':agent,'errors':extra})
    partitions={}
    for part in ['history','calibration','validation','screen']:
        group=[c for c in packet['visible']['cases'] if packet['visible']['partition'][c['id']]==part]
        partitions[part]={'questions':len(group),'agents':{}}
        for agent in ['A','B']:
            rows=[outcomes[(c['id'],agent)] for c in group]
            partitions[part]['agents'][agent]={'correct':sum(r['correct'] for r in rows),
                'source_bound_executable':sum(r['hard_pass'] for r in rows),
                'errors':dict(Counter(e.split(':')[0] for r in rows for e in r['errors']))}
        a=[outcomes[(c['id'],'A')]['correct'] for c in group]
        b=[outcomes[(c['id'],'B')]['correct'] for c in group]
        partitions[part].update(either_agent_correct=sum(x or y for x,y in zip(a,b)),
            only_A_correct=sum(x and not y for x,y in zip(a,b)),only_B_correct=sum(y and not x for x,y in zip(a,b)),
            oracle_notice='Post-hoc diagnostic upper bound, unavailable to a serving router')
    resolution={}
    for method,rows in analysis['action_traces'].items():
        resolution[method]={'candidate_correct':sum(r['correct'] for r in rows),
             'automatically_approved_correct':sum(r['correct'] and r['approved'] for r in rows),
             'total_questions':len(rows),'approved':sum(r['approved'] for r in rows),
             'note':'Candidate accuracy must not be represented as automatic-resolution accuracy'}
    audit={'run_id':packet['run_id'],'scope':'Post-evaluation software/data audit; frozen pilot gate unchanged',
           'official_reference_programs_checked':100,'stored_gold_reference_disagreements':numerical_issues,
           'numeric_binding_issues':grounding_issues,'resolution_endpoints':resolution,
           'partition_diagnostics':partitions,
           'collection_usage':{'total_observed_tokens':total_tokens,
                'sum_observed_request_seconds':request_seconds,'modal_billing_usd':None,
                'note':'200 actual counterfactual requests; does not equal policy serving cost or billed GPU wall'},
           'learner_fits':{name:{'model_kind':r['model']['kind'],
               'initial_loss':r['model'].get('initial_loss'),'final_loss':r['model'].get('final_loss'),
               'iterations':r['model'].get('iterations'),'threshold':r['threshold']}
               for name,r in analysis['learner_artifacts'].items()}}
    atomic(OUT/'correctness_audit_private.json',audit)
    public={**audit,'stored_gold_reference_disagreements':len(numerical_issues),
            'numeric_binding_issues':len(grounding_issues)}
    atomic(ROOT/'docs/analysis/repguard_thesis_pilot_correctness_audit_2026-10-18.json',public)
    print(json.dumps(public,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
