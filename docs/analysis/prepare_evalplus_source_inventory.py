"""Pin official EvalPlus sources and a metadata-selected coding pilot, zero inference."""
import gzip
import hashlib
import io
import json
import time
import urllib.request
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'results/thesis_evalplus_source_v1'
REV='26d6d00bb1fd0fa37f39c99d5290da67891d1c5e'
URLS={'evalplus_source.zip':f'https://codeload.github.com/evalplus/evalplus/zip/{REV}',
      'MbppPlus-v0.2.0.jsonl.gz':'https://github.com/evalplus/mbppplus_release/releases/download/v0.2.0/MbppPlus.jsonl.gz'}
def digest(b):return hashlib.sha256(b).hexdigest()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);data=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    if path.exists():assert path.read_text()==data,'Refusing changed artifact'
    else:path.write_text(data)
def main():
    DEST.mkdir(parents=True,exist_ok=True);files={}
    for name,url in URLS.items():
        f=DEST/name
        if f.exists():b=f.read_bytes()
        else:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'repguard-research-source-intake'}),timeout=60) as r:b=r.read(100_000_001)
            if len(b)>100_000_000:raise ValueError('Source size cap')
            f.write_bytes(b)
        files[name]={'url':url,'bytes':len(b),'sha256':digest(b)}
    source_bytes=(DEST/'evalplus_source.zip').read_bytes();code={}
    with zipfile.ZipFile(io.BytesIO(source_bytes)) as z:
        prefix=f'evalplus-{REV}/'
        for name in z.namelist():
            if not name.startswith(prefix):raise ValueError('Unexpected archive prefix')
            rel=name[len(prefix):]
            if '..' in Path(rel).parts or rel.startswith('/'):raise ValueError('Unsafe source path')
            if (rel.startswith('evalplus/') and rel.endswith('.py')) or rel in ['LICENSE','README.md','pyproject.toml','requirements.txt']:
                b=z.read(name);f=DEST/'source'/rel;f.parent.mkdir(parents=True,exist_ok=True)
                if f.exists():assert f.read_bytes()==b
                else:f.write_bytes(b)
                code[rel]=digest(b)
    raw=gzip.decompress((DEST/'MbppPlus-v0.2.0.jsonl.gz').read_bytes());data=[json.loads(line) for line in raw.splitlines() if line.strip()]
    assert len({r['task_id'] for r in data})==len(data)
    required={'task_id','prompt','entry_point','canonical_solution','base_input','plus_input','atol'}
    assert all(required<=set(r) for r in data)
    ordered=sorted(data,key=lambda r:digest(('repguard-partial-feedback-dev-v1:'+r['task_id']).encode()))
    selected=ordered[:32];public=[{k:r[k] for k in ['task_id','prompt','entry_point']} for r in selected]
    private={r['task_id']:{k:r[k] for k in r if k not in ['task_id','prompt','entry_point']} for r in selected}
    write(DEST/'public_development_inventory.json',public);write(DEST/'annotations_private.json',private)
    summary={'scope':'Preparation only:32 metadata-selected MBPP+ development tasks, ZERO model calls or task executions. Not a validated method or clean test set.',
             'repository':'https://github.com/evalplus/evalplus','revision':REV,'dataset_version':'v0.2.0','source_files':files,'code_sha256':code,
             'dataset_tasks':len(data),'selected_tasks':32,'selection':'SHA256 of fixed salt+task_id, before any model outcomes; no score filtering',
             'public_sha256':digest((DEST/'public_development_inventory.json').read_bytes()),'case_ids':[r['task_id'] for r in selected],
             'base_test_input_count':sum(len(r['base_input']) for r in selected),'plus_test_input_count':sum(len(r['plus_input']) for r in selected),
             'example_schema_keys':sorted(data[0]),'model_calls':0,'programs_executed':0,'benchmark_score':None,
             'limitations':['MBPP+/EvalPlus established benchmark; pretraining contamination unknown','Overlap with archived MBPP200 development NOT yet mapped; do not claim independence',
             'Archive20model headroom does not transfer automatically to current Ollama models','Official sources/tests are not a proof every task is unambiguous or every oracle correct',
             'Must validate reference solutions and isolate code execution in a fresh cloud sandbox before any study','No source/test/canonical-solution annotations may enter GPU prompts except explicitly permitted public examples',
             'Need lock feedback visibility, audit budget, method/comparators, seeds/calls/splits before inference','No claim that test generation, partial testing or conditional reputation is novel']}
    write(DEST/'inventory.json',summary)
    print(json.dumps({k:summary[k] for k in ['revision','dataset_tasks','selected_tasks','base_test_input_count','plus_test_input_count','model_calls','programs_executed','example_schema_keys']},indent=2))
if __name__=='__main__':main()
