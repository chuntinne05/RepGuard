"""Engineering examples and a read-only replay over actual frozen research files.

Synthetic examples, controlled mutations and natural recorded claims are labeled
separately. This is not a model experiment or a cross-domain effectiveness study.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from repguard.verification import Candidate, Contract, EvidenceStore, Fact, Operand, Scope, verify
from repguard.verification.adapters import json_pointer_fact

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/general_verification_v1"
REPORT = ROOT / "docs/reports/2026-11-09"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")


def scope(entity, metric, period="2026-Q3", population="all_records", state="observed", **qualifiers):
    return Scope(entity=entity,metric=metric,period=period,population=population,state=state,qualifiers=qualifiers)


def base(domain, metric, unit, old, new, claimed):
    before=scope(domain,metric,period="2026-Q2")
    after=scope(domain,metric)
    facts=[Fact(id="old",value=old,unit=unit,scope=before,source_id="source-old",snapshot_sha256="a"*64,
                locator="/value",root_ids=("original-old",)),
           Fact(id="new",value=new,unit=unit,scope=after,source_id="source-new",snapshot_sha256="b"*64,
                locator="/value",root_ids=("original-new",))]
    c=Contract(id=domain,question=f"Percentage change in {metric}?",authority_ref="synthetic-reviewed-fixture",
               approval="approved",operation="percent_change",operands={"old":Operand(scope=before,unit=unit),"new":Operand(scope=after,unit=unit)},
               output_unit="percent",absolute_tolerance="0.01")
    a=Candidate(claim_id=domain,value=claimed,unit="percent",bindings={"old":"old","new":"new"})
    return c,a,facts


def engineering_examples():
    examples=[]
    domains=[("sales_operations","delivered_orders","count","100","120","20"),
             ("research_reporting","latency","millisecond","200","180","-10"),
             ("financial_reporting","revenue","million_USD","80","100","25")]
    for args in domains:
        c,a,fs=base(*args)
        variants=[("correct",c,a,fs,["old","new"],"consistent"),
                  ("arithmetic_error",c,a.model_copy(update={"value":"999"}),fs,["old","new"],"inconsistent"),
                  ("wrong_percent_kind",c,a.model_copy(update={"unit":"percentage_point"}),fs,["old","new"],"inconsistent"),
                  ("contract_unreviewed",c.model_copy(update={"approval":"review_required"}),a,fs,["old","new"],"unresolved"),
                  ("unadmitted_source",c,a,fs,["old"],"unresolved")]
        for axis,value in [("entity","another_entity"),("metric","other_metric"),("period","2025-Q3"),
                           ("population","selected_subset"),("state","forecast")]:
            bad=[fs[0],fs[1].model_copy(update={"scope":fs[1].scope.model_copy(update={axis:value})})]
            variants.append(("wrong_"+axis,c,a,bad,["old","new"],"unresolved"))
        bad=[fs[0],fs[1].model_copy(update={"origin":"peer_assertion"})]
        variants.append(("peer_assertion_as_evidence",c,a,bad,["old","new"],"unresolved"))
        competing=fs+[fs[1].model_copy(update={"id":"conflict","value":"123","source_id":"competing"})]
        variants.append(("unresolved_conflict",c,a,competing,["old","new","conflict"],"unresolved"))
        for name,contract,candidate,facts,admitted,expected in variants:
            receipt=verify(contract,candidate,EvidenceStore(facts,admitted))
            assert receipt.verdict==expected,(args[0],name,receipt)
            record={"id":args[0]+"/"+name,"kind":"synthetic_engineering_fixture","expected":expected,
                    "receipt":receipt.model_dump(mode="json")}
            examples.append(record)
            if name=="correct":
                folder=OUT/'examples'/args[0]
                write(folder/'contract.json',contract.model_dump(mode="json"))
                write(folder/'candidate.json',candidate.model_dump(mode="json"))
                write(folder/'store.json',{"facts":[f.model_dump(mode="json") for f in facts],"admitted_fact_ids":admitted})
    # Exact workflow status: accepted/submitted do not imply completed effects.
    s=scope('release_pipeline','effect_status',period='attempt-1',state='execution_observed')
    c=Contract(id='release',question='Was execution completed?',authority_ref='synthetic-operation-spec',approval='approved',operation='lookup',
               operands={'value':Operand(scope=s,unit='status')},output_unit='status')
    f=Fact(id='state',value='submitted',unit='status',scope=s,source_id='execution-log',snapshot_sha256='c'*64,locator='/state',root_ids=('runtime',))
    for value,expected in [('submitted','consistent'),('completed','inconsistent')]:
        a=Candidate(claim_id='release',value=value,unit='status',bindings={'value':'state'})
        receipt=verify(c,a,EvidenceStore([f],['state']))
        assert receipt.verdict==expected
        examples.append({'id':'execution_status/'+value,'kind':'synthetic_engineering_fixture','expected':expected,'receipt':receipt.model_dump(mode='json')})
    write(OUT/'engineering_examples.json',examples)
    return examples


def real_artifact_replay():
    v2=ROOT/'results/arqa_v2/runs/deaee6167f9609bd2f045f46/analysis.json'
    v1=ROOT/'results/verification_v1/runs/1a97e7cca4367a1fe81c9417/analysis.json'
    plan='deaee6167f9609bd2f045f46';rows=[]

    def one(name,pointer,value,unit,fact_unit,tolerance='0'):
        s=scope('RepGuard',name,period='2026-11-09',population='ARQA24groups',plan_id=plan,readout='frozen')
        f=json_pointer_fact(v2,pointer,fact_id='actual',scope=s,unit=fact_unit,source_id='arqa-cycle02-analysis',root_ids=(plan,))
        c=Contract(id=name,question='Check the recorded cycle02 '+name,authority_ref='registered-plan:'+plan,approval='approved',
                   operation='lookup',operands={'value':Operand(scope=s,unit=fact_unit)},output_unit=unit,absolute_tolerance=tolerance)
        a=Candidate(claim_id=name,value=value,unit=unit,bindings={'value':'actual'})
        r=verify(c,a,EvidenceStore([f],['actual']))
        rows.append({'id':name,'kind':'real_recorded_artifact_claim','expected':'consistent','receipt':r.model_dump(mode='json')})
        assert r.verdict=='consistent',r
        return c,a,f

    one('responses','/calls','288','count','count')
    c,a,f=one('cross_self_delta','/contrasts/checklist/delta','2.08','percentage_point','ratio_difference','0.005')
    # Both cycles happen to have about+2.08pp. A numerical match alone cannot bind the run.
    other_scope=f.scope.model_copy(update={'population':'DG120pairs','qualifiers':(('plan_id','1a97e7cca4367a1fe81c9417'),('readout','frozen'))})
    other=json_pointer_fact(v1,'/primary_cross_minus_self_pp',fact_id='wrong-run',scope=other_scope,unit='percentage_point',source_id='DG-cycle01-analysis',root_ids=('1a97e7cca4367a1fe81c9417',))
    wrong=a.model_copy(update={'bindings':{'value':'wrong-run'}})
    r=verify(c,wrong,EvidenceStore([other],['wrong-run']))
    assert r.verdict=='unresolved'
    rows.append({'id':'same_number_wrong_real_run','kind':'controlled_mutation_over_real_artifacts','expected':'unresolved','receipt':r.model_dump(mode='json')})
    one('schema_validity','/schema_validity','95.14','percent','ratio','0.005')
    one('scientific_gate','/scientific_gate','FAIL_stop_scale_and_history','status','status')
    c,a,f=one('standard_A_correct_count','/metrics/standard~1A/correct','16','count','count')
    r=verify(c,a.model_copy(update={'value':'24'}),EvidenceStore([f],['actual']))
    assert r.verdict=='inconsistent'
    rows.append({'id':'incorrect_perfect_accuracy_claim','kind':'controlled_mutation_over_real_artifacts','expected':'inconsistent','receipt':r.model_dump(mode='json')})
    write(OUT/'real_artifact_replay.json',rows)
    return rows


def main():
    synthetic=engineering_examples();real=real_artifact_replay()
    summary={'created_utc':datetime.now(timezone.utc).isoformat(),'scope':'Engineering functionality only, not external cross-domain validation or method superiority.',
             'synthetic_cases':len(synthetic),'synthetic_workload_families':4,
             'real_recorded_artifact_claims':sum(r['kind']=='real_recorded_artifact_claim' for r in real),
             'controlled_mutations_over_real_artifacts':sum(r['kind']=='controlled_mutation_over_real_artifacts' for r in real),
             'all_expected_engineering_outcomes_observed':True,'new_model_calls':0,'new_human_annotations':0,
             'semantics_boundary':'Facts scoped/admitted and contracts approved by caller in these examples. Does not validate that NL parsing, metadata or original experiments are correct.'}
    write(REPORT/'general_verification_v1_engineering_results.json',summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
