"""Independent local verification of saved real responses. No network/inference."""
import hashlib
import json
import math
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from thesis_pilot.core import digest,correct
from thesis_pilot.causal_tools import messages as cm,verify as cv
from thesis_pilot.competence_tools import messages as nm,verify as nv
from thesis_pilot.pot_tools import messages as pm,verify as pv
from thesis_pilot.core import skill
from thesis_pilot.program_integrity_v2 import inspect_program
from repguard_unit_failure_diagnostic import surgery
from repguard_pot_format_control import canonical
from repguard_pot_readout_control import canonical as robust_readout

def read(p):return json.loads(p.read_text())

def main():
    old=read(ROOT/'results/thesis_real_pilot_v2/packet_private.json')
    for name,h in old['visible']['source_sha256'].items():
        assert hashlib.sha256((ROOT/'thesis_pilot'/name).read_bytes()).hexdigest()==h
    dest=ROOT/'results/thesis_causal_repair_v1';plan=read(dest/'plan.json');private=read(dest/'private.json')
    assert digest(private)==plan['private_sha256']
    assert plan['run_id']==digest({k:v for k,v in plan.items() if k!='run_id'})[:24]
    fresh=plan['fresh_cases'];assert len(fresh)==24 and len({c['report'] for c in fresh})==24
    assert not {c['report'] for c in fresh}&{c['report'] for c in old['visible']['cases']}
    native=ROOT/'results/thesis_competence_probe_v1';np=read(native/'plan.json')
    for folder,p in [(dest,plan),(native,np)]:
        with zipfile.ZipFile(folder/'frozen_source.zip') as z:
            for f,h in p['source_sha256'].items():assert hashlib.sha256(z.read(f)).hexdigest()==h
    manifest={};verified=[];original={};fresh_scores={}
    for phase,cc in [('diagnostic',plan['history_diagnostic']),('fresh',fresh)]:
        cases={c['id']:c for c in cc}
        for f in sorted((dest/phase).glob('*.json')):
            r=read(f);assert r['state']=='completed';c=cases[r['case_id']];o=r['output'];action=r['action'];initial=None
            if phase=='fresh' and action!='initial':
                initial=read(dest/phase/f'{digest(c["id"])[:16]}_initial.json')['output']['verification']['answer']
                initial=initial or {'reasoning':'Initial output malformed','status':'insufficient_evidence','steps':[],'display_unit':'number'}
            oracle=private['oracle_sources'][c['id']] if action=='oracle_evidence' else None
            assert o['prompt_sha256']==digest(cm(c,action,initial,oracle))
            assert cv(c,o['response']['message']['content'],action,initial)==o['verification']
            verified.append((f,o));manifest[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
            if phase=='fresh':original.setdefault(c['id'],{})[action]=o['verification']
    assert len(verified)==112
    for i,vv in original.items():
        assert set(vv)==set(plan['fresh_actions'])
        for a,v in vv.items():
            final=v if v['hard_pass'] else vv['initial']
            fresh_scores[a]=fresh_scores.get(a,0)+int(final['hard_pass'] and correct(final['value'],private['gold'][i]))
    summary=read(dest/'summary.json')
    for a,n in fresh_scores.items():assert summary['fresh'][a]['correct']==n
    native_cases={c['id']:c for c in plan['history_diagnostic']};nr=[];ns={}
    assert np['case_ids']==[c['id'] for c in plan['history_diagnostic']]
    for f in sorted(native.glob('*.json')):
        r=read(f)
        if 'state' not in r:continue
        assert r['state']=='completed';c=native_cases[r['case_id']];o=r['output'];arm=r['contract']
        assert digest(nm(c,arm))==o['prompt_sha256']
        assert nv(c,o['response']['message']['content'],arm)==o['verification']
        if arm=='numeric_native':assert json.loads(nm(c,arm)[1]['content'])==json.loads(cm(c)[1]['content'])
        if arm=='numeric_raw_native':assert nm(c,arm)[0]==nm(c,'numeric_native')[0]
        nr.append((f,o));manifest[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
        v=o['verification'];ns[arm]=ns.get(arm,0)+int(v['hard_pass'] and correct(v['value'],private['gold'][c['id']]))
    assert len(nr)==24
    native_summary=read(native/'summary.json')
    for a,n in ns.items():assert native_summary['results'][a]['correct']==n
    verified+=nr
    pot=ROOT/'results/thesis_pot_control_v1';pp=read(pot/'plan.json');ps=read(pot/'summary.json')
    assert pp['case_ids']==[c['id'] for c in fresh]
    with zipfile.ZipFile(pot/'frozen_source.zip') as z:
        for f,h in pp['source_sha256'].items():assert hashlib.sha256(z.read(f)).hexdigest()==h
    pc={c['id']:c for c in fresh};pr=[];pot_correct=0;pot_byid={}
    for f in sorted(pot.glob('*.json')):
        row=read(f)
        if 'state' not in row:continue
        assert row['state']=='completed';c=pc[row['case_id']];o=row['output']
        assert digest(pm(c))==o['prompt_sha256']
        assert pv(o['response']['message']['content'])==o['verification']
        assert json.loads(pm(c)[1]['content'])==json.loads(nm(c,'numeric_raw_native')[1]['content'])
        vv=o['verification'];pot_correct+=int(vv['hard_pass'] and correct(vv['value'],private['gold'][c['id']]))
        pot_byid[c['id']]=o
        pr.append((f,o));manifest[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
    assert len(pr)==24 and ps['correct']==pot_correct
    verified+=pr
    # Verify fitted OOF profiles, legal decisions and replay quality/cost from
    # actual responses, rather than trusting the learner's summary counters.
    policy_dir=ROOT/'results/thesis_paired_history_probe_v1'
    hp=read(policy_dir/'plan.json');hs=read(policy_dir/'summary.json');ht=read(policy_dir/'traces_private.json')
    analysis_file=ROOT/'docs/analysis/repguard_paired_history_probe.py'
    assert hashlib.sha256(analysis_file.read_bytes()).hexdigest()==hp['source_sha256']
    assert hp==read(ROOT/'docs/analysis/repguard_paired_history_analysis_plan_2026-10-18.json')
    for f,h in hp['helper_sha256'].items():assert hashlib.sha256((ROOT/'docs/analysis'/f).read_bytes()).hexdigest()==h
    learned_ids=sorted(pc,key=lambda i:digest('causal-repair-fold:'+pc[i]['report']));folds={i:j%3 for j,i in enumerate(learned_ids)}
    td={t['id']:t for t in ht['traces']};assert set(td)==set(pc)
    public_state={};labels={};times={};normalized_pot={}
    def eval_seconds(o):return (o['response']['prompt_eval_duration']+o['response']['eval_duration'])/1e9
    for i,c in pc.items():
        b=original[i]['initial'];a,changed=surgery(b['answer']);b=cv(c,json.dumps(a)) if changed else b
        y=int(b['hard_pass'] and correct(b['value'],private['gold'][i]));v=pot_byid[i]['verification']
        py=int(v['hard_pass'] and correct(v['value'],private['gold'][i]));ry=py if v['hard_pass'] else y
        guard=not b['hard_pass'] or bool(inspect_program(b['answer'])['errors'])
        ss=b.get('sources',[]);ta=any(s['source'].startswith('T') for s in ss);te=any(not s['source'].startswith('T') for s in ss)
        key=[skill(c['question']),'mixed' if ta and te else 'table' if ta else 'text','multi' if len((b['answer'] or {}).get('steps',[]))>1 else 'one']
        public_state[i]={'guard':guard,'key':key};labels[i]={'cheap':y,'direct_pot':py,'regen':ry}
        initial_output=read(dest/'fresh'/f'{digest(i)[:16]}_initial.json')['output']
        times[i]=(eval_seconds(initial_output),eval_seconds(pot_byid[i]))
        assert ht['data'][i]['cheap']==y and ht['data'][i]['direct_pot']==py and ht['data'][i]['regen']==ry
        assert ht['data'][i]['guard']==guard and ht['data'][i]['key']==key
        fmt,_=canonical(pot_byid[i]['response']['message']['content']);normalized_pot[i]=(fmt,int(fmt['hard_pass'] and correct(fmt['value'],private['gold'][i])))
    for i in learned_ids:
        t=td[i];st=public_state[i]
        train=[j for j in learned_ids if folds[j]!=folds[i] and not public_state[j]['guard']]
        local=[j for j in train if public_state[j]['key']==st['key']]
        assert t['train_ids']==train and t['local_ids']==local and i not in train
        assert t['fold']==folds[i] and t['forced_guard']==st['guard']
        g=sum(labels[j]['regen']-labels[j]['cheap'] for j in train)/(len(train)+4)
        l=(sum(labels[j]['regen']-labels[j]['cheap'] for j in local)+6*g)/(len(local)+6)
        assert math.isclose(t['global_gain'],g,abs_tol=1e-12) and math.isclose(t['local_gain'],l,abs_tol=1e-12)
        assert t['global_regenerate']==bool(st['guard'] or g>.05) and t['local_regenerate']==bool(st['guard'] or l>.05)
    fmt_summary=read(ROOT/'results/thesis_pot_format_control_v2/summary.json')
    assert fmt_summary['normalized_correct']==sum(y for vv,y in normalized_pot.values())
    for name,metrics in hs['methods'].items():
        score=0;normalized_score=0;seconds=0.;calls=0
        for i in learned_ids:
            btime,rtime=times[i];y=labels[i]
            if name=='direct_pot':score+=y['direct_pot'];normalized_score+=normalized_pot[i][1];seconds+=rtime;calls+=1;continue
            invoke=(name=='always_regenerate_with_fallback' or (name=='rule_guard_only' and public_state[i]['guard']) or
                (name=='oof_global_history' and td[i]['global_regenerate']) or (name=='oof_local_history' and td[i]['local_regenerate']))
            score+=y['regen'] if invoke else y['cheap'];seconds+=btime+(rtime if invoke else 0);calls+=1+int(invoke)
            fmt_v,ny=normalized_pot[i];normalized_score+=(ny if fmt_v['hard_pass'] else y['cheap']) if invoke else y['cheap']
        assert score==metrics['correct'] and math.isclose(seconds/24,metrics['mean_ollama_eval_seconds'],rel_tol=1e-12)
        assert math.isclose(calls/24,metrics['mean_model_calls'],rel_tol=1e-12)
        assert normalized_score==fmt_summary['same_frozen_decisions_with_uniform_formatter'][name]['correct']
    assert math.isclose(hs['zero_harm_upper95_at_n24'],1-.05**(1/24),abs_tol=1e-12)
    readout_dir=ROOT/'results/thesis_pot_readout_control_v3';readout_summary=read(readout_dir/'summary.json');robust={}
    for i in pc:
        rv,_=robust_readout(pot_byid[i]['response']['message']['content'])
        robust[i]=(rv,int(rv['hard_pass'] and correct(rv['value'],private['gold'][i])))
    assert sum(y for rv,y in robust.values())==readout_summary['robust_direct_pot_correct']
    for name in hs['methods']:
        score=0
        for i in learned_ids:
            if name=='direct_pot':score+=robust[i][1];continue
            invoke=(name=='always_regenerate_with_fallback' or (name=='rule_guard_only' and public_state[i]['guard']) or
                (name=='oof_global_history' and td[i]['global_regenerate']) or (name=='oof_local_history' and td[i]['local_regenerate']))
            rv,ry=robust[i];score+=(ry if rv['hard_pass'] else labels[i]['cheap']) if invoke else labels[i]['cheap']
        assert score==readout_summary['same_frozen_decisions'][name]['correct']
    assert all((ry if rv['hard_pass'] else labels[i]['cheap'])==labels[i]['regen'] for i,(rv,ry) in robust.items() if not public_state[i]['guard'])
    for folder in [policy_dir,ROOT/'results/thesis_pot_format_control_v2',readout_dir]:
        for f in folder.glob('*.json'):manifest[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
    for f,o in verified:
        assert o['app']=='repguard-thesis-real-pilot-20261018'
        assert o['model']=='qwen3:14b' and o['response']['model']=='qwen3:14b'
        assert o['model_digest']=='bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8'
        assert o['live_inference'] and not o['evaluation_volume_mounted'] and o['response']['done']
        assert 'L4' in o['gpu']
    for folder in [dest,native,pot]:
        for f in folder.glob('*.json'):manifest[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
        f=folder/'frozen_source.zip';manifest[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
    result={'scope':'This research round only; previous calls/aborted runs not included',
      'passed':True,'actual_responses_recomputed':len(verified),'causal_study':112,'competence_diagnostics':24,'pot_control':24,
      'mock_inference':0,'unresolved_initiated_calls':0,'frozen_primary_seven_unchanged':True,
      'fresh_report_count':24,'previous100_report_overlap':0,'prompt_hashes_and_local_execution_match':True,
      'OOF_profiles_current_case_exclusion_and_replay_recomputed':True,'format_control_recomputed':True,
      'final_variable_readout_control_recomputed':True,'robust_single_agent_correct':readout_summary['robust_direct_pot_correct'],
      'input_tokens':sum(o['response'].get('prompt_eval_count',0) for f,o in verified),
      'output_tokens':sum(o['response'].get('eval_count',0) for f,o in verified),
      'done_reason_counts':{reason:sum(o['response'].get('done_reason')==reason for f,o in verified) for reason in set(o['response'].get('done_reason') for f,o in verified)},
      'manifest_sha256':digest(manifest),'causal_scores':fresh_scores,'competence_scores':ns,'pot_correct':pot_correct}
    (ROOT/'results/thesis_research_cycle_01_manifest_private.json').write_text(json.dumps(manifest,indent=2))
    Path(__file__).with_name('repguard_research_cycle_01_verification_2026-10-18.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
