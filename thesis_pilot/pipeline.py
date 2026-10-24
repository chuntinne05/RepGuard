"""Real Ollama collection with durable per-request receipts and no gold access."""
import json
import time
from pathlib import Path
from .core import AGENTS, SCHEMA, digest, prompt, verify


def atomic(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    temporary.replace(path)


def save(path, value):
    value={k:v for k,v in value.items() if k!='artifact_sha256'}
    value['artifact_sha256']=digest(value);atomic(path,value);return value


def validate(value):
    if digest({k:v for k,v in value.items() if k!='artifact_sha256'})!=value['artifact_sha256']:
        raise ValueError('Artifact checksum mismatch')


def verify_visible(public):
    if public['agents']!=AGENTS or public['total_requests']!=200:
        raise ValueError('Changed agent configuration or inference budget')
    if len(public['cases'])!=100 or len({c['id'] for c in public['cases']})!=100:
        raise ValueError('Changed pilot size/IDs')
    if len({c['report'] for c in public['cases']})!=100:
        raise ValueError('Report grouping changed')
    if public['run_id']!=digest({k:v for k,v in public.items() if k!='run_id'})[:24]:
        raise ValueError('Input identity mismatch')
    import hashlib
    for name,expected in public['source_sha256'].items():
        if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Frozen source changed: '+name)
    for case in public['cases']:
        for agent in AGENTS:prompt(case,agent)  # Runtime allowlist; never gold.


def jobs(public):
    cases=public['cases']
    return ([(a,c) for a in AGENTS for c in cases[:4]]+
            [(a,c) for a in AGENTS for c in cases[4:]])


def collect(public,root,commit,request,environment):
    verify_visible(public);root=Path(root);root.mkdir(parents=True,exist_ok=True)
    ip=root/'visible.json'
    if ip.exists() and json.loads(ip.read_text())!=public:raise ValueError('Changed public inputs')
    atomic(ip,public);atomic(root/'environment.json',environment)
    old_status=root/'status.json'
    if old_status.exists():
        previous=json.loads(old_status.read_text())
        if previous['state'] in ['stopped_technical_gate','stopped_wall_budget']:
            return previous
    first=root/'first_started.json'
    if not first.exists():atomic(first,{'epoch':time.time()})
    first_epoch=json.loads(first.read_text())['epoch']
    ledger={};completed=0;started=0
    for index,(agent,case) in enumerate(jobs(public)):
        if index==8:
            structural=executable=0
            for j in range(8):
                earlier=json.loads((root/f'case_{j:04d}.json').read_text())
                validate(earlier)
                _,sample=jobs(public)[j]
                v=verify(sample,earlier['response']['message']['content'])
                structural+=isinstance(v['answer'],dict) and set(v['answer'])==set(SCHEMA['required'])
                executable+=v['hard_pass']
            gate={'structured':int(structural),'executable_source_bound':int(executable),
                  'requests':8,'passed':structural>=6 and executable>=1,'uses_gold':False}
            atomic(root/'technical_gate.json',gate);commit()
            if not gate['passed']:
                atomic(root/'status.json',{'state':'stopped_technical_gate','completed':completed,'total':200})
                commit();return {'state':'stopped_technical_gate','completed':completed}
        path=root/f'case_{index:04d}.json'
        old=None
        if path.exists():
            old=json.loads(path.read_text());validate(old)
            if old['run_id']!=public['run_id'] or old['index']!=index:
                raise ValueError('Mixed response checkpoint')
            if old['state']=='complete':
                ledger[str(index)]=old['artifact_sha256'];completed+=1
                continue
        if time.time()-first_epoch>public['max_collection_wall_seconds']:
            atomic(root/'status.json',{'state':'stopped_wall_budget','completed':completed,'total':200})
            commit();return {'state':'stopped_wall_budget','completed':completed}
        attempts=old.get('attempts',[]) if old else []
        if len(attempts)>=2:raise RuntimeError('Persistent request attempt cap reached')
        messages=prompt(case,agent);prompt_sha=digest(messages)
        attempt={'started_epoch':time.time(),'state':'initiated'};attempts.append(attempt)
        row={'run_id':public['run_id'],'index':index,'case_id':case['id'],'agent':agent['id'],
             'model':agent['model'],'prompt_sha256':prompt_sha,'state':'request_initiated','attempts':attempts}
        save(path,row);commit();started+=1
        body={'model':agent['model'],'messages':messages,'format':SCHEMA,'stream':False,
              'think':False,'keep_alive':'20m','options':{'temperature':0,'seed':18102026,
              'num_ctx':16384,'num_predict':agent['num_predict']}}
        begin=time.monotonic()
        try:
            response=request(body)
            if not response.get('done') or response.get('model')!=agent['model']:
                raise RuntimeError('Incomplete or unexpected real Ollama response')
            attempt.update(state='response_received',finished_epoch=time.time())
            row.update(state='complete',response=response,wall_seconds=time.monotonic()-begin)
            saved=save(path,row);ledger[str(index)]=saved['artifact_sha256'];completed+=1
            save(root/'ledger.json',ledger)
            atomic(root/'status.json',{'run_id':public['run_id'],'state':'collecting',
                   'completed':completed,'total':200,'last_case':case['id'],
                   'last_agent':agent['id'],'last_updated_epoch':time.time()})
            commit()
        except Exception as error:
            attempt.update(state='unknown_or_transport_failure',error=repr(error),finished_epoch=time.time())
            row.update(state='infrastructure_failed',wall_seconds=time.monotonic()-begin)
            save(path,row);atomic(root/'status.json',{'state':'infrastructure_failed','completed':completed,
                                                     'total':200,'error':repr(error)})
            commit();raise
    atomic(root/'status.json',{'run_id':public['run_id'],'state':'collection_complete',
           'completed':completed,'total':200,'elapsed_wall_seconds':time.time()-first_epoch})
    commit();return {'state':'collection_complete','completed':completed}


def load_responses(public,root):
    root=Path(root);ledger=json.loads((root/'ledger.json').read_text());validate(ledger)
    result={}
    for index,(agent,case) in enumerate(jobs(public)):
        row=json.loads((root/f'case_{index:04d}.json').read_text());validate(row)
        if row['state']!='complete' or row['artifact_sha256']!=ledger[str(index)] or row['prompt_sha256']!=digest(prompt(case,agent)):
            raise ValueError('Incomplete, mismatched or corrupt real response')
        key=(case['id'],agent['id'])
        if key in result:raise ValueError('Duplicate solver outcome')
        result[key]=row
    if len(result)!=200:raise ValueError('Wrong outcome count')
    return result
