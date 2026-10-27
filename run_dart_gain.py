"""Prepare, submit, inspect, and fetch the fixed gain/structure experiment."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'infra/modal'))
from neural_pipeline import atomic,digest,verify_packet

APP='repguard-gain-structure-v1'
OUTPUT=ROOT/'results/dart_gain_v1'


def prepare():
    import numpy as np
    prior=ROOT/'results/dart_neural_v1/cloud'
    old=json.loads((prior/'input_private.json').read_text()); verify_packet(old)
    emb=json.loads((prior/'embeddings_private.json').read_text())
    x=np.array(emb['embeddings'])
    assert x.shape==(168,384) and np.isfinite(x).all()
    assert np.allclose(np.linalg.norm(x,axis=1),1)
    packet={k:v for k,v in old.items() if k not in ('run_id','source_sha256')}
    packet['embeddings']=emb['embeddings']
    packet['parent_run_id']=old['run_id']
    packet['embedding_sha256']=hashlib.sha256((prior/'embeddings_private.json').read_bytes()).hexdigest()
    paths=[ROOT/'infra/modal'/n for n in ('gain_core.py','gain_pipeline.py','gain_modal.py','neural_core.py','neural_pipeline.py')]
    paths += [Path(__file__),ROOT/'docs/analysis/dart_gain_v1_protocol_2026-10-05.md']
    packet['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    packet['run_id']=digest(packet)[:24]
    OUTPUT.mkdir(parents=True,exist_ok=True)
    target=OUTPUT/'packet_private.json'
    if target.exists() and json.loads(target.read_text())!=packet:
        raise ValueError('Refusing to overwrite a prepared different experiment')
    atomic(target,packet)
    print(json.dumps({'run_id':packet['run_id'],'tasks':168,'cases':305}))


def main():
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('action',choices=['prepare','submit','status','fetch'])
    p.add_argument('--resume',action='store_true')
    args=p.parse_args()
    if args.action=='prepare':
        prepare(); return
    import modal
    packet=json.loads((OUTPUT/'packet_private.json').read_text()); run_id=packet['run_id']
    reader=modal.Function.from_name(APP,'inspect_run')
    if args.action=='submit':
        receipt=OUTPUT/'receipt.json'
        if receipt.exists():
            old=json.loads(receipt.read_text())
            if old['run_id']!=run_id:
                raise ValueError('Receipt identity mismatch')
            try:
                value=modal.FunctionCall.from_id(old['call_id']).get(timeout=0)
                print(json.dumps(value)); return
            except TimeoutError:
                print(json.dumps({'already_submitted':old})); return
            except Exception:
                # Fail closed unless the cloud itself saved a failure state.
                if not args.resume:
                    raise
                if reader.remote(run_id)['state']!='pipeline_failed':
                    raise RuntimeError('No confirmed failed checkpoint; refusing duplicate submit')
        call=modal.Function.from_name(APP,'worker').spawn(packet)
        value={'app':APP,'run_id':run_id,'call_id':call.object_id}
        atomic(receipt,value); print(json.dumps(value))
    elif args.action=='status':
        print(json.dumps(reader.remote(run_id),indent=2))
    else:
        import io,zipfile
        data=reader.remote(run_id,archive=True)
        target=OUTPUT/'cloud'; target.mkdir(exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for name in z.namelist():
                if Path(name).name!=name or not name.endswith('.json'):
                    raise ValueError('Invalid archive member')
            z.extractall(target)
            count=len(z.namelist())
        print(json.dumps({'artifacts':count,'directory':str(target)}))


if __name__=='__main__':
    main()
