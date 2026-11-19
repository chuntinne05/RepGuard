"""CPU-only pinned archive intake, source and evaluation volumes kept separate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/workspace_v4"
BASE = ROOT / "results/general_verification_v1/source_intake/DataSpace"
APP_NAME = "repguard-workspace-v4-source-intake-20261109"
INPUT_VOLUME = "repguard-workspace-v4-inputs-20261109"
EVAL_VOLUME = "repguard-workspace-v4-evaluation-20261109"
app = modal.App(APP_NAME)
inputs = modal.Volume.from_name(INPUT_VOLUME, create_if_missing=True)
evaluation = modal.Volume.from_name(EVAL_VOLUME, create_if_missing=True)
image = modal.Image.debian_slim(python_version="3.11")


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


@app.function(image=image, volumes={"/inputs":inputs,"/evaluation":evaluation},
              cpu=2, memory=2048, timeout=1800, max_containers=1, retries=0)
def fetch_sources(meta, tasks):
    import tempfile
    import urllib.request
    import zipfile
    import shutil
    from datetime import datetime, timezone

    root=Path('/inputs'); private=Path('/evaluation')
    receipt=root/'source_receipt.json'
    if receipt.exists():
        existing=json.loads(receipt.read_text())
        if existing['dataset_revision']!=meta['revision'] or existing['task_ids']!=[t['task_id'] for t in tasks]:
            raise RuntimeError('Different source request already exists')
        return existing
    archive=next(x for x in meta['files'] if x['rfilename']=='release/DataSpace-Benchmark.zip')
    url=f'https://huggingface.co/datasets/HKUSTDial/DataSpace/resolve/{meta["revision"]}/{archive["rfilename"]}?download=true'
    with tempfile.TemporaryDirectory(prefix='repguard-dataspace-') as temp:
        path=Path(temp)/'source.zip'
        print('Downloading pinned archive, exact byte cap, no model calls.',flush=True)
        digest=hashlib.sha256(); total=0
        req=urllib.request.Request(url,headers={'Accept-Encoding':'identity','User-Agent':'RepGuard-research'})
        with urllib.request.urlopen(req,timeout=180) as source, path.open('wb') as target:
            while True:
                chunk=source.read(8*1024*1024)
                if not chunk: break
                total+=len(chunk)
                if total>archive['size']:raise RuntimeError('Archive exceeds pinned size')
                digest.update(chunk);target.write(chunk)
        if total!=archive['size'] or digest.hexdigest()!=archive['lfs']['sha256']:
            raise RuntimeError('Archive identity failed')
        print(json.dumps({'archive_sha256':'PASS','bytes':total}),flush=True)
        public_files=[]; private_files=[]
        with zipfile.ZipFile(path) as z:
            members={m.filename:m for m in z.infolist() if not m.is_dir()}
            for task in tasks:
                tid=task['task_id'];prefix='DataSpace-Benchmark/'
                expected={f'input/{tid}/task.json'}|{f'input/{tid}/context/{p}' for p in task['workspace_files']}
                actual={name[len(prefix):] for name in members if name.startswith(prefix+f'input/{tid}/')}
                if actual!=expected:raise RuntimeError('Manifest/archive input membership mismatch:'+tid)
                paths=[(rel,root/rel,public_files) for rel in sorted(expected)]
                paths += [(f'output/{tid}/gold.csv',private/f'output/{tid}/gold.csv',private_files),
                          (f'evaluation/configs/{tid}.json',private/f'configs/{tid}.json',private_files)]
                for relative,dest,ledger in paths:
                    if '..' in Path(relative).parts or not dest.resolve().is_relative_to((root if ledger is public_files else private).resolve()):
                        raise RuntimeError('Unsafe source path')
                    member=members[prefix+relative]
                    if member.file_size>500_000_000:raise RuntimeError('Member exceeds source cap')
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    with z.open(member) as source,dest.open('wb') as target:
                        shutil.copyfileobj(source,target,1024*1024)
                    if dest.stat().st_size!=member.file_size:raise RuntimeError('Member length mismatch')
                    h=hashlib.sha256()
                    with dest.open('rb') as f:
                        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
                    ledger.append({'path':str(dest.relative_to(root if ledger is public_files else private)),
                                   'bytes':member.file_size,'sha256':h.hexdigest()})
        result={'dataset':'HKUSTDial/DataSpace','dataset_revision':meta['revision'],
                'task_ids':[t['task_id'] for t in tasks],'archive_bytes':total,'archive_sha256':digest.hexdigest(),
                'full_archive_sha256_verified':True,'input_members_exactly_match_manifest':True,
                'public_input_files':public_files,'evaluation_files':private_files,
                'evaluation_volume_separate':True,'model_calls':0,'benchmark_scorer_executed':False,
                'oracle_semantics_validated':False,'created_utc':datetime.now(timezone.utc).isoformat()}
        write(receipt,result)
        inputs.commit();evaluation.commit()
        print(json.dumps({'source_intake':'complete','public_files':len(public_files),'private_files':len(private_files)}),flush=True)
        return result


def launch():
    from datetime import datetime,timezone
    meta=json.loads((BASE/'hf_metadata.json').read_text())
    packet=json.loads((BASE/'source_inspection_public_tasks.json').read_text())
    receipt=OUT/'intake_launch_receipt.json'
    if receipt.exists():raise RuntimeError('Already launched; inspect existing job')
    with app.run(detach=True):
        call=fetch_sources.spawn(meta,packet['tasks'])
        value={'created_utc':datetime.now(timezone.utc).isoformat(),'app_id':app.app_id,
               'function_call_id':call.object_id,'app_name':APP_NAME,'model_calls':0,
               'archive_byte_cap':2878651222,'task_ids':[t['task_id'] for t in packet['tasks']]}
        write(receipt,value);print(json.dumps(value,indent=2),flush=True)


if __name__=='__main__':launch()
